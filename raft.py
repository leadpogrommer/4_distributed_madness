import asyncio
import random
import traceback
from dataclasses import dataclass
from typing import Any
from enum import Enum, auto

from timer import Timer
from transport import Node, Transport


@dataclass()
class AppendEntriesRequest:
    term: int
    leaderId: Node
    prevLogIndex: int
    prevLogTerm: int
    entries: list['LogEntry']
    leaderCommit: int


@dataclass()
class AppendEntriesResponse:
    term: int
    success: bool
    last_index: int


@dataclass()
class VoteRequest:
    term: int
    candidateId: Node
    lastLogIndex: int
    lastLogTerm: int


@dataclass()
class VoteResponse:
    term: int
    voteGranted: bool

@dataclass()
class SendValueToLeader:
    value: Any


@dataclass()
class LogEntry:
    term: int
    # index: int
    data: Any


class Role(Enum):
    CANDIDATE = auto()
    FOLLOWER = auto()
    LEADER = auto()


class RaftServer:
    # common state
    currentTerm: int = 0
    votedFor: Node | None = None
    log: list[LogEntry]
    # volatile common state (we don't save non-volatile state, so we don't care
    commitIndex: int = 0
    lastApplied: int = 0

    # leader state
    nextIndex: dict[Node, int] = None
    matchIndex: dict[Node, int] = None

    # candidate state
    votes: int = 0

    # other stuff
    role: Role = Role.FOLLOWER
    leaderId: Node | None = None
    election_timer: Timer | None = None
    is_running = True
    done_running = asyncio.Event()

    @property
    def prev_log_term(self):
        return self.log[-1].term

    def __init__(self, transport: Transport):
        self.log = [LogEntry(self.currentTerm, 'NOTHING')]
        self.transport: Transport = transport
        self.message_handlers = {
            AppendEntriesRequest: self.on_append_entries_request,
            AppendEntriesResponse: self.on_append_entries_response,
            VoteRequest: self.on_vote_request,
            VoteResponse: self.on_vote_response,
            SendValueToLeader: self.on_request_from_client,
        }
        self.transport.on_message_received_callback = self.on_message

    async def start(self):
        await self.transport.start()
        self._become_follower()

    # ROLE TRANSITIONS
    def _become_candidate(self):
        self.role = Role.CANDIDATE
        print(f'Starting (totally not rigged) election... term = {self.currentTerm+1} ')
        # increment current term
        self.currentTerm += 1
        # vote for self
        self.votes = 1
        self.votedFor = self.transport.self_node

        for node in self.transport.nodes:
            req = VoteRequest(
                self.currentTerm,
                self.transport.self_node,
                len(self.log) - 1,
                self.log[-1].term,
            )
            asyncio.create_task(self.transport.send_message(node, req))

        self.start_election_timer()

    def _become_leader(self):
        print(f'Ama host now!!! {self.currentTerm=}')
        self.role = Role.LEADER
        self.stop_election_timer()
        for node in self.transport.nodes:
            asyncio.create_task(self.pinger(node))
        self.nextIndex = {node: len(self.log) for node in self.transport.nodes}
        self.matchIndex = {node: -1 for node in self.transport.nodes}

    def _become_follower(self):
        self.role = Role.FOLLOWER
        print(f'Ama bomzh now {self.currentTerm=}')
        self.votedFor = None
        self.start_election_timer()

    # MESSAGE HANDLING
    async def on_message(self, node: Node, message):
        # print(f'Got message from {node}: {message}')
        try:
            await self.message_handlers[type(message)](node, message)
        except Exception as e:
            print('Got exception while processing message: ')
            traceback.print_exception(e)

    async def on_append_entries_request(self, node: Node, req: AppendEntriesRequest):
        def reply(state: bool):
            # if state == False:
            #     print("Refusing to append")
            #     traceback.print_stack()
            #     exit()
            asyncio.create_task(self.transport.send_message(node, AppendEntriesResponse(self.currentTerm, state, len(self.log) - 1)))

        # 1. Reply false if term < currentTerm
        if req.term < self.currentTerm:
            reply(False)
            return

        self.update_term(req.term)
        if self.role != Role.FOLLOWER:
            reply(False)
            return
        self.leaderId = req.leaderId
        self.start_election_timer()

        # 2. Reply false if log doesn’t contain an entry at prevLogIndex whose term matches prevLogTerm
        if (len(self.log) <= req.prevLogIndex) or (self.log[req.prevLogIndex].term != req.prevLogTerm):
            reply(False)
            return

        # 3. If an existing entry conflicts with a new one (same index
        # but different terms), delete the existing entry and all that
        # follow it
        for i in range(len(req.entries)):
            my_i = i + req.prevLogIndex + 1
            if my_i >= len(self.log):
                break
            if self.log[my_i].term != req.entries[i].term:
                if my_i <= self.commitIndex:
                    print('ERROR: deleting applied entry!')
                self.log = self.log[:my_i]
                print('Deleted non matching entry')
                break

        # 4. Append any new entries not already in the log
        # TODO: check here in case of trouble
        self.log += req.entries[len(self.log) - req.prevLogIndex - 1:]

        # 5. If leaderCommit > commitIndex, set commitIndex = min(leaderCommit, index of last new entry)
        if req.leaderCommit > self.commitIndex:
            self.commitIndex = min(req.leaderCommit, len(self.log) - 1)
        reply(True)

        # TODO: Apply to state machine

    async def on_append_entries_response(self, node: Node, resp: AppendEntriesResponse):
        self.update_term(resp.term)
        if self.role != Role.LEADER:
            return
        if resp.success:
            self.nextIndex[node] = len(self.log)
            self.matchIndex[node] = resp.last_index
        else:
            self.nextIndex[node] -= 1
            if self.nextIndex[node] < 0:
                print('FUCK')
                exit(1)

        max_n = None
        # print('Trying to increase commitIndex')
        for n in range(self.commitIndex+1, len(self.log)):
            if self.log[n].term != self.currentTerm:
                continue
            ok_count = 0
            for node, match in self.matchIndex.items():
                if match >= n:
                    ok_count += 1
            if (ok_count + 1) > (len(self.transport.nodes) + 1)/2:
                max_n = n
        if max_n is not None:
            self.commitIndex = max_n
        self._send_new_dickpics_to_fucking_slaves()

    async def on_vote_request(self, node: Node, req: VoteRequest):
        res = VoteResponse(self.currentTerm, False)
        current_term = self.currentTerm
        self.update_term(req.term)

        # TODO: check correctness of this
        my_last_log_term = self.log[-1].term if len(self.log) != 0 else 0
        if (req.term >= current_term) and (self.votedFor is None or self.votedFor == node) and (req.lastLogTerm >= my_last_log_term):
            self.votedFor = node
            res.voteGranted = True
            print('!!! GRANTED VOTE !!!')

        asyncio.create_task(self.transport.send_message(node, res))

    async def on_vote_response(self, node: Node, resp: VoteResponse):
        self.update_term(resp.term)
        if self.role != Role.CANDIDATE:
            print('WARNING: received vote response while not being wa candidate')
            return
        if resp.voteGranted:
            self.votes += 1
            if self.votes > (len(self.transport.nodes)+1)/2:
                self._become_leader()

    async def on_request_from_client(self, node: Node, req: SendValueToLeader):
        self._append_log_entry(req.value)

    # MISCELLANEOUS STUFF
    def stop_election_timer(self):
        if self.election_timer is not None:
            self.election_timer.cancel()

    def start_election_timer(self):
        self.stop_election_timer()
        self.election_timer = Timer(1+random.random()*0.250, self._become_candidate)

    async def pinger(self, node: Node):
        while self.role == Role.LEADER:
            req = AppendEntriesRequest(
                self.currentTerm,
                self.transport.self_node,
                prevLogIndex=self.nextIndex[node]-1,
                prevLogTerm=self.log[self.nextIndex[node]-1].term,
                entries=[],
                leaderCommit=self.currentTerm,
            )
            await self.transport.send_message(node, req)
            await asyncio.sleep(0.3)

    # return True if node became follower
    def update_term(self, new_term: int) -> bool:
        if new_term > self.currentTerm:
            print(f'Updating term and converting to follower: {self.currentTerm} -> {new_term}', flush=True)
            self.currentTerm = new_term
            self._become_follower()
            return True
        return False

    def shutdown(self):
        self.transport.shutdown()
        self.stop_election_timer()
        self.is_running = False
        self.done_running.set()

    def _append_log_entry(self, value: Any):
        if self.role != Role.LEADER:
            print('ERROR: trying to append entry while not being a leader')
        entry = LogEntry(self.currentTerm, value)
        self.log.append(entry)
        self._send_new_dickpics_to_fucking_slaves()

    def append_log_entry(self, value: Any):
        if self.role == Role.LEADER:
            self._append_log_entry(value)
        elif self.leaderId is not None:
            asyncio.create_task(self.transport.send_message(self.leaderId, SendValueToLeader(value)))
        else:
            print('ERROR: cannot send entry to leader: leader id unknown')

    def _send_new_dickpics_to_fucking_slaves(self):
        if self.role != Role.LEADER or len(self.log) == 0:
            return
        for node in self.transport.nodes:
            # TODO: immediately send commitIndex update

            if len(self.log) - 1 >= self.nextIndex[node]:
                asyncio.create_task(self.transport.send_message(node, AppendEntriesRequest(
                    term=self.currentTerm,
                    leaderId=self.transport.self_node,
                    prevLogIndex=self.nextIndex[node] - 1,
                    prevLogTerm=self.log[self.nextIndex[node]-1].term,
                    entries=self.log[self.nextIndex[node]:],
                    leaderCommit=self.commitIndex,
                )))










import asyncio
import random
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
class LogEntry:
    term: int
    index: int
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

    def __init__(self, transport: Transport):
        self.transport: Transport = transport
        self.message_handlers = {
            AppendEntriesRequest: self.on_append_entries_request,
            AppendEntriesResponse: self.on_append_entries_response,
            VoteRequest: self.on_vote_request,
            VoteResponse: self.on_vote_response,
        }
        self.transport.on_message_received_callback = self.on_message


    async def start(self):
        await self.transport.start()
        await self._become_follower()

    async def _become_candidate(self):
        # TODO: timer should be reset on appendentries and when granting vote
        print(f'Starting (totally not rigged) election... term = {self.currentTerm+1} ')
        self.role = Role.CANDIDATE
        # increment current term
        self.currentTerm += 1
        # vote for self
        self.votes = 1
        self.votedFor = self.transport.self_node

        for node in self.transport.nodes:
            req = VoteRequest(
                self.currentTerm,
                self.transport.self_node,
                0,  # TODO
                0,  # TODO
            )
            asyncio.create_task(self.transport.send_message(node, req))

        await self.start_election_timer()

    async def _become_leader(self):
        # TODO: demote self to follower
        print(f'Ama host now!!! {self.currentTerm=}')
        self.role = Role.LEADER
        await self.stop_election_timer()
        for node in self.transport.nodes:
            asyncio.create_task(self.pinger(node))


    async def _become_follower(self):
        print(f'Ama bomzh now {self.currentTerm=}')
        self.votedFor =None
        self.role = Role.FOLLOWER
        await self.start_election_timer()



    async def stop_election_timer(self):
        if self.election_timer is not None:
            self.election_timer.cancel()

    async def start_election_timer(self):
        await self.stop_election_timer()
        self.election_timer = Timer(1+random.random()*0.250, self._become_candidate)

    async def on_message(self, node: Node, message):
        # print(f'Got message from {node}: {message}')
        await self.message_handlers[type(message)](node, message)

    async def on_append_entries_request(self, node: Node, req: AppendEntriesRequest):
        if self.currentTerm < req.term:
            print(f'Updating term {self.currentTerm} -> {req.term}', flush=True)
            self.currentTerm = max(req.term, self.currentTerm)
        if self.role == Role.FOLLOWER:
            # TODO: check if leader is shit?
            await self.stop_election_timer()
            await self.start_election_timer()
        elif self.role == Role.CANDIDATE:
            await self._become_follower()

    async def on_append_entries_response(self, node: Node, resp: AppendEntriesResponse):
        pass

    async def on_vote_request(self, node: Node, req: VoteRequest):
        res = VoteResponse(self.currentTerm, False)
        if self.currentTerm < req.term:
            self.currentTerm = req.term
            await self._become_follower()

        # TODO: check if log is up to date
        if (req.term >= self.currentTerm) and (self.votedFor is None):
            self.votedFor = node
            res.voteGranted = True
        asyncio.create_task(self.transport.send_message(node, res))

    async def on_vote_response(self, node: Node, resp: VoteResponse):
        if self.role != Role.CANDIDATE:
            print('WARNING: received vote response while not being wa candidate')
            return
        # TODO: wwhy am I ignoring resp.term
        if resp.voteGranted:
            self.votes += 1
            if self.votes > (len(self.transport.nodes)+1)/2:
                await self._become_leader()

    async def pinger(self, node: Node):
        while self.role == Role.LEADER:
            req = AppendEntriesRequest(
                self.currentTerm,
                self.transport.self_node,
                0,
                0,
                [],
                0
            )
            await self.transport.send_message(node, req)
            await asyncio.sleep(0.3)








import asyncio
from signal import SIGINT, SIGTERM
import sys
from ui.debug_ui import start_debug_ui

from raft import RaftServer
from transport import Node, Transport


async def on_connected(node: Node):
    print(f'Connected to {node}')


async def on_disconnected(node: Node):
    print(f'Disconnected from {node}')


async def on_message(node: Node, message):
    print(f'Got message from {node}: {message}')


async def main():
    ports = list(map(int, sys.argv[1:]))
    print(ports)
    my_node = Node('127.0.0.1', ports[0])
    nodes = [Node('127.0.0.1', port) for port in ports[1:]]
    transport = Transport(
        my_node, nodes, on_message, on_connected, on_disconnected
    )
    raft = RaftServer(transport)
    start_debug_ui(raft)
    await raft.start()
    print('Transport started')
    for sig in [SIGINT, SIGTERM]:
        asyncio.get_running_loop().add_signal_handler(sig, raft.shutdown)
    await raft.done_running.wait()

if __name__ == '__main__':
    asyncio.run(main())
    # qasync.run(main())

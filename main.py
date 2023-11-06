from dataclasses import dataclass, field as dataclass_field
import asyncio
from asyncio import StreamReader, StreamWriter
import pickle
from aioconsole import ainput
import sys

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
    await raft.start()
    print('Transport started')
    while True:
        index, message = (await ainput()).split()
        await transport.send_message(nodes[int(index)], message)
        print('Message sent!')

if __name__ == '__main__':
    asyncio.run(main())
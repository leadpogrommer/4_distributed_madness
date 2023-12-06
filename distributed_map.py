from dataclasses import dataclass
from time import time
from typing import Any
from transport import Node


@dataclass
class MapSet:
    key: Any
    value: Any


@dataclass
class MapRemove:
    key: Any


@dataclass
class MapCAS:
    key: Any
    old: Any
    new: Any


@dataclass
class MapLockAcquire:
    node: Node
    current_time: int

@dataclass
class MapLockProlongate:
    node: Node
    current_time: int

@dataclass
class MapLockRelease:
    node: Node


@dataclass
class Lock:
    node: Node
    time: int

class DistributedDict(dict):
    _lock = None
    auto_unlock_time = 2

    def apply_log_entry(self, entry):
        match entry:
            case MapSet():
                print(f'Applying set operation: {entry}')
                self[entry.key] = entry.value
            case MapRemove():
                print(f'Applying del operation: {entry}')
                del self[entry.key]
            case MapCAS():
                if entry.old == self[entry.key]:
                    print('CAS successful')
                    self[entry.key] = entry.new
                else:
                    print('CAS Unsuccessful')
            case MapLockAcquire():
                if self._lock is not None:
                    if entry.current_time - self._lock.time > self.auto_unlock_time:
                        self._lock = None
                if self._lock is None or self._lock.node == entry.node:
                    self._lock = Lock(entry.node, entry.current_time)
            case MapLockProlongate():
                if self._lock is not  None:
                    if entry.current_time - self._lock.time > self.auto_unlock_time:
                        self._lock = None
                    elif self._lock.node == entry.node:
                        self._lock.time = entry.current_time
            case MapLockRelease():
                if self._lock is not None and self._lock.node == entry.node:
                    self._lock = None
                        
            case _:
                print(f'Trying to apply unknown action: {entry}')
        print(f'Map state: {self}')
    
    def get_owner(self) -> Node:
        if self._lock is not None and (time() - self._lock.time <= self.auto_unlock_time):
            return self._lock.node
        return None

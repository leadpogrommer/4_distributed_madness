from dataclasses import dataclass
from typing import Any


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


class DistributedDict(dict):
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
            case _:
                print(f'Trying to apply unknown action: {entry}')
        print(f'Map state: {self}')

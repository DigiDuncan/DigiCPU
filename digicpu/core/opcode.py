from collections.abc import Callable
from typing import Optional


class Opcode:
    def __init__(self, value: int, assembly: str, func: Optional[Callable] = None):
        self.value = value
        self.assembly = assembly
        self.function = func

    @property
    def width(self) -> int:
        # Instruction size is encoded with the first 2 bits of the opcode.
        return ((self.value & 0b11000000) >> 6) + 1

    def run(self, args: list[int]) -> None:
        if not self.function:
            return
        args = args[:self.width - 1]
        self.function(*args)

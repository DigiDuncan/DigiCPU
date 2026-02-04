from typing import Sequence


class RAM:
    def __init__(self, size: int = 256):
        self.size = size
        self.state = [0] * size

    def load(self, pos: int) -> int:
        return self.state[pos % self.size]

    def save(self, pos: int, data: int):
        self.state[pos % self.size] = data

    def write(self, starting_byte: int, data: Sequence[int]):
        for n, px in enumerate(data):
            i = starting_byte + n
            self.state[i] = px

    def read(self, starting_byte: int, width: int) -> Sequence[int]:
        return self.state[starting_byte:starting_byte + width]

class RAM:
    def __init__(self, size: int = 256):
        self.size = size
        self.state = [0] * size

    def load(self, pos: int) -> int:
        return self.state[pos % self.size]

    def save(self, pos: int, data: int):
        self.state[pos % self.size] = data

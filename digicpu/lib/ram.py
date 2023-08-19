class RAM:
    def __init__(self, size: int = 256):
        self.size = size
        self.state = list(range(256))

    def load(self, pos: int) -> int:
        return self.state[pos]

    def save(self, pos: int, data: int):
        self.state[pos] = data

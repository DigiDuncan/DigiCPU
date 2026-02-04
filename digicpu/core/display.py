class SevenSegmentDisplay:
    def __init__(self):
        self.address: int = 0
        self.data: int = 0

        self.digits = [0] * 8

    def update(self):
        self.digits[self.address - 1] = self.data

    def reset(self):
        self.digits = [0] * 8

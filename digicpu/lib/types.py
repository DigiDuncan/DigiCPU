from enum import IntEnum
from typing import Literal

Register = Literal[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]
Position = int
ROM_SIZE = 256
RAM_SIZE = 256
STACK_SIZE = 16
MAX_INT = 256
MAX_REG = 14
MAX_INSTRUCTION_WIDTH = 4

class Registers(IntEnum):
    ADDR = 8
    DATA = 9
    RAMA = 10
    RAMD = 11
    STCK = 12
    OVFL = 13
    INPT = 14

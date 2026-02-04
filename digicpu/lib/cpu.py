from functools import wraps
import re
from typing import Callable, Optional, cast

# LOGGING STUFF
import logging

from digicpu.lib.errors import RegisterOverflowError, ROMOutOfBoundsError, IntegerOverflowError, \
    UnknownInstructionError, UnknownOpcodeError
from digicpu.lib.ram import RAM
from digicpu.lib.types import MAX_INT, MAX_REG, MAX_INSTRUCTION_WIDTH, Register, \
    ROM_SIZE, RAM_SIZE, STACK_SIZE

logger = logging.getLogger("digicpu")
logging.basicConfig(level=logging.INFO)
logger.setLevel(logging.DEBUG)

try:
    from digiformatter import logger as digilogger
    dfhandler = digilogger.DigiFormatterHandler()
    logger.handlers = []
    logger.propagate = False
    logger.addHandler(dfhandler)
except ImportError:
    pass

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


class Registers:
    IMR = 0
    IN = 8
    ADDR = 9
    DATA = 10
    STACK = 11
    OF = 12


def make_int(i: str | int) -> int:
    if isinstance(i, int):
        return i
    if i.startswith("0X"):
        return int(i[2:], 16)
    elif i.startswith("0B"):
        return int(i[2:], 2)
    elif i.startswith("\""):
        return ord(i[1]) % MAX_INT
    else:
        return int(i)


def check_arithmetic(reg_1, reg_2, reg_to):
    """Sanity checks for arthimatic functions."""
    if reg_1 > MAX_REG:
        raise RegisterOverflowError(reg_1)
    if reg_2 > MAX_REG:
        raise RegisterOverflowError(reg_2)
    if reg_to > MAX_REG:
        raise RegisterOverflowError(reg_to)


def check_logic(reg_1, reg_2, jump):
    """Sanity checks for logical functions."""
    if reg_1 > MAX_REG:
        raise RegisterOverflowError(reg_1)
    if reg_2 > MAX_REG:
        raise RegisterOverflowError(reg_2)
    if jump > ROM_SIZE:
        raise ROMOutOfBoundsError(jump)


# This is a decorator and shouldn't be invoked.
def heavy(f: Callable) -> Callable:
    @wraps(f)
    def wrapper(self, *args, **kwargs):
        self.busy_flag = True
        f(self, *args, **kwargs)
        self.busy_flag = False
    return wrapper

class CPU:
    """A high-level implemenation of a CPU's functionality."""
    def __init__(self):
        self.program_counter: int = 0
        self.registers: list[int] = [0] * (MAX_REG + 1)
        self.rom: list[int] = [0] * ROM_SIZE
        self.ram: RAM = RAM(RAM_SIZE)

        self.opcodes = [
            Opcode(0x00, "NOP"),
            Opcode(0x41, "IMM", self.immediate),
            Opcode(0x07, "HLT", self.halt),
            Opcode(0x91, "CPY", self.copy),
            Opcode(0x50, "CLR", self.clear),
            Opcode(0x10, "RST", self.reset_state),
            Opcode(0x08, "CLF", self.clear_flags),
            Opcode(0x09, "CNF", self.clear_negative_flag),
            Opcode(0x0A, "CZF", self.clear_zero_flag),
            Opcode(0x0B, "COF", self.clear_overflow_flag),
            Opcode(0x49, "JNF", self.jump_if_negative_flag),
            Opcode(0x4D, "JNN", self.jump_if_not_negative_flag),
            Opcode(0x4A, "JZF", self.jump_if_zero_flag),
            Opcode(0x4E, "JNZ", self.jump_if_not_zero_flag),
            Opcode(0x4B, "JOF", self.jump_if_overflow_flag),
            Opcode(0x4F, "JNO", self.jump_if_not_overflow_flag),
            Opcode(0xF1, "EQ",  self.conditional_eq),
            Opcode(0xF2, "LT",  self.conditional_lt),
            Opcode(0xF3, "LTE", self.conditional_lte),
            Opcode(0xF5, "NEQ", self.conditional_neq),
            Opcode(0xF6, "GTE", self.conditional_gte),
            Opcode(0xF7, "GT",  self.conditional_gt),
            Opcode(0xE0, "NND", self.logical_nand),
            Opcode(0xE1, "OR",  self.logical_or),
            Opcode(0xE2, "AND", self.logical_and),
            Opcode(0xE3, "NOR", self.logical_nor),
            Opcode(0xA4, "NOT", self.logical_not),
            Opcode(0xE5, "XOR", self.logical_xor),
            Opcode(0x64, "JMP", self.jump),
            Opcode(0x65, "JMR", self.jump_register),
            Opcode(0x68, "INC", self.increment),
            Opcode(0x69, "DEC", self.decrement),
            Opcode(0xE8, "ADD", self.add),
            Opcode(0xE9, "SUB", self.sub),
            Opcode(0xEA, "MUL", self.multiply),
            Opcode(0xEB, "MOD", self.modulo),
            Opcode(0xEC, "SHL", self.shift_left),
            Opcode(0xED, "SHR", self.shift_right),
            Opcode(0xEE, "MIN", self.minimum),
            Opcode(0xEF, "MAX", self.maximum),
            Opcode(0x98, "RLD", self.ram_load),
            Opcode(0x99, "RSV", self.ram_save),
            Opcode(0x9A, "RLR", self.ram_load_register),
            Opcode(0x9B, "RSR", self.ram_save_register),
            Opcode(0x5C, "PSH", self.push),
            Opcode(0x5D, "POP", self.pop),
            Opcode(0xBF, "SEG", self.int_to_sevenseg),
            Opcode(0xF8, "ADO", self.add_with_overflow),
            Opcode(0xFA, "MLO", self.multiply_with_overflow),
        ]

        self._just_jumped = False
        self._last_instruction_size = 0
        self._halt_flag = False

        self.busy_flag = False  # Basically unimplemented -- some functions set it though

        self.negative_flag = False
        self.zero_flag = False
        self.overflow_flag = False

        self._current_instruction = ""

    @property
    def valid_opcodes(self) -> list[str]:
        return [o.assembly for o in self.opcodes]

    @property
    def input_register(self) -> int:
        return self.registers[8]

    @input_register.setter
    def input_register(self, v):
        self.registers[8] = v

    @property
    def address_register(self) -> int:
        return self.registers[9]

    @address_register.setter
    def address_register(self, v):
        self.registers[9] = v

    @property
    def data_register(self) -> int:
        return self.registers[10]

    @data_register.setter
    def data_register(self, v):
        self.registers[10] = v

    @property
    def stack_register(self) -> int:
        return self.registers[11]

    @stack_register.setter
    def stack_register(self, v):
        self.registers[11] = v

    @property
    def overflow_register(self) -> int:
        return self.registers[12]

    @overflow_register.setter
    def overflow_register(self, v):
        self.registers[12] = v

    def copy(self, reg_from: Register, reg_to: Register):
        """CPY <from> <to>
        Copy the value from register `from` to register `to`."""
        logger.debug(f"CPY {reg_from} {reg_to}")
        if reg_from > MAX_REG:
            raise RegisterOverflowError(reg_from)
        if reg_to > MAX_REG:
            raise RegisterOverflowError(reg_to)
        self.registers[reg_to] = self.registers[reg_from]

    def clear(self, reg: Register):
        """CLR <reg>
        Clear the value in register `reg`."""
        logger.debug(f"CLR {reg}")
        if reg > MAX_REG:
            raise RegisterOverflowError(reg)
        self.registers[reg] = 0

    def reset_state(self):
        """RST
        Clear the value of all registers and flags."""
        logger.debug("RST")
        for v in range(len(self.registers)):
            self.registers[v] = 0
        self.busy_flag = False
        self.negative_flag = False
        self.overflow_flag = False
        self.zero_flag = False

    def clear_negative_flag(self):
        """CNF
        Clear the negative flag"""
        logger.debug("CNF")
        self.negative_flag = False

    def clear_zero_flag(self):
        """CZF
        Clear the zero flag"""
        logger.debug("CZF")
        self.zero_flag = False

    def clear_overflow_flag(self):
        """COF
        Clear the overflow flag"""
        logger.debug("COF")
        self.overflow_flag = False

    def clear_flags(self):
        """CLF
        Clear all flags"""
        logger.debug("CLF")
        self.negative_flag = False
        self.zero_flag = False
        self.overflow_flag = False

    def jump_if_negative_flag(self, jump):
        """JNF <jump>
        If the negative flag is set, jump to position `jump`."""
        logger.debug(f"JNF {jump}")
        if jump > RAM_SIZE:
            raise ROMOutOfBoundsError(jump)
        if self.negative_flag:
            self.jump(jump)

    def jump_if_not_negative_flag(self, jump):
        """JNN <jump>
        If the negative flag is set, jump to position `jump`."""
        logger.debug(f"JNN {jump}")
        if jump > RAM_SIZE:
            raise ROMOutOfBoundsError(jump)
        if not self.negative_flag:
            self.jump(jump)

    def jump_if_zero_flag(self, jump):
        """JZF <jump>
        If the zero flag is set, jump to position `jump`."""
        logger.debug(f"JZF {jump}")
        if jump > RAM_SIZE:
            raise ROMOutOfBoundsError(jump)
        if self.zero_flag:
            self.jump(jump)

    def jump_if_not_zero_flag(self, jump):
        """JNZ <jump>
        If the zero flag is set, jump to position `jump`."""
        logger.debug(f"JNZ {jump}")
        if jump > RAM_SIZE:
            raise ROMOutOfBoundsError(jump)
        if not self.zero_flag:
            self.jump(jump)

    def jump_if_overflow_flag(self, jump):
        """JOF <jump>
        If the overflow flag is set, jump to position `jump`."""
        logger.debug(f"JOF {jump}")
        if jump > RAM_SIZE:
            raise ROMOutOfBoundsError(jump)
        if self.overflow_flag:
            self.jump(jump)

    def jump_if_not_overflow_flag(self, jump):
        """JNO <jump>
        If the overflow flag is set, jump to position `jump`."""
        logger.debug(f"JNO {jump}")
        if jump > RAM_SIZE:
            raise ROMOutOfBoundsError(jump)
        if not self.overflow_flag:
            self.jump(jump)

    def immediate(self, value: int):
        """IMM <value>
        Uses `value` like it's just a normal number.
        Can also be in the form of 0xVAL, 0bVAL, or a single character \"V\""""
        logger.debug(f"IMM {value}")
        if value >= MAX_INT:
            raise IntegerOverflowError(value)
        self.registers[Registers.IMR] = value

    def jump(self, position: int):
        """JMP <position>
        Jump to position `position` in ROM."""
        logger.debug(f"JMP {position}")
        if position >= ROM_SIZE:
            raise ROMOutOfBoundsError(position)
        self.program_counter = position % ROM_SIZE
        self._just_jumped = True

    def jump_register(self, reg: int):
        """JMR <reg>
        Jump to position stored in `<reg>` in ROM."""
        logger.debug(f"JMR {reg}")
        if reg >= MAX_REG:
            raise RegisterOverflowError(reg)
        self.program_counter = self.registers[reg] % ROM_SIZE
        self._just_jumped = True

    def increment(self, reg):
        """INC <reg>
        Add one to the value in `reg`.
        Sets the overflow flag and zero flag.
        """
        logger.debug(f"INC {reg}")
        if reg > MAX_REG:
            raise RegisterOverflowError(reg)
        ans = (self.registers[reg] + 1)
        self.registers[reg] = ans % MAX_INT
        self.overflow_flag = ans > MAX_INT
        self.zero_flag = ans == 0

    def decrement(self, reg):
        """DEC <reg>
        Subtract one from the value in `reg`.
        Sets the negative flag and zero flag.
        """
        logger.debug(f"DEC {reg}")
        if reg > MAX_REG:
            raise RegisterOverflowError(reg)
        ans = (self.registers[reg] - 1)
        self.registers[reg] = ans % MAX_INT
        self.negative_flag = ans < 0
        self.zero_flag = ans == 0

    def add(self, reg_1, reg_2, reg_to):
        """ADD <A> <B> <to>
        Add the values from registers A and B and copy it to register `to`.
        Sets the overflow flag or zero flag.
        """
        logger.debug(f"ADD {reg_1} {reg_2} {reg_to}")
        check_arithmetic(reg_1, reg_2, reg_to)
        ans = (self.registers[reg_1] + self.registers[reg_2])
        self.registers[reg_to] = ans % MAX_INT
        self.overflow_flag = ans > MAX_INT
        self.zero_flag = ans == 0

    def add_with_overflow(self, reg_1, reg_2, reg_to):
        """ADO <A> <B> <to>
        Add the values from registers A and B and copy it to register `to`.
        Sets the value in the OF register to the 0 if the result is less than 256, and 1 otherwise.
        Sets the overflow flag and zero flag.
        """
        logger.debug(f"ADO {reg_1} {reg_2} {reg_to}")
        check_arithmetic(reg_1, reg_2, reg_to)
        ans = (self.registers[reg_1] + self.registers[reg_2])
        self.registers[reg_to] = ans % MAX_INT
        self.registers[Registers.OF] = ans // MAX_INT
        self.overflow_flag = ans > MAX_INT * MAX_INT
        self.zero_flag = ans == 0

    def sub(self, reg_1, reg_2, reg_to):
        """SUB <A> <B> <to>
        Subtract the values from registers A and B and copy it to register `to`.
        Sets the negative flag and zero flag.
        """
        logger.debug(f"SUB {reg_1} {reg_2} {reg_to}")
        check_arithmetic(reg_1, reg_2, reg_to)
        if self.registers[reg_2] > self.registers[reg_1]:
            self.negative_flag = True
        ans = (self.registers[reg_1] - self.registers[reg_2])
        self.registers[reg_to] = ans % MAX_INT
        self.zero_flag = ans == 0

    def multiply(self, reg_1, reg_2, reg_to):
        """MUL <A> <B> <to>
        Mulitply the values from registers A and B and copy it to register `to`.
        Sets the overflow flag and zero flag.
        """
        logger.debug(f"MUL {reg_1} {reg_2} {reg_to}")
        check_arithmetic(reg_1, reg_2, reg_to)
        ans = (self.registers[reg_1] * self.registers[reg_2])
        self.registers[reg_to] = ans % MAX_INT
        self.overflow_flag = ans > MAX_INT
        self.zero_flag = ans == 0

    def multiply_with_overflow(self, reg_1, reg_2, reg_to):
        """MLO <A> <B> <to>
        Mulitply the values from registers A and B and copy it to register `to`.
        Sets the value in the OF register to the 0 if the result is less than 256, and (result // 256) otherwise.
        Sets the overflow flag and zero flag.
        """
        logger.debug(f"MLO {reg_1} {reg_2} {reg_to}")
        check_arithmetic(reg_1, reg_2, reg_to)
        ans = (self.registers[reg_1] * self.registers[reg_2])
        self.registers[reg_to] = ans % MAX_INT
        self.registers[Registers.OF] = ans // MAX_INT
        self.overflow_flag = ans > MAX_INT * MAX_INT
        self.zero_flag = ans == 0

    def modulo(self, reg_1, reg_2, reg_to):
        """MOD <A> <B> <to>
        Modulo the values from registers A and B and copy it to register `to`.
        Sets the zero flag.
        """
        logger.debug(f"MOD {reg_1} {reg_2} {reg_to}")
        check_arithmetic(reg_1, reg_2, reg_to)
        ans = (self.registers[reg_1] % self.registers[reg_2])
        self.registers[reg_to] = ans
        self.zero_flag = ans == 0

    def shift_left(self, reg_1, reg_2, reg_to):
        """SHL <A> <B> <to>
        Shift the value in register A B amount and copy it to register `to`.
        Sets the zero flag.
        """
        logger.debug(f"SHL {reg_1} {reg_2} {reg_to}")
        check_arithmetic(reg_1, reg_2, reg_to)
        ans = (self.registers[reg_1] << self.registers[reg_2]) % MAX_INT
        self.registers[reg_to] = ans
        self.zero_flag = ans == 0

    def shift_right(self, reg_1, reg_2, reg_to):
        """SHR <A> <B> <to>
        Shift the value in register A B amount and copy it to register `to`.
        Sets the zero flag.
        """
        logger.debug(f"SHR {reg_1} {reg_2} {reg_to}")
        check_arithmetic(reg_1, reg_2, reg_to)
        ans = (self.registers[reg_1] >> self.registers[reg_2]) % MAX_INT
        self.registers[reg_to] = ans
        self.zero_flag = ans == 0

    def minimum(self, reg_1, reg_2, reg_to):
        """MIN <A> <B> <to>
        Choose the minimum value from registers A and B and copy it to register `to`.
        Sets the zero flag.
        """
        logger.debug(f"MIN {reg_1} {reg_2} {reg_to}")
        check_arithmetic(reg_1, reg_2, reg_to)
        ans = min(self.registers[reg_1], self.registers[reg_2])
        self.registers[reg_to] = ans
        self.zero_flag = ans == 0

    def maximum(self, reg_1, reg_2, reg_to):
        """MAX <A> <B> <to>
        Choose the minimum value from registers A and B and copy it to register `to`.
        Sets the zero flag.
        """
        logger.debug(f"MAX {reg_1} {reg_2} {reg_to}")
        check_arithmetic(reg_1, reg_2, reg_to)
        ans = max(self.registers[reg_1], self.registers[reg_2])
        self.registers[reg_to] = ans
        self.zero_flag = ans == 0

    def logical_and(self, reg_1, reg_2, reg_to):
        """AND <A> <B> <to>
        Logical AND the values from registers A and B and copy it to register `to`.
        Sets the zero flag.
        """
        logger.debug(f"AND {reg_1} {reg_2} {reg_to}")
        check_logic(reg_1, reg_2, reg_to)
        ans = (self.registers[reg_1] & self.registers[reg_2]) % MAX_INT
        self.registers[reg_to] = ans
        self.zero_flag = ans == 0

    def logical_or(self, reg_1, reg_2, reg_to):
        """OR <A> <B> <to>
        Logical OR the values from registers A and B and copy it to register `to`.
        Sets the zero flag.
        """
        logger.debug(f"OR {reg_1} {reg_2} {reg_to}")
        check_logic(reg_1, reg_2, reg_to)
        ans = (self.registers[reg_1] | self.registers[reg_2]) % MAX_INT
        self.registers[reg_to] = ans
        self.zero_flag = ans == 0

    def logical_nand(self, reg_1, reg_2, reg_to):
        """NAND <A> <B> <to>
        Logical NAND the values from registers A and B and copy it to register `to`.
        Sets the zero flag.
        """
        logger.debug(f"NND {reg_1} {reg_2} {reg_to}")
        check_logic(reg_1, reg_2, reg_to)
        ans = ~(self.registers[reg_1] & self.registers[reg_2]) % MAX_INT
        self.registers[reg_to] = ans
        self.zero_flag = ans == 0

    def logical_nor(self, reg_1, reg_2, reg_to):
        """NOR <A> <B> <to>
        Logical NOR the values from registers A and B and copy it to register `to`.
        Sets the zero flag.
        """
        logger.debug(f"NOR {reg_1} {reg_2} {reg_to}")
        check_logic(reg_1, reg_2, reg_to)
        ans = ~(self.registers[reg_1] | self.registers[reg_2]) % MAX_INT
        self.registers[reg_to] = ans
        self.zero_flag = ans == 0

    def logical_xor(self, reg_1, reg_2, reg_to):
        """XOR <A> <B> <to>
        Logical XOR the values from registers A and B and copy it to register `to`.
        Sets the zero flag.
        """
        logger.debug(f"XOR {reg_1} {reg_2} {reg_to}")
        check_logic(reg_1, reg_2, reg_to)
        ans = (self.registers[reg_1] ^ self.registers[reg_2]) % MAX_INT
        self.registers[reg_to] = ans
        self.zero_flag = ans == 0

    def logical_not(self, reg, reg_to):
        """NOT <A> <to>
        Logical NOT the value from register A and copy it to register `to`.
        Sets the zero flag.
        """
        logger.debug(f"NOT {reg} {reg_to}")
        check_logic(reg, 0, reg_to)  # HACK: don't want to make a seperate checking function, only 1-operand math func.
        ans = (~self.registers[reg]) % MAX_INT
        self.registers[reg_to] = ans
        self.zero_flag = ans == 0

    def conditional_eq(self, reg_1, reg_2, jump):
        """EQ <A> <B> <jump>
        If the value in register A equals the value in register B, jump to position `jump`."""
        logger.debug(f"EQ {reg_1} {reg_2} {jump}")
        check_logic(reg_1, reg_2, jump)
        if self.registers[reg_1] == self.registers[reg_2]:
            self.jump(jump)

    def conditional_neq(self, reg_1, reg_2, jump):
        """NEQ <A> <B> <jump>
        If the value in register A doesn't equal the value in register B, jump to position `jump`."""
        logger.debug(f"NEQ {reg_1} {reg_2} {jump}")
        check_logic(reg_1, reg_2, jump)
        if self.registers[reg_1] != self.registers[reg_2]:
            self.jump(jump)

    def conditional_gt(self, reg_1, reg_2, jump):
        """GT <A> <B> <jump>
        If the value in register A is greater than the value in register B, jump to position `jump`."""
        logger.debug(f"GT {reg_1} {reg_2} {jump}")
        check_logic(reg_1, reg_2, jump)
        if self.registers[reg_1] > self.registers[reg_2]:
            self.jump(jump)

    def conditional_gte(self, reg_1, reg_2, jump):
        """GTE <A> <B> <jump>
        If the value in register A is greater than or equal to the value in register B, jump to position `jump`."""
        logger.debug(f"GTE {reg_1} {reg_2} {jump}")
        check_logic(reg_1, reg_2, jump)
        if self.registers[reg_1] >= self.registers[reg_2]:
            self.jump(jump)

    def conditional_lt(self, reg_1, reg_2, jump):
        """LT <A> <B> <jump>
        If the value in register A is less than the value in register B, jump to position `jump`."""
        logger.debug(f"LT {reg_1} {reg_2} {jump}")
        check_logic(reg_1, reg_2, jump)
        if self.registers[reg_1] < self.registers[reg_2]:
            self.jump(jump)

    def conditional_lte(self, reg_1, reg_2, jump):
        """LTE <A> <B> <jump>
        If the value in register A is less than or equal to the value in register B, jump to position `jump`."""
        logger.debug(f"LTE {reg_1} {reg_2} {jump}")
        check_logic(reg_1, reg_2, jump)
        if self.registers[reg_1] <= self.registers[reg_2]:
            self.jump(jump)

    @heavy
    def int_to_sevenseg(self, reg_from, reg_to):
        """SEG <from> <to>
        Convert the value in register `from` to its seven segment representation and place it in register `to`.
        Send an 'X' to clear the screen."""
        logger.debug(f"SEG {reg_from} {reg_to}")
        check_arithmetic(reg_from, 0, reg_to)
        char = self.registers[reg_from]
        match char:
            case 0 | 48:
                self.registers[reg_to] = 0b0111111
            case 1 | 49:
                self.registers[reg_to] = 0b0000110
            case 2 | 50:
                self.registers[reg_to] = 0b1011011
            case 3 | 51:
                self.registers[reg_to] = 0b1001111
            case 4 | 52:
                self.registers[reg_to] = 0b1100110
            case 5 | 53:
                self.registers[reg_to] = 0b1101101
            case 6 | 53:
                self.registers[reg_to] = 0b1111101
            case 7 | 54:
                self.registers[reg_to] = 0b0000111
            case 8 | 55:
                self.registers[reg_to] = 0b1111111
            case 9 | 56:
                self.registers[reg_to] = 0b1101111
            case 10 | 65 | 97:
                self.registers[reg_to] = 0b1110111
            case 11 | 66 | 98:
                self.registers[reg_to] = 0b1111100
            case 12 | 67 | 99:
                self.registers[reg_to] = 0b0111001
            case 13 | 68 | 100:
                self.registers[reg_to] = 0b1011110
            case 14 | 69 | 101:
                self.registers[reg_to] = 0b1111001
            case 15 | 70 | 102:
                self.registers[reg_to] = 0b1110001
            case 45:
                self.registers[reg_to] = 0b1000000
            case 95:
                self.registers[reg_to] = 0b0001000
            case 88 | 120:
                self.registers[reg_to] = 0

    def ram_load(self, pos_from, reg_to):
        """RLD <pos_from> <reg_to>
        Load the value from position `pos_from` in RAM into register `reg_to`."""
        logger.debug(f"RLD {pos_from} {reg_to}")
        if reg_to > MAX_REG:
            raise RegisterOverflowError(reg_to)
        if pos_from > ROM_SIZE:
            raise ROMOutOfBoundsError(pos_from)
        self.registers[reg_to] = self.ram.load(pos_from)

    def ram_save(self, reg_from, pos_to):
        """RSV <reg_from> <pos_to>
        Save the value from register `reg_from` to RAM position `pos_to`."""
        logger.debug(f"RSV {reg_from} {pos_to}")
        if reg_from > MAX_REG:
            raise RegisterOverflowError(reg_from)
        if pos_to > ROM_SIZE:
            raise ROMOutOfBoundsError(pos_to)
        self.ram.save(pos_to, self.registers[reg_from])

    def ram_load_register(self, reg_from, reg_to):
        """RLR <reg_from> <reg_to>
        Load the value from RAM position stored in `reg_from` into register `reg_to`."""
        logger.debug(f"RLD {reg_from} {reg_to}")
        if reg_to > MAX_REG:
            raise RegisterOverflowError(reg_to)
        if reg_from > MAX_REG:
            raise RegisterOverflowError(reg_from)
        self.registers[reg_to] = self.ram.load(self.registers[reg_from])

    def ram_save_register(self, reg_from, reg_to):
        """RSR <reg_from> <reg_to>
        Save the value from register `reg_from` to RAM position stored in `reg_to`."""
        logger.debug(f"RSV {reg_from} {reg_to}")
        if reg_to > MAX_REG:
            raise RegisterOverflowError(reg_to)
        if reg_from > MAX_REG:
            raise RegisterOverflowError(reg_from)
        self.ram.save(self.registers[reg_to], self.registers[reg_from])

    @heavy
    def push(self, reg_from):
        """PSH <reg_from>
        Push the value from `reg_from` to the stack."""
        logger.debug(f"PSH {reg_from}")
        if reg_from > MAX_REG:
            raise RegisterOverflowError(reg_from)
        self.ram.save(self.registers[Registers.STACK], self.registers[reg_from])
        self.registers[Registers.STACK] += 1
        self.registers[Registers.STACK] %= STACK_SIZE

    @heavy
    def pop(self, reg_to):
        """POP <reg_to>
        Pop the value from from the stack into register `reg_to`."""
        logger.debug(f"PSH {reg_to}")
        if reg_to > MAX_REG:
            raise RegisterOverflowError(reg_to)
        self.registers[reg_to] = self.ram.load(self.registers[Registers.STACK])
        self.registers[Registers.STACK] -= 1
        self.registers[Registers.STACK] %= STACK_SIZE

    def halt(self):
        self._halt_flag = True

    def step(self):
        """Run one clock cycle. Just keep doing this until we're out of ROM."""
        # If we're halted, we're... halted.
        if self._halt_flag:
            return

        # Get the current instruction and process it.
        current_ins = self.rom[self.program_counter]
        # This is needed because we're genericizing here and we need to not get IndexErrors.
        extended_rom = self.rom + [0] * MAX_INSTRUCTION_WIDTH
        # Get the next few values in case they're operands.
        operands = extended_rom[self.program_counter + 1:self.program_counter + 1 + MAX_INSTRUCTION_WIDTH]
        found = False
        for o in self.opcodes:
            if o.value != current_ins:
                continue
            found = True
            o.run(operands)
            self._last_instruction_size = o.width
            self._current_instruction = f"{o.assembly} {' '.join(f"{o:02X}" for o in operands[:o.width -1])}"
        if not found:
            raise UnknownOpcodeError(current_ins, self.program_counter)

        # If we just jumped, we don't need to increment the program counter.
        if not self._just_jumped:
            self.program_counter += self._last_instruction_size
        self._just_jumped = False

    def load(self, rom: list[int]):
        """Load a program from a list of bytes."""
        self.rom = [0] * ROM_SIZE
        for n, i in enumerate(rom):
            self.rom[n] = i

    def load_string(self, s: str):
        """Load an assembly program from string."""
        s = re.sub(r"#(.*)\n", "", s)  # comments

        # Deal with constants. It's not really an opcode, so it's not coded like one.
        replacements = {}
        constants: list[str] = re.findall(r"CONST (.+ .+)\n", s)
        for constant in constants:
            split = constant.split(maxsplit = 1)
            replacements[split[0]] = split[1]

        # Replace everything we determined needs to be, e.g.: constants.
        for key, value in replacements.items():
            s = s.replace(key, value)

        # Make sure everything's uppercase, since we assume that a lot.
        s = s.upper()

        # Store labels for later.
        labels = {}
        lines = s.split("\n")
        n = 0
        for line in lines:
            line = line.strip()
            # If we find a label definition, save it.
            if m := re.match(r"LABEL (.*)", line):
                labels[m.group(1)] = n
            else:
                # Step over opcodes, since we know how wide they are.
                for o in self.opcodes:
                    if line.startswith(o.assembly):
                        n += o.width
                        break

        # Replace all labels with nothing, since we dealt with them.
        s = re.sub(r"LABEL (.*)\n", "", s)

        # No newlines.
        s = s.replace("\n", " ")

        # Split the instructions by spaces and clean then up.
        instructions = s.split()
        instructions = [i.strip().upper() for i in instructions]
        instructions = cast(list[str | int], instructions)

        # Step through these instructions.
        for n, i in enumerate(instructions):
            match i:
                # Is a valid Opcode.
                case x if x in self.valid_opcodes:
                    opcode = next(o for o in self.opcodes if o.assembly == x)
                    instructions[n] = opcode.value
                    continue
                # Register aliases
                case "IMR":
                    instructions[n] = Registers.IMR
                    continue
                case "IN":
                    instructions[n] = Registers.IN
                    continue
                case "ADDR":
                    instructions[n] = Registers.ADDR
                    continue
                case "DATA":
                    instructions[n] = Registers.DATA
                    continue
                case "STACK":
                    instructions[n] = Registers.STACK
                    continue
                case "OF":
                    instructions[n] = Registers.OF
                    continue
                # Otherwise, is this a label?
                case x:
                    if x in labels:
                        instructions[n] = make_int(labels[x])
                        continue

            # Otherwise it's just a number I guess.
            instructions[n] = make_int(i)

        # If we didn't turn something into a number, something messed up.
        for i in instructions:
            if not isinstance(i, int):
                raise UnknownInstructionError(i)

        instructions = cast(list[int], instructions)
        self.load(instructions)

    def reset(self):
        """Clear the resgisters and start at the beginning of the program."""
        self.program_counter = 0
        self._halt_flag = False
        for v in range(len(self.registers)):
            self.registers[v] = 0
        self.busy_flag = False
        self.negative_flag = False
        self.overflow_flag = False
        self.zero_flag = False

    def input(self, value: int):
        """Set the input register to `value.`"""
        self.input_register = value % MAX_INT

    def __str__(self) -> str:
        return f"PROGRAM COUNTER: 0x{self.program_counter:X}\nREGISTERS: {[hex(v).upper() for v in self.registers[:8]]}\nINPUT: 0x{self.input_register:X} ({self.input_register})"

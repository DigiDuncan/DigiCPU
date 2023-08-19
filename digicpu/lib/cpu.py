import re
from typing import Literal, Optional

# LOGGING STUFF
import logging

from digicpu.lib.ram import RAM

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

Register = Literal[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
ROM_SIZE = 256
RAM_SIZE = 256
MAX_INT = 256
MAX_REG = 10


class Opcode:
    def __init__(self, value: int, assembly: str, func: Optional[callable] = None):
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
        raise ValueError(f"Register {reg_1} greater than {MAX_REG}!")
    if reg_2 > MAX_REG:
        raise ValueError(f"Register {reg_2} greater than {MAX_REG}!")
    if reg_to > MAX_REG:
        raise ValueError(f"Register {reg_to} greater than {MAX_REG}!")


def check_logic(reg_1, reg_2, jump):
    """Sanity checks for logical functions."""
    if reg_1 > MAX_REG:
        raise ValueError(f"Register {reg_1} greater than {MAX_REG}!")
    if reg_2 > MAX_REG:
        raise ValueError(f"Register {reg_2} greater than {MAX_REG}!")
    if jump > ROM_SIZE:
        raise ValueError(f"Jump point {jump} greater than ROM size {ROM_SIZE}!")


class CPU:
    """A high-level implemenation of a CPU's functionality."""
    def __init__(self):
        self.program_counter: int = 0
        self.registers: list[int] = [0] * 11
        self.rom: list[int] = [0] * ROM_SIZE
        self.ram: RAM = RAM(RAM_SIZE)

        self.opcodes = [
            Opcode(0x00, "NOP"),
            Opcode(0x41, "IMM", self.immediate),
            Opcode(0x44, "JMP", self.jump),
            Opcode(0x91, "CPY", self.copy),
            Opcode(0xE0, "AND", self.logical_and),
            Opcode(0xE2, "OR",  self.logical_or),
            Opcode(0xA3, "NOT", self.logical_not),
            Opcode(0xEF, "ADD", self.add),
            Opcode(0xE8, "SUB", self.sub),
            Opcode(0xEC, "SEG", self.int_to_sevenseg),
            Opcode(0xF1, "EQ",  self.conditional_eq),
            Opcode(0xF2, "LT",  self.conditional_lt),
            Opcode(0xF3, "LTE", self.conditional_lte),
            Opcode(0xF5, "NEQ", self.conditional_neq),
            Opcode(0xF6, "GTE", self.conditional_gte),
            Opcode(0xF7, "GT",  self.conditional_gt),
            Opcode(0x0F, "HLT", self.halt),
        ]

        self._just_jumped = False
        self._last_instruction_size = 0
        self._halt_flag = False

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

    def copy(self, reg_from: Register, reg_to: Register):
        """CPY <from> <to>
        Copy the value from register `from` to register `to`."""
        logger.debug(f"CPY {reg_from} {reg_to}")
        if reg_from > MAX_REG:
            raise ValueError(f"Register {reg_from} greater than {MAX_REG}!")
        if reg_to > MAX_REG:
            raise ValueError(f"Register {reg_to} greater than {MAX_REG}!")
        self.registers[reg_to] = self.registers[reg_from]

    def immediate(self, value: int):
        """IMM <value>
        Uses `value` like it's just a normal number.
        Can also be in the form of 0xVAL, 0bVAL, or a single character \"V\""""
        logger.debug(f"IMM {value}")
        if value >= MAX_INT:
            raise ValueError(f"Immediate value {value} higher than {MAX_INT}!")
        self.registers[Registers.IMR] = value

    def jump(self, position: int):
        """JMP <position>
        Jump to position `position` in ROM."""
        logger.debug(f"JMP {position}")
        if position >= ROM_SIZE:
            raise ValueError(f"You tried to leave the ROM! ({position})")
        self.program_counter = position % ROM_SIZE
        self._just_jumped = True

    def add(self, reg_1, reg_2, reg_to):
        """ADD <A> <B> <to>
        Add the values from registers A and B and copy it to register `to`."""
        logger.debug(f"ADD {reg_1} {reg_2} {reg_to}")
        check_arithmetic(reg_1, reg_2, reg_to)
        self.registers[reg_to] = (self.registers[reg_1] + self.registers[reg_2]) % MAX_INT

    def sub(self, reg_1, reg_2, reg_to):
        """SUB <A> <B> <to>
        Subtract the values from registers A and B and copy it to register `to`."""
        logger.debug(f"SUB {reg_1} {reg_2} {reg_to}")
        check_arithmetic(reg_1, reg_2, reg_to)
        self.registers[reg_to] = (self.registers[reg_1] - self.registers[reg_2]) % MAX_INT

    def logical_and(self, reg_1, reg_2, reg_to):
        """AND <A> <B> <to>
        Logical AND the values from registers A and B and copy it to register `to`."""
        logger.debug(f"AND {reg_1} {reg_2} {reg_to}")
        check_arithmetic(reg_1, reg_2, reg_to)
        self.registers[reg_to] = (self.registers[reg_1] & self.registers[reg_2]) % MAX_INT

    def logical_or(self, reg_1, reg_2, reg_to):
        """OR <A> <B> <to>
        Logical OR the values from registers A and B and copy it to register `to`."""
        logger.debug(f"OR {reg_1} {reg_2} {reg_to}")
        check_arithmetic(reg_1, reg_2, reg_to)
        self.registers[reg_to] = (self.registers[reg_1] | self.registers[reg_2]) % MAX_INT

    def logical_not(self, reg, reg_to):
        """NOT <A> <to>
        Logical NOT the value from register A and copy it to register `to`."""
        logger.debug(f"NOT {reg} {reg_to}")
        check_arithmetic(reg, 0, reg_to)  # HACK: don't want to make a seperate checking function, only 1-operand math func.
        self.registers[reg_to] = (~self.registers[reg]) % MAX_INT

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
        """NEQ <pos_from> <reg_to>
        Load the value from position `from_pos` in RAM into register `to_reg`."""
        logger.debug(f"RLD {pos_from} {reg_to}")
        if reg_to > MAX_REG:
            raise ValueError(f"Register {reg_to} greater than {MAX_REG}!")
        if pos_from > ROM_SIZE:
            raise ValueError(f"Position {pos_from} greater than {ROM_SIZE}!")
        self.registers[reg_to] = self.ram.load(pos_from)

    def ram_save(self, reg_from, pos_to):
        """NEQ <from_reg> <to_pos>
        Save the value from register `from_reg` to RAM position `to_pos`."""
        logger.debug(f"RSV {reg_from} {pos_to}")
        if reg_from > MAX_REG:
            raise ValueError(f"Register {reg_from} greater than {MAX_REG}!")
        if pos_to > ROM_SIZE:
            raise ValueError(f"Position {pos_to} greater than {ROM_SIZE}!")
        self.ram.save(pos_to, self.registers[reg_from])

    def halt(self):
        self._halt_flag = True

    def step(self):
        """Run one clock cycle. Just keep doing this until we're out of ROM."""
        # If we're halted, we're... halted.
        if self._halt_flag:
            return

        # Get the current instruction and process it.
        current_ins = self.rom[self.program_counter]
        # This is needed because we're genericizing here and we need no not get IndexErrors.
        extended_rom = self.rom + [0, 0, 0, 0]
        # Get the next few values in case they're operands.
        operands = extended_rom[self.program_counter + 1:self.program_counter + 5]
        found = False
        for o in self.opcodes:
            if o.value != current_ins:
                continue
            found = True
            o.run(operands)
            self._last_instruction_size = o.width
            self._current_instruction = f"{o.assembly} {' '.join(str(o) for o in operands[:o.width -1])}"
        if not found:
            raise ValueError(f"Unknown opcode {current_ins} at counter {self.program_counter}")

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
                raise ValueError(f"Unknown instruction! {i}")

        self.load(instructions)

    def reset(self):
        """Clear the resgisters and start at the beginning of the program."""
        self.program_counter = 0
        self._halt_flag = False
        for v in range(len(self.registers)):
            self.registers[v] = 0

    def input(self, value: int):
        """Set the input register to `value.`"""
        self.input_register = value % MAX_INT

    def __str__(self) -> str:
        return f"PROGRAM COUNTER: 0x{self.program_counter:X}\nREGISTERS: {[hex(v).upper() for v in self.registers[:8]]}\nINPUT: 0x{self.input_register:X} ({self.input_register})\nOUTPUT: 0x{self.output_register:X} ({self.output_register})"

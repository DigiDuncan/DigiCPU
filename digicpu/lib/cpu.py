import re
from typing import Literal

# LOGGING STUFF
import logging

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
MAX_INT = 256
MAX_REG = 10

class Opcodes:
    IMM = 0x01
    JMP = 0x04
    CPY = 0x51
    ADD = 0xAF
    SUB = 0xA8
    AND = 0xA0
    OR = 0xA2
    NOT = 0x63
    EQ = 0xB1
    LT = 0xB2
    LTE = 0xB3
    NEQ = 0xB5
    GTE = 0xB6
    GT = 0xB7
    NOP = 0x0
    SEG = 0x64
    IN = 8
    ADR = 9
    DAT = 10
    HLT = 0x0F

widths = {
    "IMM" : 2,
    "JMP" : 2,
    "CPY" : 3,
    "ADD" : 4,
    "SUB" : 4,
    "AND" : 4,
    "OR " : 4,
    "NOT" : 3,
    "EQ"  : 4,
    "LT"  : 4,
    "LTE" : 4,
    "NEQ" : 4,
    "GTE" : 4,
    "GT"  : 4,
    "NOP" : 1,
    "SEG" : 4,
    "HLT" : 1
}

def make_int(self, i: str) -> int:
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

        self._just_jumped = False
        self._last_instruction_size = 0
        self._halt_flag = False

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
        self.registers[0] = value
    
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

    def halt(self):
        self._halt_flag = True

    def step(self):
        """Run one clock cycle. Just keep doing this until we're out of ROM."""
        if self._halt_flag:
            return
        current_ins = self.rom[self.program_counter]
        extended_rom = self.rom + [0, 0, 0, 0]
        o1, o2, o3, o4 = extended_rom[self.program_counter + 1:self.program_counter + 5]
        match current_ins:
            case Opcodes.NOP:
                pass
            case Opcodes.IMM:
                self.immediate(o1)
            case Opcodes.JMP:
                self.jump(o1)
            case Opcodes.CPY:
                self.copy(o1, o2)
            case Opcodes.ADD:
                self.add(o1, o2, o3)
            case Opcodes.SUB:
                self.sub(o1, o2, o3)
            case Opcodes.AND:
                self.add(o1, o2, o3)
            case Opcodes.OR:
                self.logical_or(o1, o2, o3)
            case Opcodes.NOT:
                self.logical_not(o1, o2)
            case Opcodes.EQ:
                self.conditional_eq(o1, o2, o3)
            case Opcodes.LT:
                self.conditional_lt(o1, o2, o3)
            case Opcodes.LTE:
                self.conditional_lte(o1, o2, o3)
            case Opcodes.NEQ:
                self.conditional_neq(o1, o2, o3)
            case Opcodes.GTE:
                self.conditional_gte(o1, o2, o3)
            case Opcodes.GT:
                self.conditional_gt(o1, o2, o3)
            case Opcodes.SEG:
                self.int_to_sevenseg(o1, o2)
            case Opcodes.HLT:
                self.halt()
            case _:
                raise ValueError(f"Unknown opcode {current_ins} at counter {self.program_counter}")
            
        self._last_instruction_size = (current_ins & 0b11000000) >> 6
        if not self._just_jumped:
            self.program_counter += (self._last_instruction_size + 2)
        self._just_jumped = False

    def load(self, rom: list[int]):
        """Load a program from a list of bytes."""
        self.rom = [0] * ROM_SIZE
        for n, i in enumerate(rom):
            self.rom[n] = i

    def load_string(self, s: str):
        """Load an assembly program from string."""
        s = re.sub(r"#(.*)\n", "")  # comments

        replacements = {}
        constants: list[str] = re.findall(r"CONST (.+ .+)\n", s)
        for constant in constants:
            split = constant.split(maxsplit = 1)
            replacements[split[0]] = split[1]

        for key, value in replacements.items():
            s = s.replace(key, value)

        s = s.upper()

        labels = {}
        lines = s.split("\n")
        n = 0
        for line in lines:
            line = line.strip()
            if m := re.match(r"LABEL (.*)"):
                labels[m.group(1)] = n
            else:
                for ins, w in widths.items():
                    if line.startswith(ins):
                        n += w
                        break

        s = re.sub(r"LABEL (.*)\n", "")

        s = s.replace("\n", " ")
        instructions = s.split()
        instructions = [i.strip().upper() for i in instructions]
        for n, i in enumerate(instructions):
            match i:
                case "NOP":
                    instructions[n] = Opcodes.NOP
                    continue
                case "IMM":
                    instructions[n] = Opcodes.IMM
                    continue
                case "JMP":
                    instructions[n] = Opcodes.JMP
                    continue
                case "CPY":
                    instructions[n] = Opcodes.CPY
                    continue
                case "ADD":
                    instructions[n] = Opcodes.ADD
                    continue
                case "SUB":
                    instructions[n] = Opcodes.SUB
                    continue
                case "AND":
                    instructions[n] = Opcodes.AND
                    continue
                case "OR":
                    instructions[n] = Opcodes.OR
                    continue
                case "NOT":
                    instructions[n] = Opcodes.NOT
                    continue
                case "EQ":
                    instructions[n] = Opcodes.EQ
                    continue
                case "LT":
                    instructions[n] = Opcodes.LT
                    continue
                case "LTE":
                    instructions[n] = Opcodes.LTE
                    continue
                case "NEQ":
                    instructions[n] = Opcodes.NEQ
                    continue
                case "GTE":
                    instructions[n] = Opcodes.GTE
                    continue
                case "GT":
                    instructions[n] = Opcodes.GT
                    continue
                case "SEG":
                    instructions[n] = Opcodes.SEG
                    continue
                case "HLT":
                    instructions[n] = Opcodes.HLT
                    continue
                case "IN":
                    instructions[n] = Opcodes.IN
                    continue
                case "ADR":
                    instructions[n] = Opcodes.ADR
                    continue
                case "DAT":
                    instructions[n] = Opcodes.DAT
                    continue

            instructions[n] = make_int(i)

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

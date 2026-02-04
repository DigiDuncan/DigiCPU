from digicpu.lib.errors import (RAMOutOfBoundsError, RegisterOverflowError,
                                ROMOutOfBoundsError)
from digicpu.lib.types import MAX_REG, RAM_SIZE, ROM_SIZE, Position, Register


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

def check_registers(*registers: Register) -> None:
    for r in registers:
        if r > MAX_REG:
            raise RegisterOverflowError(r)
        
def check_rom_positions(*positions: Position) -> None:
    for p in positions:
        if p > ROM_SIZE:
            raise ROMOutOfBoundsError(p)

def check_ram_positions(*positions: Position) -> None:
    for p in positions:
        if p > RAM_SIZE:
            raise RAMOutOfBoundsError(p)

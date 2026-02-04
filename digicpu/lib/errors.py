from digicpu.lib.types import MAX_INT, MAX_REG, RAM_SIZE, ROM_SIZE


class RegisterOverflowError(ValueError):
    def __init__(self, value: int) -> None:
        super().__init__(f"Register {value} greater than {MAX_REG}!")

class ROMOutOfBoundsError(ValueError):
    def __init__(self, value: int) -> None:
        super().__init__(f"Position {value} outside of ROM (max size {ROM_SIZE})!")

class RAMOutOfBoundsError(ValueError):
    def __init__(self, value: int) -> None:
        super().__init__(f"Position {value} outside of ROM (max size {RAM_SIZE})!")

class IntegerOverflowError(ValueError):
    def __init__(self, value: int) -> None:
        super().__init__(f"Integer {value} higher than maximum value {MAX_INT})!")

class UnknownOpcodeError(ValueError):
    def __init__(self, opcode: int, counter: int | None) -> None:
        if counter is not None:
            super().__init__(f"Unknown opcode {opcode:02X} at counter {counter}!")
        else:
            super().__init__(f"Unknown opcode {opcode:02X}!")

class UnknownInstructionError(ValueError):
    def __init__(self, instruction: str) -> None:
        super().__init__(f"Unknown instruction '{instruction}'!")

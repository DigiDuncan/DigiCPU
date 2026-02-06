import re
from typing import cast

from digicpu.core.opcode import Opcode
from digicpu.lib.errors import UnknownInstructionError, ROMTooLargeError
from digicpu.lib.types import Registers, ROM_SIZE
from digicpu.lib.utils import make_int


def assemble(s: str, opcodes: list[Opcode]) -> list[int]:
    valid_opcodes = [o.assembly for o in opcodes]
    
    s = re.sub(r"#(.*)\n", "\n", s)  # comments
    s = s.replace("...", "NOP") # ... is a macro for NOP

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

    # Replace semis with newlines for one-liners
    s = s.replace(";", "\n")

    # Fix legacy IMM
    s = re.sub(r"IMM ([^\s]+)\n", "IMM \\1 0\n", s)

    # Store labels for later.
    labels = {}
    lines = s.split("\n")
    n = 0
    for line in lines:
        line = line.strip()

        # If we find a label definition, save it.
        if m := re.match(r"LABEL ([^:]+):?", line):
            labels[m.group(1)] = n
        else:
            # Step over opcodes, since we know how wide they are.
            for o in opcodes:
                if line.startswith(o.assembly):
                    n += o.width
                    break

    # Replace all labels with nothing, since we dealt with them.
    s = re.sub(r"LABEL (.*)\n", "", s)
    # Constants, too.
    s = re.sub(r"CONST (.*)\n", "", s)

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
            case x if x in valid_opcodes:
                opcode = next(o for o in opcodes if o.assembly == x)
                instructions[n] = opcode.value
                continue
            # Register aliases
            case x if x in [m.name for m in Registers]:
                instructions[n] = Registers[x]
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

    if len(instructions) > ROM_SIZE:
        ROMTooLargeError(len(instructions))

    return instructions

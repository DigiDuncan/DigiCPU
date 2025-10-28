# DigiCPU
A software-based very basic CPU made in Python.

## How it Works
**Barely!** I made this with almost no knowledge on how a CPU works other than some guidance from [@Arceus3251](http://github.com/Arceus3251).

Running the module will launch an [Arcade](https://api.arcade.academy/en/development/) window with eight seven-segment displays on it.

Register 9 is an address bus for the display (1-8 is each digit, left to right.)
Register 10 is a data bus and sends that value to the display in register 9.

## Controls
- `R`: Reset the CPU.
- `[SPACE]` Pause the CPU.
- `Keypad -`: Speed up the CPU.
- `Keypad +`: Slow down the CPU.
- `ZXCVBNM,`: Hold each key to set the input value to the CPU.

## Opcodes
|Canon Name                       |ASM  |b7 |b6 |b5 |b4 |b3 |b2 |b1 |b0 |Dec|Hex  |Width|Type       |Notes                                    |
|---------------------------------|-----|---|---|---|---|---|---|---|---|---|-----|-----|-----------|-----------------------------------------|
|No Operation                     |`NOP`|0  |0  |0  |0  |0  |0  |0  |0  |0  |`00` |1    |Immediate  |                                         |
|Immediate                        |`IMM`|0  |1  |0  |0  |0  |0  |0  |1  |65 |`41` |2    |Immediate  |                                         |
|Jump                             |`JMP`|0  |1  |1  |1  |0  |1  |0  |0  |116|`74` |2    |Conditional|                                         |
|Copy                             |`CPY`|1  |0  |0  |1  |0  |0  |0  |1  |145|`91` |3    |Copy       |                                         |
|Logical And                      |`AND`|1  |1  |1  |0  |0  |0  |0  |0  |224|`E0` |4    |Logic      |                                         |
|Logical Or                       |`OR` |1  |1  |1  |0  |0  |0  |1  |0  |226|`E2` |4    |Logic      |                                         |
|Logical Not                      |`NOT`|1  |0  |1  |0  |0  |0  |1  |1  |163|`A3` |3    |Logic      |                                         |
|Add                              |`ADD`|1  |1  |1  |0  |1  |0  |0  |0  |232|`E8` |4    |Math       |                                         |
|Subtract                         |`SUB`|1  |1  |1  |0  |1  |1  |1  |1  |239|`EF` |4    |Math       |                                         |
|Modulo                           |`MOD`|1  |1  |1  |0  |1  |0  |0  |1  |233|`E9` |4    |Math       |Implemented in Python, unsure in hardware|
|Int to Seven Segment             |`SEG`|1  |0  |1  |0  |1  |1  |0  |0  |172|`AC` |3    |Math       |Implemented in Python, unsure in hardware|
|Conditional Equals               |`EQ` |1  |1  |1  |1  |0  |0  |0  |1  |241|`F1` |4    |Conditional|                                         |
|Conditional Less Than            |`LT` |1  |1  |1  |1  |0  |0  |1  |0  |242|`F2` |4    |Conditional|                                         |
|Conditional Less Than Or Equal   |`LTE`|1  |1  |1  |1  |0  |0  |1  |1  |243|`F3` |4    |Conditional|                                         |
|Conditional Not Equal            |`NEQ`|1  |1  |1  |1  |0  |1  |0  |1  |245|`F5` |4    |Conditional|                                         |
|Conditional Greater Than Or Equal|`GTE`|1  |1  |1  |1  |0  |1  |1  |0  |246|`F6` |4    |Conditional|                                         |
|Conditional Greater Than         |`GT` |1  |1  |1  |1  |0  |1  |1  |1  |247|`F7` |4    |Conditional|                                         |
|RAM Load                         |`RLD`|1  |0  |0  |1  |1  |0  |0  |0  |152|`98` |3    |RAM        |                                         |
|RAM Save                         |`RSV`|1  |0  |0  |1  |1  |0  |0  |1  |153|`99` |3    |RAM        |                                         |
|RAM Load from Register           |`RLR`|1  |0  |0  |1  |1  |0  |1  |0  |154|`9A` |3    |RAM        |                                         |
|RAM Save from Register           |`RSR`|1  |0  |0  |1  |1  |0  |1  |1  |155|`9B` |3    |RAM        |                                         |
|Push                             |`PSH`|0  |1  |0  |1  |1  |1  |0  |0  |92 |`5C` |2    |RAM        |                                         |
|Pop                              |`POP`|0  |1  |0  |1  |1  |1  |0  |1  |93 |`5D` |2    |RAM        |                                         |
|Halt                             |`HLT`|0  |0  |0  |0  |1  |1  |1  |1  |15 |`0F` |1    |Immediate  |                                         |
|*Return*                         |`RET`|0  |0  |0  |0  |1  |0  |0  |0  |8  |`08` |1    |Immediate  |*Unused, reserved*                       |
|Logical Xor                      |`XOR`|1  |1  |1  |0  |0  |1  |0  |0  |228|`E4` |4    |Logic      |                                         |
|Shift Left                       |`SHL`|1  |1  |1  |0  |1  |0  |1  |0  |234|`EA` |4    |Math       |                                         |
|Shift Right                      |`SHR`|1  |1  |1  |0  |1  |0  |1  |1  |235|`EB` |4    |Math       |                                         |
|Multiply                         |`MUL`|1  |1  |1  |0  |1  |1  |0  |0  |236|`EC` |4    |Math       |                                         |
|Minimum                          |`MIN`|1  |1  |1  |0  |1  |1  |0  |1  |237|`ED` |4    |Math       |                                         |
|Maximum                          |`MAX`|1  |1  |1  |0  |1  |1  |1  |0  |238|`EE` |4    |Math       |                                         |

### Some Notes About Opcodes
- The most significant two bits (7 and 6) denote the width of the instruction minus one. Since all instructions must be at least one wide, bits 7 and 6 being `00` denote the instruction being one wide, `01` means two wide, etc.
- Bits 5 and 4 denote the type of instruction.
  - `00`: Immediate
  - `01`: Copy/RAM (bit 3 differentiates between copy (`0`) and RAM (`1`))
  - `10`: Logic/Math (bit 3 differentiates between logic (`0`) and math (`1`))
  - `11`: Conditional
- `NOP` is all 0s.
- `HLT` is `0x0F`.

## Comments
You can write a comment by starting your line with `#`. The assembler will ignore that line.

## Constants
You can define a constant like: `CONST <NAME> <VALUE>`. ~~You totally can't make macros with this.~~

## Labels
You can define a label with `LABEL <NAME>`, and then jump to it with `JMP <NAME>`.

## Register Aliases
You can use the keywords `IMR`, `IN`, `ADDR`, and `DATA` to reference the registers 0, 8, 9, and 10, respectively.

# DigiCPU
A software-based very basic 8-bit CPU made in Python.

## How it Works
**Barely!** I made this with almost no knowledge on how a CPU works other than some guidance from [@Arceus3251](http://github.com/Arceus3251).

Running the module will launch an [Arcade](https://api.arcade.academy/en/development/) window with eight seven-segment displays on it.

Register 9 is an address bus for the display (1-8 is each digit, left to right.)
Register 10 is a data bus and sends that value to the display in register 9.
Register 11 is the stack pointer.

## Controls
- `R`: Reset the CPU.
- `[SPACE]` Pause the CPU.
- `Keypad -`: Speed up the CPU.
- `Keypad +`: Slow down the CPU.
- `ZXCVBNM,`: Hold each key to set the input value to the CPU.

## Opcodes

| Canon Name                        | ASM   | OP7 (W1) | OP6 (W0) | OP5 (T2) | OP4 (T1) | OP3 (T0) | OP2 | OP1 | OP0 | Dec | Hex   | Width | Module      |
|-----------------------------------|-------|----------|----------|----------|----------|----------|-----|-----|-----|-----|-------|-------|-------------|
| No Operation                      | `NOP` | 0        | 0        | 0        | 0        | 0        | 0   | 0   | 0   | 0   | `00`  | 1     | Immediate   |
| Immediate                         | `IMM` | 0        | 1        | 0        | 0        | 0        | 0   | 0   | 1   | 65  | `41`  | 2     | Immediate   |
| Halt                              | `HLT` | 0        | 0        | 0        | 0        | 0        | 1   | 1   | 1   | 7   | `07`  | 1     | Immediate   |
| Copy                              | `CPY` | 1        | 0        | 0        | 1        | 0        | 0   | 0   | 1   | 145 | `91`  | 3     | Copy        |
| Copy                              | `CLR` | 0        | 1        | 0        | 1        | 0        | 0   | 0   | 0   | 80  | `50`  | 2     | Copy        |
| Conditional Equals                | `EQ`  | 1        | 1        | 1        | 1        | 0        | 0   | 0   | 1   | 241 | `F1`  | 4     | Conditional |
| Conditional Less Than             | `LT`  | 1        | 1        | 1        | 1        | 0        | 0   | 1   | 0   | 242 | `F2`  | 4     | Conditional |
| Conditional Less Than Or Equal    | `LTE` | 1        | 1        | 1        | 1        | 0        | 0   | 1   | 1   | 243 | `F3`  | 4     | Conditional |
| Conditional Not Equal             | `NEQ` | 1        | 1        | 1        | 1        | 0        | 1   | 0   | 1   | 245 | `F5`  | 4     | Conditional |
| Conditional Greater Than Or Equal | `GTE` | 1        | 1        | 1        | 1        | 0        | 1   | 1   | 0   | 246 | `F6`  | 4     | Conditional |
| Conditional Greater Than          | `GT`  | 1        | 1        | 1        | 1        | 0        | 1   | 1   | 1   | 247 | `F7`  | 4     | Conditional |
| Logical Nand                      | `NND` | 1        | 1        | 1        | 0        | 0        | 0   | 0   | 0   | 224 | `E0`  | 4     | Logic       |
| Logical Or                        | `OR`  | 1        | 1        | 1        | 0        | 0        | 0   | 0   | 1   | 225 | `E1`  | 4     | Logic       |
| Logical And                       | `AND` | 1        | 1        | 1        | 0        | 0        | 0   | 1   | 0   | 226 | `E2`  | 4     | Logic       |
| Logical Nor                       | `NOR` | 1        | 1        | 1        | 0        | 0        | 0   | 1   | 1   | 227 | `E3`  | 4     | Logic       |
| Logical Not                       | `NOT` | 1        | 0        | 1        | 0        | 0        | 1   | 0   | 0   | 164 | `A4`  | 3     | Logic       |
| Logical Xor                       | `XOR` | 1        | 1        | 1        | 0        | 0        | 1   | 0   | 1   | 229 | `E5`  | 4     | Logic       |
| Jump                              | `JMP` | 0        | 1        | 1        | 0        | 0        | 1   | 0   | 0   | 100 | `64`  | 2     | Logic       |
| Add                               | `ADD` | 1        | 1        | 1        | 0        | 1        | 0   | 0   | 0   | 232 | `E8`  | 4     | Math        |
| Subtract                          | `SUB` | 1        | 1        | 1        | 0        | 1        | 0   | 0   | 1   | 233 | `E9`  | 4     | Math        |
| Multiply                          | `MUL` | 1        | 1        | 1        | 0        | 1        | 0   | 1   | 0   | 234 | `EA`  | 4     | Math        |
| Modulo                            | `MOD` | 1        | 1        | 1        | 0        | 1        | 0   | 1   | 1   | 235 | `EB`  | 4     | Math        |
| Shift Left                        | `SHL` | 1        | 1        | 1        | 0        | 1        | 1   | 0   | 0   | 236 | `EC`  | 4     | Math        |
| Shift Right                       | `SHR` | 1        | 1        | 1        | 0        | 1        | 1   | 0   | 1   | 237 | `ED`  | 4     | Math        |
| Minimum                           | `MIN` | 1        | 1        | 1        | 0        | 1        | 1   | 1   | 0   | 238 | `EE`  | 4     | Math        |
| Maximum                           | `MAX` | 1        | 1        | 1        | 0        | 1        | 1   | 1   | 1   | 239 | `EF`  | 4     | Math        |
| RAM Load                          | `RLD` | 1        | 0        | 0        | 1        | 1        | 0   | 0   | 0   | 152 | `98`  | 3     | RAM         |
| RAM Save                          | `RSV` | 1        | 0        | 0        | 1        | 1        | 0   | 0   | 1   | 153 | `99`  | 3     | RAM         |
| RAM Load from Register            | `RLR` | 1        | 0        | 0        | 1        | 1        | 0   | 1   | 0   | 154 | `9A`  | 3     | RAM         |
| RAM Save from Register            | `RSR` | 1        | 0        | 0        | 1        | 1        | 0   | 1   | 1   | 155 | `9B`  | 3     | RAM         |
| Push                              | `PSH` | 0        | 1        | 0        | 1        | 1        | 1   | 0   | 0   | 92  | `5C`  | 2     | RAM         |
| Pop                               | `POP` | 0        | 1        | 0        | 1        | 1        | 1   | 0   | 1   | 93  | `5D`  | 2     | RAM         |
| Int to Seven Segment              | `SEG` | 1        | 0        | 1        | 1        | 1        | 1   | 1   | 1   | 191 | `BF`  | 3     | Extensions  |
| Add with Overflow                 | `ADO` | 1        | 1        | 1        | 1        | 1        | 0   | 0   | 0   | 248 | `F8`  | 3     | Extensions  |
| Multiply with Overflow            | `MLO` | 1        | 0        | 1        | 1        | 1        | 0   | 1   | 0   | 250 | `FA`  | 3     | Extensions  |

### Some Notes About Opcodes
- The most significant two bits (7 and 6) denote the width of the instruction minus one. Since all instructions must be at least one wide, bits 7 and 6 being `00` denote the instruction being one wide, `01` means two wide, etc.
- Bits 5, 4, and 3 denote the type of instruction:

| Value | Module      |
|-------|-------------|
| `000` | Immediate   |
| `001` | *Unused*    |
| `010` | Copy        |
| `011` | RAM         |
| `100` | Logic       |
| `101` | Math        |
| `110` | Conditional |
| `111` | Extensions  |

- `NOP` is all 0s.
- `HLT` is `0x07`.

## Comments
You can write a comment by starting your line with `#`. The assembler will ignore that line.

## Constants
You can define a constant like: `CONST <NAME> <VALUE>`. ~~You totally can't make macros with this.~~

## Labels
You can define a label with `LABEL <NAME>`, and then jump to it with `JMP <NAME>`.

## Register Aliases
You can use the keywords `IMR`, `IN`, `ADDR`, `DATA`, `STACK`, and `OF` to reference the registers 0, 8, 9, 10, 11, and 12 respectively.

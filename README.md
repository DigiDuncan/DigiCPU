# DigiCPU
A software-based very basic 8-bit CPU made in Python.

## How it Works
**Barely!** I made this with almost no knowledge on how a CPU works other than some guidance from [@Arceus3251](http://github.com/Arceus3251).

Running the module will launch an [Arcade](https://api.arcade.academy/en/development/) window with eight seven-segment displays on it.

The CPU has the following registers:
- General purpose registers `0...7`
- Address/Data lines for the seven segment display on `8` and `9`
- Address/Data lines for the RAM on `10` and `11`
- Stack pointer `12`
- Overflow register `13`
- Input register `14`

The CPU also has overflow, zero, and negative flags.

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
| Immediate                         | `IMM` | 1        | 0        | 0        | 0        | 0        | 0   | 0   | 1   | 129 | `81`  | 2     | Immediate   |
| Halt                              | `HLT` | 0        | 0        | 0        | 0        | 0        | 1   | 1   | 1   | 7   | `07`  | 1     | Immediate   |
| Copy                              | `CPY` | 1        | 0        | 0        | 1        | 0        | 0   | 0   | 1   | 145 | `91`  | 3     | Copy        |
| Clear Flags                       | `CLF` | 0        | 0        | 0        | 0        | 1        | 0   | 0   | 0   | 8   | `08`  | 1     | Flag        |
| Clear Negative Flag               | `CNF` | 0        | 0        | 0        | 0        | 1        | 0   | 0   | 1   | 9   | `09`  | 1     | Flag        |
| Clear Zero Flag                   | `CZF` | 0        | 0        | 0        | 0        | 1        | 0   | 1   | 0   | 10  | `0A`  | 1     | Flag        |
| Clear Overflow Flag               | `COF` | 0        | 0        | 0        | 0        | 1        | 0   | 1   | 1   | 11  | `0B`  | 1     | Flag        |
| Jump If Negative Flag             | `JNF` | 0        | 1        | 0        | 0        | 1        | 0   | 0   | 1   | 73  | `49`  | 2     | Flag        |
| Jump If Not Negative Flag         | `JNN` | 0        | 1        | 0        | 0        | 1        | 1   | 0   | 1   | 77  | `4D`  | 2     | Flag        |
| Jump If Zero Flag                 | `JZF` | 0        | 1        | 0        | 0        | 1        | 0   | 1   | 0   | 74  | `4A`  | 2     | Flag        |
| Jump If Not Zero Flag             | `JNZ` | 0        | 1        | 0        | 0        | 1        | 1   | 1   | 0   | 78  | `4E`  | 2     | Flag        |
| Jump If Overflow Flag             | `JOF` | 0        | 1        | 0        | 0        | 1        | 0   | 1   | 1   | 75  | `4B`  | 2     | Flag        |
| Jump If Not Overflow Flag         | `JNO` | 0        | 1        | 0        | 0        | 1        | 1   | 1   | 1   | 79  | `4F`  | 2     | Flag        |
| Conditional Equal                 | `EQ`  | 1        | 1        | 1        | 1        | 0        | 0   | 0   | 1   | 241 | `F1`  | 4     | Conditional |
| Conditional Less Than             | `LT`  | 1        | 1        | 1        | 1        | 0        | 0   | 1   | 0   | 242 | `F2`  | 4     | Conditional |
| Conditional Less Than Or Equal    | `LTE` | 1        | 1        | 1        | 1        | 0        | 0   | 1   | 1   | 243 | `F3`  | 4     | Conditional |
| Conditional Not Equal             | `NEQ` | 1        | 1        | 1        | 1        | 0        | 1   | 0   | 1   | 245 | `F5`  | 4     | Conditional |
| Conditional Greater Than Or Equal | `GTE` | 1        | 1        | 1        | 1        | 0        | 1   | 1   | 0   | 246 | `F6`  | 4     | Conditional |
| Conditional Greater Than          | `GT`  | 1        | 1        | 1        | 1        | 0        | 1   | 1   | 1   | 247 | `F7`  | 4     | Conditional |
| Jump                              | `JMP` | 0        | 1        | 1        | 1        | 0        | 0   | 0   | 1   | 113 | `71`  | 2     | Conditional |
| Jump from Register                | `JMR` | 0        | 1        | 1        | 0        | 0        | 1   | 0   | 1   | 117 | `75`  | 2     | Logic       |
| Logical Nand                      | `NND` | 1        | 1        | 1        | 0        | 0        | 0   | 0   | 0   | 224 | `E0`  | 4     | Logic       |
| Logical Or                        | `OR`  | 1        | 1        | 1        | 0        | 0        | 0   | 0   | 1   | 225 | `E1`  | 4     | Logic       |
| Logical And                       | `AND` | 1        | 1        | 1        | 0        | 0        | 0   | 1   | 0   | 226 | `E2`  | 4     | Logic       |
| Logical Nor                       | `NOR` | 1        | 1        | 1        | 0        | 0        | 0   | 1   | 1   | 227 | `E3`  | 4     | Logic       |
| Logical Not                       | `NOT` | 1        | 0        | 1        | 0        | 0        | 1   | 0   | 0   | 164 | `A4`  | 3     | Logic       |
| Logical Xor                       | `XOR` | 1        | 1        | 1        | 0        | 0        | 1   | 0   | 1   | 229 | `E5`  | 4     | Logic       |
| Increment                         | `INC` | 0        | 1        | 1        | 0        | 1        | 0   | 0   | 0   | 104 | `68`  | 2     | Math        |
| Decrement                         | `DEC` | 0        | 1        | 1        | 0        | 1        | 0   | 0   | 1   | 105 | `69`  | 2     | Math        |
| Add                               | `ADD` | 1        | 1        | 1        | 0        | 1        | 0   | 0   | 0   | 232 | `E8`  | 4     | Math        |
| Subtract                          | `SUB` | 1        | 1        | 1        | 0        | 1        | 0   | 0   | 1   | 233 | `E9`  | 4     | Math        |
| Multiply                          | `MUL` | 1        | 1        | 1        | 0        | 1        | 0   | 1   | 0   | 234 | `EA`  | 4     | Math        |
| Modulo                            | `MOD` | 1        | 1        | 1        | 0        | 1        | 0   | 1   | 1   | 235 | `EB`  | 4     | Math        |
| Shift Left                        | `SHL` | 1        | 1        | 1        | 0        | 1        | 1   | 0   | 0   | 236 | `EC`  | 4     | Math        |
| Shift Right                       | `SHR` | 1        | 1        | 1        | 0        | 1        | 1   | 0   | 1   | 237 | `ED`  | 4     | Math        |
| Minimum                           | `MIN` | 1        | 1        | 1        | 0        | 1        | 1   | 1   | 0   | 238 | `EE`  | 4     | Math        |
| Maximum                           | `MAX` | 1        | 1        | 1        | 0        | 1        | 1   | 1   | 1   | 239 | `EF`  | 4     | Math        |
| Push                              | `PSH` | 0        | 1        | 0        | 1        | 1        | 1   | 0   | 0   | 92  | `5C`  | 2     | RAM         |
| Pop                               | `POP` | 0        | 1        | 0        | 1        | 1        | 1   | 0   | 1   | 93  | `5D`  | 2     | RAM         |
| Int to Seven Segment              | `SEG` | 1        | 0        | 1        | 1        | 1        | 1   | 1   | 1   | 191 | `BF`  | 3     | Extensions  |
| Add with Overflow                 | `ADO` | 1        | 1        | 1        | 1        | 1        | 0   | 0   | 0   | 248 | `F8`  | 4     | Extensions  |
| Multiply with Overflow            | `MLO` | 1        | 1        | 1        | 1        | 1        | 0   | 1   | 0   | 250 | `FA`  | 4     | Extensions  |

### Some Notes About Opcodes
- The most significant two bits (7 and 6) denote the width of the instruction minus one. Since all instructions must be at least one wide, bits 7 and 6 being `00` denote the instruction being one wide, `01` means two wide, etc. You can also think of this as denoting 
- Bits 5, 4, and 3 denote the type of instruction:

| Value | Module      |
|-------|-------------|
| `000` | Immediate   |
| `001` | Flag        |
| `010` | Copy        |
| `011` | RAM         |
| `100` | Logic       |
| `101` | Math        |
| `110` | Conditional |
| `111` | Extensions  |

- `NOP` is all 0s.

## Comments
You can write a comment by starting your line with `#`. The assembler will ignore that line.

## Constants
You can define a constant like: `CONST <NAME> <VALUE>`. ~~You totally can't make macros with this.~~

## Labels
You can define a label with `LABEL <NAME>`, and then jump to it with `JMP <NAME>` (or any other jumping operation).

## Register Aliases
You can use the keywords `IMR`, `IN`, `ADDR`, `DATA`, `STACK`, and `OF` to reference the registers 0, 8, 9, 10, 11, and 12 respectively.

# DigiCPU
A software-based very basic CPU made in Python.

## How it Works
**Barely!** I made this with almost no knowledge on how a CPU works other than some guidance from [@Arceus3251](http://github.com/Arceus3251).

Running the module will launch an [Arcade](https://api.arcade.academy/en/development/) window with eight seven-segment displays on it.

Register 9 is an address bus for the display (1-8 is each digit, left to right.)
Register 10 is a data bus and sends that value to the display in register 9.

## Controls
`R`: Reset the CPU.
`[SPACE]` Pause the CPU.
`Keypad -`: Speed up the CPU.
`Keypad +`: Slow down the CPU.

## Opcodes
|Canon Name                       |Shorthand|Byte 7|Byte 6|Byte 5|Byte 4|Byte 3|Byte 2|Byte 1|Byte 0|Decimal|Hex|
|---------------------------------|---------|------|------|------|------|------|------|------|------|-------|---|
|Immediate                        |IMM      |0     |0     |0     |0     |0     |0     |0     |1     |1      |1  |
|Jump                             |JMP      |0     |0     |0     |0     |0     |1     |0     |0     |4      |4  |
|Copy                             |CPY      |0     |1     |0     |1     |0     |0     |0     |1     |81     |51 |
|Add                              |ADD      |1     |0     |1     |0     |1     |1     |1     |1     |175    |AF |
|Subtract                         |SUB      |1     |0     |1     |0     |1     |0     |0     |0     |168    |A8 |
|Logical And                      |AND      |1     |0     |1     |0     |0     |0     |0     |0     |160    |A0 |
|Logical Or                       |OR       |1     |0     |1     |0     |0     |0     |1     |0     |162    |A2 |
|Logical Not                      |NOT      |0     |1     |1     |0     |0     |0     |1     |1     |99     |63 |
|Conditional Equals               |EQ       |1     |0     |1     |1     |0     |0     |0     |1     |177    |B1 |
|Conditional Less Than            |LT       |1     |0     |1     |1     |0     |0     |1     |0     |178    |B2 |
|Conditional Less Than Or Equal   |LTE      |1     |0     |1     |1     |0     |0     |1     |1     |179    |B3 |
|Conditional Not Equal            |NEQ      |1     |0     |1     |1     |0     |1     |0     |1     |181    |B5 |
|Conditional Greater Than Or Equal|GTE      |1     |0     |1     |1     |0     |1     |1     |0     |182    |B6 |
|Conditional Greater Than         |GT       |1     |0     |1     |1     |0     |1     |1     |1     |183    |B7 |
|No Operation                     |NOP      |0     |0     |0     |0     |0     |0     |0     |0     |0      |0  |
|Int to Seven Segment             |SEG      |0     |1     |1     |0     |0     |1     |0     |0     |100    |64 |
|Halt                             |HLT      |0     |0     |0     |0     |1     |1     |1     |1     |15     |F  |

## Comments
You can write a comment by starting you line with `#`. The assembler will ignore that line.

## Cosntants
You can define a constant like: `CONST <NAME> <VALUE>`. ~~You totally can't make macros with this.~~

## Labels
You can define a label with `LABEL <NAME>`, and then jump to it with `JMP <NAME>`.

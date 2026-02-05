import importlib.resources as pkg_resources

import arcade
from arcade.types import LRBT
import arrow
import pyglet
from pyglet.graphics import Batch

import digicpu.data.fonts
import digicpu.data.programs
from digicpu.constants import (ACCENT_DARK_COLOR, ACCENT_LIGHT_COLOR, BG_COLOR,
                               BG_DARK_COLOR, SCREEN_HEIGHT, SCREEN_TITLE,
                               SCREEN_WIDTH, TEXT_COLOR, TEXT_DIM_COLOR, BOX_COLOR)
from digicpu.core.cpu import CPU
from digicpu.core.display import SevenSegmentDisplay
from digicpu.lib.sevenseg import SevenSeg

PROGRAM = "new_test.asm"

class DigiCPUWindow(arcade.Window):
    def __init__(self, width, height, title, fps: float = 240.0):
        super().__init__(width, height, title, update_rate = 1 / fps)
        self.fps: float = fps

        self.now = arrow.now()
        self.sprite_list = arcade.SpriteList()

        self.cpu = CPU()
        self.output_display = SevenSegmentDisplay()

        self.digits: list[SevenSeg] = []
        for _ in range(8):
            self.digits.append(SevenSeg(SCREEN_WIDTH // 11, on_color = ACCENT_LIGHT_COLOR.rgb, off_color = ACCENT_DARK_COLOR.rgb))

        for n, d in enumerate(self.digits):
            self.sprite_list.append(d)
            d.center_y = self.height * 0.75
            d.left = ((d.width / 11) * (n + 1)) + (d.width * (n + 1))

        t = pkg_resources.read_text(digicpu.data.programs, PROGRAM)
        self.cpu.load_string(t)

        self.tick: int = 0
        self.tick_multiplier: int = 1

        self.input_value: int = 0
        self.paused: bool = True

        self.text_batch: Batch = Batch()

        self.fps_text = arcade.Text(f"{self.fps} FPS", 5, self.height - 5, anchor_y = "top", batch = self.text_batch, font_name = "Fira Code", font_size = 8)
        self.tick_text = arcade.Text(f"Tick {self.tick} | PAUSED", 5, self.fps_text.bottom, anchor_y = "top", batch=self.text_batch, font_name = "Fira Code", font_size = 8)
        self.rate_text = arcade.Text(f"Tick Rate 1:{self.tick_multiplier}", 5, self.tick_text.bottom, anchor_y = "top", batch=self.text_batch, font_name = "Fira Code", font_size = 8)

        self.busy_flag_text = arcade.Text("B", self.digits[0].left, self.digits[0].bottom - 5, font_size = 22, anchor_y = "top", font_name = "Fira Code", batch=self.text_batch, color = arcade.color.GRAY)
        self.negative_flag_text = arcade.Text("N", self.busy_flag_text.right + 5, self.digits[0].bottom - 5, font_size = 22, anchor_y = "top", font_name = "Fira Code", batch=self.text_batch, color = arcade.color.GRAY)
        self.zero_flag_text = arcade.Text("Z", self.negative_flag_text.right + 5, self.digits[0].bottom - 5, font_size = 22, anchor_y = "top", font_name = "Fira Code", batch=self.text_batch, color = arcade.color.GRAY)
        self.overflow_flag_text = arcade.Text("O", self.zero_flag_text.right + 5, self.digits[0].bottom - 5, font_size = 22, anchor_y = "top", font_name = "Fira Code", batch=self.text_batch, color = arcade.color.GRAY)

        self.program_text = arcade.Text("PC 00", self.digits[-1].right, self.digits[0].bottom - 5, font_size = 24, anchor_y = "top", anchor_x = "right", align = "right", batch=self.text_batch, font_name = "Fira Code", color = ACCENT_LIGHT_COLOR)

        self.rom_text_width = 16
        rom = ""
        for i, b in enumerate(self.cpu.rom):
            rom += f"{b:02X}"
            if i % self.rom_text_width == self.rom_text_width - 1:
                rom += "\n"
        rom.rstrip("\n")

        self.rom_doc = pyglet.text.document.FormattedDocument(rom)
        self.rom_doc.set_style(0, len(self.rom_doc.text), {"font_name": "Super Mario Bros. NES", "font_size": 12, "color": TEXT_DIM_COLOR})
        self.rom_text = pyglet.text.DocumentLabel(self.rom_doc, x = 5, y = -15, batch = self.text_batch, multiline = True, width = self.width, anchor_y = "bottom")

        self.last_real_rom_byte = 0xFF
        non_ops = [b for b in self.cpu.rom if b != 0]
        self.last_real_rom_byte = len(self.cpu.rom) - self.cpu.rom[::-1].index(non_ops[-1]) - 1

        self.instruction_doc = pyglet.text.document.FormattedDocument("NOP")
        self.instruction_doc.set_style(0, len(self.instruction_doc.text), {"font_name": "Super Mario Bros. NES", "font_size": 24, "color": TEXT_COLOR})
        self.instruction_text = pyglet.text.DocumentLabel(self.instruction_doc, 5, self.rom_text.top + 5, batch = self.text_batch)

        self.registers_doc = pyglet.text.document.FormattedDocument("00 " * len(self.cpu.registers))
        self.registers_doc.set_style(0, len(self.registers_doc.text), {"font_name": "Super Mario Bros. NES", "font_size": 12, "color": TEXT_DIM_COLOR})
        self.registers_text = pyglet.text.DocumentLabel(self.registers_doc, self.digits[0].left, self.digits[0].top + 5, batch = self.text_batch, anchor_y = "bottom")

        self.box_rect = LRBT(self.digits[0].left - 10, self.digits[-1].right + 10, self.program_text.bottom - 5, self.registers_text.top + 5)

    def setup(self):
        ...

    def on_show(self) -> None:
        self.paused = False

    def on_key_press(self, symbol, modifiers):
        if symbol == arcade.key.R:
            self.cpu.reset()
            self.output_display.reset()
            self.tick = 0
        elif symbol == arcade.key.NUM_ADD or symbol == arcade.key.EQUAL:
            new = max(self.tick_multiplier + 1, 1)
            self.tick_multiplier = new
        elif symbol == arcade.key.NUM_SUBTRACT or symbol == arcade.key.MINUS:
            new = max(self.tick_multiplier - 1, 1)
            self.tick_multiplier = new
        elif symbol == arcade.key.SPACE:
            self.paused = not self.paused
        elif symbol == arcade.key.RIGHT and self.paused:
            self.run_tick()
        elif symbol == arcade.key.GRAVE:
            with open("./dump.bin", "wb") as f:
                f.write(bytes(self.cpu.rom))

        elif symbol == arcade.key.Z:
            self.input_value += 128
        elif symbol == arcade.key.X:
            self.input_value += 64
        elif symbol == arcade.key.C:
            self.input_value += 32
        elif symbol == arcade.key.V:
            self.input_value += 16
        elif symbol == arcade.key.B:
            self.input_value += 8
        elif symbol == arcade.key.N:
            self.input_value += 4
        elif symbol == arcade.key.M:
            self.input_value += 2
        elif symbol == arcade.key.COMMA:
            self.input_value += 1

    def on_key_release(self, symbol, modifiers):
        if symbol == arcade.key.Z:
            self.input_value -= 128
        elif symbol == arcade.key.X:
            self.input_value -= 64
        elif symbol == arcade.key.C:
            self.input_value -= 32
        elif symbol == arcade.key.V:
            self.input_value -= 16
        elif symbol == arcade.key.B:
            self.input_value -= 8
        elif symbol == arcade.key.N:
            self.input_value -= 4
        elif symbol == arcade.key.M:
            self.input_value -= 2
        elif symbol == arcade.key.COMMA:
            self.input_value -= 1

    def update_rom_text(self):
        self.rom_doc.set_style(0, len(self.rom_doc.text), {"color": TEXT_DIM_COLOR})

        # ROM
        byte = self.cpu.program_counter - self.cpu._last_instruction_size
        line = byte // self.rom_text_width
        col = byte % self.rom_text_width
        idx = (self.rom_text_width * 2 * line) + (col * 2)
        span_width = self.cpu._last_instruction_size * 2
        if (col + span_width) > (self.rom_text_width * 2):
            span_width += 1
        self.rom_doc.set_style(idx, idx + span_width, {"color": TEXT_COLOR})

        # NOP
        line = (self.last_real_rom_byte + 1) // self.rom_text_width
        col = (self.last_real_rom_byte + 1) % self.rom_text_width
        idx = (self.rom_text_width * 2 * line) + (col * 2)
        self.rom_doc.set_style(idx, len(self.rom_doc.text), {"color": BG_DARK_COLOR})

        # INSTRUCTION
        self.instruction_doc.text = self.cpu._current_instruction_string
        self.instruction_doc.set_style(0, len(self.instruction_doc.text), {"color": TEXT_DIM_COLOR})
        idx = self.instruction_doc.text.index(" ")
        self.instruction_doc.set_style(0, idx, {"color": TEXT_COLOR})

        # REGISTERS
        self.registers_doc.set_style(0, idx, {"color": TEXT_DIM_COLOR})
        if len(self.cpu._current_instruction) > 2 and self.cpu._current_instruction[0] in [0x81, 0x91]:
            idx = self.cpu._current_instruction[2] * 3
            self.registers_doc.set_style(idx, idx + 2, {"color": TEXT_COLOR})


    def on_update(self, delta_time):
        self.fps = round(1 / delta_time)
        self.now = arrow.now()

        if self.paused:
            return

        self.run_tick()

    def run_tick(self):
        if not self.cpu._halt_flag:
            self.tick += 1
        if self.tick % self.tick_multiplier == 0:
            self.cpu.input_register = self.input_value
            if self.cpu.program_counter <= 255:
                self.cpu.step()

            # "Wiring"
            self.output_display.address = self.cpu.address_register
            self.output_display.data = self.cpu.data_register
            self.output_display.update()

            for n, digit in enumerate(self.digits):
                digit.set_bits(self.output_display.digits[n])

            self.sprite_list.update()

        self.rate_text.value = f"Tick Rate: 1:{self.tick_multiplier}"
        self.program_text.value = f"PC {self.cpu.program_counter:02X}"
        self.registers_text.text = " ".join([f"{r:02X}" for r in self.cpu.registers])

        self.busy_flag_text.color = ACCENT_LIGHT_COLOR if self.cpu.busy_flag else ACCENT_DARK_COLOR
        self.negative_flag_text.color = ACCENT_LIGHT_COLOR if self.cpu.negative_flag else ACCENT_DARK_COLOR
        self.zero_flag_text.color = ACCENT_LIGHT_COLOR if self.cpu.zero_flag else ACCENT_DARK_COLOR
        self.overflow_flag_text.color = ACCENT_LIGHT_COLOR if self.cpu.overflow_flag else ACCENT_DARK_COLOR

        self.update_rom_text()

    def on_draw(self):
        self.clear(BG_COLOR)
        arcade.draw_rect_filled(self.box_rect, BOX_COLOR)
        self.sprite_list.draw()
        self.text_batch.draw()

def main():
    with pkg_resources.path(digicpu.data.fonts, "NES.ttf") as p:
        arcade.load_font(p)
    with pkg_resources.path(digicpu.data.fonts, "FIRACODE.ttf") as p:
        arcade.load_font(p)

    window = DigiCPUWindow(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    window.setup()
    arcade.run()

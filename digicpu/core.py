import arcade
import arrow
import importlib.resources as pkg_resources
import logging

import digicpu.data
from digicpu.lib.cpu import CPU
from digicpu.lib.display import SevenSegmentDisplay
from digicpu.lib.sevenseg import SevenSeg

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

SCREEN_TITLE = "DigiCPU"
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720


class GameWindow(arcade.Window):
    def __init__(self, width, height, title):
        self.now = arrow.now()
        self.sprite_list: arcade.SpriteList = None

        self.cpu: CPU = None
        self.output_display: SevenSegmentDisplay = None

        self.digits: list[SevenSeg] = []

        self.fps = 240
        self.tick = 0
        self.tick_multiplier = 1

        self.fps_text: arcade.Text = None
        self.rate_text: arcade.Text = None
        self.tick_text: arcade.Text = None
        self.instruction_text: arcade.Text = None
        self.program_text: arcade.Text = None

        self.input_value = 0

        self.paused = False

        # Init the parent class
        super().__init__(width, height, title, update_rate = 1 / 240)

    def setup(self):
        self.sprite_list = arcade.SpriteList()
        self.cpu = CPU()
        t = pkg_resources.read_text(digicpu.data, "ramdom.asm")
        self.cpu.load_string(t)
        self.output_display = SevenSegmentDisplay()
        self.digits = []

        self.fps_text = arcade.Text(f"{self.fps} FPS", 5, 5)
        self.rate_text = arcade.Text(f"Tick Rate 1:{self.tick_multiplier}", 5, 25)
        self.tick_text = arcade.Text(f"Tick {self.tick} | PAUSED", 5, 45)
        self.instruction_text = arcade.Text("NOP", 5, SCREEN_HEIGHT - 5, font_size = 24, anchor_y = "top", font_name = "Fira Code")
        self.program_text = arcade.Text("Program Counter: 0", 5, SCREEN_HEIGHT - 45, font_size = 24, anchor_y = "top")
        self.input_text = arcade.Text("Input: 0", 5, SCREEN_HEIGHT - 85, font_size = 24, anchor_y = "top")

        for _ in range(8):
            self.digits.append(SevenSeg(SCREEN_WIDTH // 9))

        for d in self.digits:
            self.sprite_list.append(d)

        for n, d in enumerate(self.digits):
            d.center_y = self.height / 2
            d.left = ((d.width / 9) * (n + 1)) + (d.width * n)

    def on_key_press(self, key, modifiers):
        if key == arcade.key.R:
            self.cpu.reset()
            self.output_display.reset()
            self.tick = 0
        elif key == arcade.key.NUM_ADD:
            new = max(self.tick_multiplier + 1, 1)
            self.tick_multiplier = new
        elif key == arcade.key.NUM_SUBTRACT:
            new = max(self.tick_multiplier - 1, 1)
            self.tick_multiplier = new
        elif key == arcade.key.SPACE:
            self.paused = not self.paused

        elif key == arcade.key.Z:
            self.input_value += 128
        elif key == arcade.key.X:
            self.input_value += 64
        elif key == arcade.key.C:
            self.input_value += 32
        elif key == arcade.key.V:
            self.input_value += 16
        elif key == arcade.key.B:
            self.input_value += 8
        elif key == arcade.key.N:
            self.input_value += 4
        elif key == arcade.key.M:
            self.input_value += 2
        elif key == arcade.key.COMMA:
            self.input_value += 1

    def on_key_release(self, key, modifiers):
        if key == arcade.key.Z:
            self.input_value -= 128
        elif key == arcade.key.X:
            self.input_value -= 64
        elif key == arcade.key.C:
            self.input_value -= 32
        elif key == arcade.key.V:
            self.input_value -= 16
        elif key == arcade.key.B:
            self.input_value -= 8
        elif key == arcade.key.N:
            self.input_value -= 4
        elif key == arcade.key.M:
            self.input_value -= 2
        elif key == arcade.key.COMMA:
            self.input_value -= 1

    def on_update(self, delta_time):
        self.fps = round(1 / delta_time)
        self.fps_text.value = f"{self.fps} FPS"
        self.now = arrow.now()
        if self.paused:
            self.tick_text.value = f"Tick {self.tick} | PAUSED"
            return
        else:
            self.tick_text.value = f"Tick {self.tick}"

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
        self.instruction_text.value = self.cpu._current_instruction
        self.program_text.value = f"Program Counter: {self.cpu.program_counter}"
        self.input_text.value = f"Input: {self.input_value}"

    def draw_ram(self):
        SQUARE_SIZE = 8
        WIDTH = 16
        HEIGHT = self.cpu.ram.size // WIDTH
        BORDER = 4
        start_x = SCREEN_WIDTH - (SQUARE_SIZE * WIDTH + BORDER)
        start_y = SQUARE_SIZE * HEIGHT + BORDER
        for i in range(HEIGHT):
            for j in range(WIDTH):
                x = start_x + (j * SQUARE_SIZE)
                y = start_y - (i * SQUARE_SIZE)
                c = self.cpu.ram.load(i * WIDTH + j)
                color = (c, c, c, 255)
                arcade.draw_lrtb_rectangle_filled(x, x + SQUARE_SIZE, y, y - SQUARE_SIZE, color)

    def on_draw(self):
        arcade.start_render()
        self.sprite_list.draw()
        self.fps_text.draw()
        self.rate_text.draw()
        self.tick_text.draw()
        self.instruction_text.draw()
        self.program_text.draw()
        self.input_text.draw()
        self.draw_ram()


def main():
    window = GameWindow(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    window.setup()
    arcade.run()

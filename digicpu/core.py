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

        self.paused = False

        # Init the parent class
        super().__init__(width, height, title, update_rate = 1 / 240)

    def setup(self):
        self.sprite_list = arcade.SpriteList()
        self.cpu = CPU()
        t = pkg_resources.read_text(digicpu.data, "program.asm")
        self.cpu.load_string(t)
        self.output_display = SevenSegmentDisplay()
        self.digits = []

        self.fps_text = arcade.Text(f"{self.fps} FPS", 5, 5)
        self.rate_text = arcade.Text(f"Tick Rate 1:{self.tick_multiplier}", 5, 25)
        self.tick_text = arcade.Text(f"Tick {self.tick} | PAUSED", 5, 45)
        self.instruction_text = arcade.Text(f"NOP", 5, SCREEN_HEIGHT - 5, font_size = 24, anchor_y = "top")
        self.program_text = arcade.Text(f"Program Counter: 0", 5, SCREEN_HEIGHT - 45, font_size = 24, anchor_y = "top")

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

    def on_key_release(self, key, modifiers):
        pass

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
            if self.cpu.program_counter < 254:
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
        self.program_text.value = str(self.cpu.program_counter)

    def on_draw(self):
        arcade.start_render()
        self.sprite_list.draw()
        self.fps_text.draw()
        self.rate_text.draw()
        self.tick_text.draw()
        self.instruction_text.draw()
        self.program_text.draw()

def main():
    window = GameWindow(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    window.setup()
    arcade.run()

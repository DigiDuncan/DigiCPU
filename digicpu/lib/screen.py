import arcade
from arcade.types import Color

def packed_color_to_color(packed: int) -> Color:

    r = ((packed & 0b00110000) >> 4) * 64
    g = ((packed & 0b00001100) >> 2) * 64
    b = ((packed & 0b00000011) >> 0) * 64

    return Color(r, g, b, 255)

class Screen(arcade.Sprite):
    """
    A really basic screen.

    Pixel format is XXRRGGBB, where the highest two bits are reserved and unused.
    """

    cid = 0

    def __init__(self, width: int, height: int):
        self._tex = arcade.Texture.create_empty(f"screen-{self.__class__.cid}", (width, height))
        self.__class__.cid += 1

        super().__init__(self._tex)

        self._sprite_list = arcade.SpriteList()
        self._sprite_list.append(self)

        self.byte_size: int = width * height
        self.w = width
        self.h = height
        self.pixels = [0] * self.byte_size

    @property
    def current_state(self) -> tuple:
        return tuple(self.pixels)

    def clear(self):
        self.pixels = [0] * self.byte_size

    def update(self, *args, **kwargs):
        if self.current_state == self.last_state:
            return
        with self._sprite_list.atlas.render_into(self._tex) as fbo:
            fbo.clear()
            for n, px in enumerate(self.pixels):
                x = n % self.w
                y = self.h - (n // self.w)
                arcade.draw_point(x, y, packed_color_to_color(px))
        self.last_state = self.current_state
        super().update(*args, **kwargs)

    def draw(self) -> None:
        self._sprite_list.draw(pixelated = True)

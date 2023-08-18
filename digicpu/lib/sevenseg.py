import arcade


def get_segment_point_list(vertical: bool, length: int, thickness: int, x_offset = 0, y_offset = 0):
    points: list[tuple] = []
    if not vertical:
        points.append((0, thickness // 2))  # left point (0)
        points.append((thickness // 2, thickness))  # top left point (1)
        points.append((length - thickness // 2, thickness))  # top right point (2)
        points.append((length, thickness // 2))  # right point (3)
        points.append((length - thickness // 2, 0))  # bottom right point (4)
        points.append((thickness // 2, 0))  # bottom left point (5)
    else:
        points.append((thickness // 2, 0))  # bottom point (0)
        points.append((0, thickness // 2))  # bottom left point (1)
        points.append((0, length - thickness // 2))  # top left point (2)
        points.append((thickness // 2, length))  # top point (3)
        points.append((thickness, length - thickness // 2))  # top right point (4)
        points.append((thickness, thickness // 2))  # bottom right point (5)

    return [(p[0] + x_offset, p[1] + y_offset) for p in points]


class SevenSeg(arcade.Sprite):
    """
    #A#
    F B
    #G#
    E C
    #D# dot
    """

    cid = 0

    def __init__(self, width: int, thinness: float = 6.5,
                 on_color: tuple[int] = arcade.color.RED, off_color: tuple[int] = (32, 32, 32), *args, **kwargs):
        self._w = width
        self.digit_width = int(self._w * (4 / 5))
        if thinness < 2.5:
            raise ValueError("Thinness must be 2.5 or more.")
        self.segment_thickness = self.digit_width // thinness
        self.segment_gap = self.segment_thickness // 4
        self.segment_length = self.digit_width - (self.segment_gap * 2) - self.segment_thickness
        self.circle_size = (self._w - self.digit_width) // 2 + self.segment_gap
        self._h = int((self.segment_length * 2) + (self.segment_gap * 4) + self.segment_thickness)
        self._tex = arcade.Texture.create_empty(f"segment-{self.__class__.cid}", (self._w, self._h))
        self.__class__.cid += 1

        super().__init__(self._tex)

        self.off_color = off_color
        self.on_color = on_color

        self.segments = [False] * 8
        self.last_state = None

        self._sprite_list = arcade.SpriteList()
        self._sprite_list.append(self)

    @property
    def current_state(self) -> tuple:
        return tuple(self.segments) + (self.off_color, self.on_color)

    @property
    def a(self) -> bool:
        return self.segments[0]

    @a.setter
    def a(self, on: bool):
        self.segments[0] = on

    @property
    def b(self) -> bool:
        return self.segments[1]

    @b.setter
    def b(self, on: bool):
        self.segments[1] = on

    @property
    def c(self) -> bool:
        return self.segments[2]

    @c.setter
    def c(self, on: bool):
        self.segments[2] = on

    @property
    def d(self) -> bool:
        return self.segments[3]

    @d.setter
    def d(self, on: bool):
        self.segments[3] = on

    @property
    def e(self) -> bool:
        return self.segments[4]

    @e.setter
    def e(self, on: bool):
        self.segments[4] = on

    @property
    def f(self) -> bool:
        return self.segments[5]

    @f.setter
    def f(self, on: bool):
        self.segments[5] = on

    @property
    def g(self) -> bool:
        return self.segments[6]

    @g.setter
    def g(self, on: bool):
        self.segments[6] = on

    @property
    def dot(self) -> bool:
        return self.segments[7]

    @dot.setter
    def dot(self, on: bool):
        self.segments[7] = on

    def segment_color(self, segment: int):
        if segment > 7:
            return ValueError("Segment must 0-7.")
        return self.on_color if self.segments[segment] else self.off_color

    def set_bits(self, bits: int):
        """Set segment booleans in the pattern Dgfedcba."""
        for i in range(8):
            self.segments[i] = bool(bits & 0b1)
            bits = bits >> 1

    def get_bits(self) -> int:
        bits = 0
        for segment in self.segments:
            if segment:
                bits += 1
                bits = bits << 1
        return bits

    def clear(self):
        self.segments = [False] * 8

    def set_char(self, char: str | int):
        if isinstance(char, int):
            char = str(char)

        # Deal with a dot
        set_dot = False
        if char[-1] == ".":
            set_dot = True

        if len(char) > 1:
            raise ValueError("set_char() takes one character (and an optional '.') or empty string.")

        char = char.lower()

        # Set segments
        match char:
            case "0":
                self.set_bits(0b0111111)
            case "1":
                self.set_bits(0b0000110)
            case "2":
                self.set_bits(0b1011011)
            case "3":
                self.set_bits(0b1001111)
            case "4":
                self.set_bits(0b1100110)
            case "5":
                self.set_bits(0b1101101)
            case "6":
                self.set_bits(0b1111101)
            case "7":
                self.set_bits(0b0000111)
            case "8":
                self.set_bits(0b1111111)
            case "9":
                self.set_bits(0b1101111)
            case "a":
                self.set_bits(0b1110111)
            case "b":
                self.set_bits(0b1111100)
            case "c":
                self.set_bits(0b0111001)
            case "d":
                self.set_bits(0b1011110)
            case "e":
                self.set_bits(0b1111001)
            case "f":
                self.set_bits(0b1110001)
            case "-":
                self.set_bits(0b1000000)
            case "_":
                self.set_bits(0b0001000)
            case " " | "":
                self.clear()

        if set_dot:
            self.dot = True

    def update(self, *args, **kwargs):
        if self.current_state == self.last_state:
            return
        with self._sprite_list.atlas.render_into(self._tex) as fbo:
            fbo.clear()
            points_a = get_segment_point_list(False, self.segment_length, self.segment_thickness, self.segment_thickness // 2 + self.segment_gap, self.height - self.segment_thickness)
            arcade.draw_polygon_filled(points_a, self.segment_color(0))
            points_b = get_segment_point_list(True, self.segment_length, self.segment_thickness, self.digit_width - self.segment_thickness, self.height - self.segment_length - self.segment_gap - (self.segment_thickness // 2))
            arcade.draw_polygon_filled(points_b, self.segment_color(1))
            points_c = get_segment_point_list(True, self.segment_length, self.segment_thickness, self.digit_width - self.segment_thickness, self.segment_gap + (self.segment_thickness // 2))
            arcade.draw_polygon_filled(points_c, self.segment_color(2))
            points_d = get_segment_point_list(False, self.segment_length, self.segment_thickness, self.segment_thickness // 2 + self.segment_gap, 0)
            arcade.draw_polygon_filled(points_d, self.segment_color(3))
            points_e = get_segment_point_list(True, self.segment_length, self.segment_thickness, 0, self.segment_gap + (self.segment_thickness // 2))
            arcade.draw_polygon_filled(points_e, self.segment_color(4))
            points_f = get_segment_point_list(True, self.segment_length, self.segment_thickness, 0, self.height - self.segment_length - self.segment_gap - (self.segment_thickness // 2))
            arcade.draw_polygon_filled(points_f, self.segment_color(5))
            points_g = get_segment_point_list(False, self.segment_length, self.segment_thickness, self.segment_thickness // 2 + self.segment_gap, self.segment_length + (self.segment_gap * 2))
            arcade.draw_polygon_filled(points_g, self.segment_color(6))
            arcade.draw_circle_filled(self._w - self.circle_size, self.circle_size // 2, self.circle_size // 2, self.segment_color(7))
        self.last_state = self.current_state
        super().update(*args, **kwargs)

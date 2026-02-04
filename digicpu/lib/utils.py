from digicpu.lib.types import MAX_INT


def make_int(i: str | int) -> int:
    if isinstance(i, int):
        return i
    if i.startswith("0X"):
        return int(i[2:], 16)
    elif i.startswith("0B"):
        return int(i[2:], 2)
    elif i.startswith("\""):
        return ord(i[1]) % MAX_INT
    else:
        return int(i)

from findscript import Rom


def test_findscript():
    rom = Rom(b"hoyPLAYERdoy")
    start, end = rom.find("PLAYER")
    assert (start, end) == (3, 9)

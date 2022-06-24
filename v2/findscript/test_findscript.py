from findscript import Rom


def test_findscript_plain():
    rom = Rom(b"hoyPLAYERdoy")
    start, end = rom.find("PLAYER")
    assert (start, end) == (3, 9)


def test_findscript_rot4():
    rom = Rom(b"ls}TPE]IVhs}")
    start, end = rom.find("PLAYER")
    assert (start, end) == (3, 9)

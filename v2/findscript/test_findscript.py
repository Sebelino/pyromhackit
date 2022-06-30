from .findscript import Rom, load


def test_findscript_plain():
    rom = Rom(b"hoyPLAYERdoy")
    search_result = rom.find("PLAYER")
    assert search_result.start == 3
    assert search_result.end == 9
    assert search_result.offset == 0


def test_findscript_rot4():
    rom = Rom(b"ls}TPE]IVhs}")
    search_result = rom.find("PLAYER")
    assert search_result.start == 3
    assert search_result.end == 9
    assert search_result.offset == 252

#!/usr/bin/env python

import argparse
from contracts import contract
from enum import IntEnum

nes2rgb = {
    0x00: (112, 112, 112),
    0x01: (32, 24, 136),
    0x02: (0, 0, 168),
    0x03: (64, 0, 152),
    0x04: (136, 0, 112),
    0x05: (168, 0, 16),
    0x06: (160, 0, 0),
    0x07: (120, 8, 0),
    0x08: (64, 40, 0),
    0x09: (0, 64, 0),
    0x0A: (0, 80, 0),
    0x0B: (0, 56, 16),
    0x0C: (24, 56, 88),
    0x0D: (0, 0, 0),
    0x0E: (0, 0, 0),
    0x0F: (0, 0, 0),
    0x10: (184, 184, 184),
    0x11: (0, 112, 232),
    0x12: (32, 56, 232),
    0x13: (128, 0, 240),
    0x14: (184, 0, 184),
    0x15: (224, 0, 88),
    0x16: (216, 40, 0),
    0x17: (200, 72, 8),
    0x18: (136, 112, 0),
    0x19: (0, 144, 0),
    0x1A: (0, 168, 0),
    0x1B: (0, 144, 56),
    0x1C: (0, 128, 136),
    0x1D: (0, 0, 0),
    0x1E: (0, 0, 0),
    0x1F: (0, 0, 0),
    0x20: (248, 248, 248),
    0x21: (56, 184, 248),
    0x22: (88, 144, 248),
    0x23: (160, 136, 248),
    0x24: (240, 120, 248),
    0x25: (248, 112, 176),
    0x26: (248, 112, 96),
    0x27: (248, 152, 56),
    0x28: (240, 184, 56),
    0x29: (128, 208, 16),
    0x2A: (72, 216, 72),
    0x2B: (88, 248, 152),
    0x2C: (0, 232, 216),
    0x2D: (0, 0, 0),
    0x2E: (0, 0, 0),
    0x2F: (0, 0, 0),
    0x30: (248, 248, 248),
    0x31: (168, 224, 248),
    0x32: (192, 208, 248),
    0x33: (208, 200, 248),
    0x34: (248, 192, 248),
    0x35: (248, 192, 216),
    0x36: (248, 184, 176),
    0x37: (248, 216, 168),
    0x38: (248, 224, 160),
    0x39: (224, 248, 160),
    0x3A: (168, 240, 184),
    0x3B: (176, 248, 200),
    0x3C: (152, 248, 240),
    0x3D: (0, 0, 0),
    0x3E: (0, 0, 0),
    0x3F: (0, 0, 0),
}


class Strictness(IntEnum):
    lax = 0
    lenient = 1
    pragmatic = 2
    pedantic = 3
    nazi = 4


def readfile(path):
    with open(path, "rb") as f:
        contents = f.read()
        return contents


def guessformat(palette):
    if len(palette) >= 3 and palette[0:3] == "TLP":
        return "tlp"
    if len(palette) >= 4 and palette[0:4] == "RIFF":
        return "riffpal"
    raise Exception("I am too dumb to guess the format. Please use the"
                    " --outformat option if possible.")


def enumer(bytestring, step=1):
    """ bytes -> [int] where step signifies the number of bytes used to
    represent each number in the output list """
    dct = {
        1: list(bytestring),
        2: [2**8*bytestring[i]+bytestring[i+1]
            for i in range(0, len(bytestring)-1, 2)],
        3: [2**16*bytestring[i]+2**8*bytestring[i+1]+bytestring[i+2]
            for i in range(0, len(bytestring)-2, 3)]
    }
    return dct[step]


def validate_rgb24bpp(palette, strictness):
    assert len(palette) >= 3
    assert len(palette) % 3 == 0
    if strictness == Strictness.nazi:
        enumeration = enumer(palette, 3)
        duplicatemsg = "SIE PALETTE KONTAINS DUPLIKATE KOLORS, DUMKOPF!"
        assert len(enumeration) == len(set(enumeration)), duplicatemsg
        assert enumeration == sorted(enumeration), (
            "SIE PALETTE IS A MESS! SORT YOUR KOLORS, DUMKOPF! "
            "LEAST RED KOLORS IN FRONT! THEN LEAST GREEN! THEN LEAST BLUE!"
        )


def validate_bgr15bpp(palette, strictness):
        assert len(palette) >= 2
        assert len(palette) % 2 == 0
        duplicatemsg = "SIE PALETTE KONTAINS DUPLIKATE KOLORS, DUMKOPF!"
        if strictness >= Strictness.pragmatic:
            for byteindex in range(1, len(palette), 2):
                bit = (palette[byteindex] & 0x80) >> 7
                assert bit == 0
        if strictness == Strictness.nazi:
            enumeration = enumer(palette, 2)
            assert len(enumeration) == len(set(enumeration)), duplicatemsg
            assert enumeration == sorted(enumeration), (
                "SIE PALETTE IS A MESS! SORT YOUR KOLORS, DUMKOPF! LEAST BLUE"
                "KOLORS IN FRONT! THEN LEAST GREEN! THEN LEAST RED!"
            )


def validate_nes(palette, strictness):
    assert len(palette) >= 1
    if strictness >= Strictness.pragmatic:
        assert all(b in nes2rgb for b in palette)
    duplicatemsg = "SIE PALETTE KONTAINS DUPLIKATE KOLORS, DUMKOPF!"
    if strictness == Strictness.nazi:
        enumeration = enumer(palette)
        assert len(enumeration) == len(set(enumeration)), duplicatemsg
        assert enumeration == sorted(enumeration), (
            "SIE PALETTE IS A MESS! SORT YOUR KOLORS, DUMKOPF! LOW BYTE "
            "VALUES IN FRONT!"
        )


def validate_tpl(palette, strictness):
    signature = b"TPL"
    hdrsize = len(signature)+1
    fmtbyte = palette[3]
    if fmtbyte & 0b10:
        payloadfmt = "bgr15bpp"
        bytespercolor = 2
    elif fmtbyte & 0b01:
        payloadfmt = "nes"
        bytespercolor = 1
    else:
        payloadfmt = "rgb24bpp"
        bytespercolor = 3
    colorcount = 16
    assert len(palette) >= hdrsize+colorcount*bytespercolor
    payload = palette[hdrsize:hdrsize+colorcount*bytespercolor]
    validate(payload, payloadfmt, strictness)
    extrapalettes = palette[hdrsize+colorcount*bytespercolor:]
    if strictness >= Strictness.pragmatic:
        assert fmtbyte in {0, 1, 2}
    if strictness >= Strictness.pedantic:
        assert palette[0:3] == signature
        assert len(palette[4:])/bytespercolor in {16, 32, 64, 128, 256}
    if strictness == Strictness.nazi:
        assert len(extrapalettes) == 0, (
            "LEBENSRAUM! ELIMINATE SIE EXTRA PALETTES, DUMKOPF! "
            "IN TILE LAYER PRO, SET Palette -> Entries -> 16!"
        )


def validate_riffpal(palette, strictness):
    assert len(palette) >= 24+4
    signature = b"RIFF"
    datasig = b"PAL data"
    version = (3).to_bytes(2, byteorder="big")
    payload = palette[24:]
    dlength = (len(payload)+4).to_bytes(4, byteorder="little")
    flength = (len(payload)+16).to_bytes(4, byteorder="little")
    colorcount = (int(len(payload)/4)).to_bytes(2, byteorder="little")
    if strictness >= Strictness.pragmatic:
        for i in range(0, len(payload), 4):
            byteflag = payload[i+3]
            assert byteflag == 0
    elif strictness >= Strictness.pedantic:
        assert palette[0:4] == signature
        assert palette[4:8] == flength
        assert palette[8:16] == datasig
        assert palette[16:20] == dlength
        assert palette[20:22] == version
        assert palette[22:24] == colorcount


def validate_rgb24bpphex(palette, strictness):
    hexes = palette.split()
    assert len(hexes) >= 3
    assert len(hexes) % 3 == 0
    if strictness >= Strictness.pragmatic:
        for h in hexes:
            assert 0 <= int(h, 16) <= 255
    if strictness == Strictness.nazi:
        assert b'x' not in palette.lower(), (
            "'0xFF' SHOULD BE 'FF', DUMKOPF!"
        )
        assert palette == palette.upper(), (
            "MAKE IT '1E'! NOT '1e', DUMKOPF!"
        )
        for i in range(2, len(palette), 3):
            assert palette[i:i+1] == b" ", (
                "SIE SEPARATOR SHOULD BE A SINGLE SPACE KARAKTER! "
                "NOZING ELSE, DUMKOPF!"
            )
        enumeration = enumer(palette, 3)
        duplicatemsg = "SIE PALETTE KONTAINS DUPLIKATE KOLORS, DUMKOPF!"
        assert len(enumeration) == len(set(enumeration)), duplicatemsg
        assert enumeration == sorted(enumeration), (
            "SIE PALETTE IS A MESS! SORT YOUR KOLORS, DUMKOPF! LEAST RED "
            "KOLORS IN FRONT! THEN LEAST GREEN! THEN LEAST BLUE!"
        )


@contract(palette=bytes, fmt=str, strictness=Strictness)
def validate(palette, fmt, strictness):
    """
    Validates the palette of the given format with the given level of
    strictness. Raises an exception if it does not meet up to the standards.
    """
    if strictness == Strictness.lax:
        return
    validationmap = {
        "rgb24bpp": validate_rgb24bpp,
        "bgr15bpp": validate_bgr15bpp,
        "nes": validate_nes,
        "tpl": validate_tpl,
        "riffpal": validate_riffpal,
        "rgb24bpphex": validate_rgb24bpphex,
    }
    validator = validationmap[fmt]
    validator(palette, strictness)


def rgb24bpp2rgb24bpphex(palette):
    """ b'abc' -> b'61 62 63' """
    hexes = ["{:02x}".format(b).upper().encode("utf8") for b in palette]
    return b" ".join(hexes)


def format2rgb24bpp(palette, fmt):
    """ Changes the format of the fmt-formatted input into RGB 24 BPP. """
    if fmt == "rgb24bpp":
        return palette
    if fmt == "rgb24bpphex":
        return bytes(int(h, 16) for h in palette.split())
    if fmt == "bgr15bpp":
        newpalette = b""
        for i in range(0, len(palette), 2):
            blue = palette[i+1] >> 2
            green = ((palette[i+1] & 0b11) << 3) | (palette[i] >> 5)
            red = palette[i] & 0b00011111
            # Scale values
            blue = 8*blue
            green = 8*green
            red = 8*red
            color = bytes([red, green, blue])
            newpalette = newpalette+color
        return newpalette
    if fmt == "riffpal":
        raise NotImplementedError
    if fmt == "tpl":
        # TPL = Tile Layer Palette. Curiously, the extension is TPL, not TLP.
        payloadfmt = palette[3]
        if payloadfmt == 0:
            return palette[4:]
        if payloadfmt == 1:
            return b"".join(bytes(nes2rgb(b)) for b in palette[4:])
        if payloadfmt == 2:
            return format2rgb24bpp(palette[4:], "bgr15bpp")
        else:
            raise NotImplementedError
    raise ValueError("Unrecognized format: {}".format(fmt))


def rgb24bpp2format(palette, fmt):
    """ Changes the format of the RGB 24 BPP formatted input into fmt. """
    if fmt == "rgb24bpp":
        return palette
    if fmt == "rgb24bpphex":
        return rgb24bpp2rgb24bpphex(palette)
    if fmt == "bgr15bpp":
        newpalette = b""
        for i in range(0, len(palette), 3):
            r = (palette[i] & 0b11111000) >> 3
            g = (palette[i+1] & 0b11111000) << 5-3
            b = (palette[i+2] & 0b11111000) << 10-3
            colornum = b | g | r
            newpalette = newpalette+colornum.to_bytes(2, byteorder='little')
        return newpalette
    if fmt == "tpl":  # TODO Distinguish TPL bgr15bpp from other subformats
        return b"TPL\x02"+rgb24bpp2format(palette, "bgr15bpp")
    if fmt == "riffpal":
        raise NotImplementedError
    raise ValueError("Unrecognized format: {}".format(fmt))


def formatconvert(path, informat=None, outformat=None, outfile=None,
                  strictness=Strictness.pedantic):
    print("Attempting to read file...")
    contents = readfile(path)
    infmt = informat
    if not informat:
        print("Attempting to guess format...")
        infmt = guessformat(contents)
        print("Looks {}-formatted to me.".format(infmt))
    print("Validating input...")
    validate(contents, infmt, strictness)
    if outformat and informat != outformat:
        print("Attempting to change format into standard RGB 24 BPP...")
        contents = format2rgb24bpp(contents, infmt)
        print("Attempting to change format into {}...".format(outformat))
        contents = rgb24bpp2format(contents, outformat)
    if outfile:
        print("Attempting to write output to file...")
        with open(outfile, "wb") as f:
            f.write(contents)
    else:
        print("Printing output...")
        hexstr = rgb24bpp2rgb24bpphex(contents)
        print(hexstr.decode("latin1"))

if __name__ == "__main__":
    descr = """
Converts a palette file of one format to another.
    """.strip()
    outputformats = ["rgb24bpp", "bgr15bpp", "riffpal", "rgb24bpphex"]
    inputformats = outputformats+["tlp"]
    parser = argparse.ArgumentParser(description=descr)
    parser.add_argument("path", help="Path to the file storing the palette.")
    parser.add_argument("--informat", "-a", choices=inputformats,
                        help="Format of the input file. If left unspecified, "
                        "the program will attempt to guess the format.")
    parser.add_argument("--outformat", "-b", choices=outputformats,
                        help="Format of the output file. If left unspecified, "
                        "the format does not change.")
    parser.add_argument("--outfile", "-o", help="Path to the file to be "
                        "created. If unspecified, print each byte to the "
                        "console as space-separated hex.")
    parser.add_argument("--strictness", "-s", default="pedantic",
                        choices=["lax", "lenient", "pragmatic", "pedantic",
                                 "nazi"],
                        help="Level of strictness when validating the input.")
    """
    The strictness levels are totally ordered, so all validity checks associated
    with level X are included in level X+1, where
    lax < lenient < pragmatic < pedantic < nazi.
    lax: Never raise an exception, regardless of how little the input complies
    to the format. This assumes that the file exists and is readable.
    Like that conspiracist who expects to find Illuminati references in anything
    he reads, even in a blank page.
    lenient: Read the minimum amount of bits needed, but complain if reading
    fails because of missing data.
    Like that lazy student who attempts to copypaste the top paragraph of what
    he assumes to be a Wikipedia article into his essay, only to find out the
    article is empty.
    pragmatic: Read and validate the minimum amount of bytes needed.
    Like that unskeptical student who reads the conclusion of a paper and deems
    it to make sense without reading the full paper.
    pedantic: Validate all data. In case the specification for a format can be
    interpreted in several ways, complain only if there is no interpretation
    under which the input is considered valid.
    Like that British peer reviewer who reads a full paper written in American
    English and does not consider there to be anything wrong with that.
    nazi: Complain if the input does not comply to one certain interpretation of
    the format specification, or if the input differs from the "canonical" way
    of representing the palette.
    Like that British grammar nazi who reprimands you for spelling "fuelling"
    with one L.
    """
    """
    bgr15bpp: Bytestring containing the palette in the form b"XYXYXY...XY"
    where each XY in binary is gggrrrrr0bbbbbgg.
    rgb24bpp: Bytestring containing the palette in the form
    b"RRGGBBRRGGBB...RRGGBB"
    where 0 <= x <= 255 for each x in {R, G, B}.
    """
    args = parser.parse_args()

    formatconvert(args.path, args.informat, args.outformat, args.outfile,
                  args.strictness)

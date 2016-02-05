#!/usr/bin/env python

import argparse
import os.path

def readfile(path):
    with open(path, "rb") as f:
        contents = f.read()
        return contents
    
def guessformat(palette):
    if len(palette) >= 3 and palette[0:3] == "TLP":
        return "tlp"
    if len(palette) >= 4 and palette[0:4] == "RIFF":
        return "riffpal"
    raise Exception("I was too dumb to guess the format. Please use the --outformat option if you can.")
    
def validate(palette, fmt, strictness):
    """
    Validates the palette of the given format with the given level of strictness.
    Raises an exception if it does not meet up to the standards.
    """
    # Regardless of strictness, the types should be what you'd expect.
    assert isinstance(palette, bytes), "palette is not a bytestring!"
    assert isinstance(fmt, str), "fmt is not a string!"
    assert isinstance(strictness, str), "strictness is not a string!"
    lax = strictness == "lax"
    lenient = strictness == "lenient"
    pragmatic = strictness == "pragmatic"
    pedantic = strictness == "pedantic"
    nazi = strictness == "nazi"
    if lax:
        return
    if fmt == "rgb24bpp":
        assert len(palette) >= 3
        assert len(palette) % 3 == 0
    elif fmt == "bgr15bpp":
        assert len(palette) >= 2
        assert len(palette) % 2 == 0
        if pedantic or nazi:
            for bitindex in range(0, 8*len(palette), 5):
                byteindex = int(bitindex/8)
                bit = palette[byteindex] & (0x80 >> (bitindex % 8))
                assert bit == 0
    elif fmt == "tlp":  # TODO: BGR 15 BPP is not the only TLP payload format
        signature = b"TLP"
        flag = b"\x02"
        hdrsize = len(signature+flag)
        colorcount = 16
        bytespercolor = 2
        payload = pattern[hdrsize:hdrsize+colorcount*bytespercolor]
        payloadfmt = "bgr15bpp"
        validate(payload, payloadfmt, strictness)
        extracrap = palette[hdrsize+colorcount*bytespercolor:]
        if pedantic or nazi:
            assert palette[0:3] == signature
            assert palette[3:4] == flag  # Should be relaxed to checking 0=RGB, 1=NES, 2=SNES/GBC/GBA
    elif fmt == "riffpal":
        signature = b"RIFF"
        datasig = b"PAL data"
        version = (3).to_bytes(2, byteorder="big")
        payload = palette[24:]
        flength = (len(payload)-8).to_bytes(2, byteorder="little")
        dlength = (len(payload)-28).to_bytes(2, byteorder="little")
        colorcount = (int(len(payload)/4)).to_bytes(2, byteorder="little")
        if pedantic or nazi:
            for i in range(0, len(payload), 4):
                byteflag = payload[i+3]
                assert byteflag == 0
    elif fmt == "rgb24bpphex":
        hexes = palette.split()
        assert len(hexes) % 3 == 0
        if pragmatic or pedantic or nazi:
            for h in hexes:
                assert 0 <= int(h, 16) <= 255
        if nazi:
            assert b'x' not in palette.lower(), "'0xFF' SHOULD BE 'FF', DUMKOPF!"
            assert palette == palette.upper(), "MAKE IT '1E'! NOT '1e', DUMKOPF!"
            for i in range(2, len(palette), 3):
                assert palette[i:i+1] == b" ", "SIE SEPARATOR SHOULD BE A SINGLE REGULAR SPACE! NOZING ELSE, DUMKOPF!"
    
def rgb24bpp2rgb24bpphex(palette):
    """ b'abc' -> b'61 62 63' """
    hexes = [hex(b)[2:].upper().encode("utf8") for b in palette]
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
            blue = palette[i] >> 2
            green = ((palette[i] & 0b11) << 5) | (palette[i+1] >> 5)
            red = palette[i+1] & 0b00011111
            color = bytes([red, green, blue])
            newpalette = newpalette+color
        return newpalette
    if fmt == "riffpal":
        raise NotImplementedError
    if fmt == "tlp":
        raise NotImplementedError
        
def rgb24bpp2format(palette, fmt):
    """ Changes the format of the RGB 24 BPP formatted input into fmt. """
    if fmt == "rgb24bpp":
        return palette
    if fmt == "rgb24bpphex":
        return rgb24bpp2rgb24bpphex(palette)
    if fmt == "bgr15bpp":
        newpalette = b""
        for i in range(0, len(palette), 3):
            b = (palette[i] & 0b00011111) << 10
            g = (palette[i+1] & 0b00011111) << 5
            r = palette[i+2] & 0b00011111
            colornum = b | g | r
            newpalette = newpalette+colornum.to_bytes(2, byteorder='big')
        return newpalette
    if fmt == "riffpal":
        raise NotImplementedError
    
def formatconvert(path, informat=None, outformat=None, outfile=None, strictness="pedantic"):
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
    parser.add_argument("--informat", "-a", choices=inputformats, help="Format of the input file. If left unspecified, the program will attempt to guess the format.")
    parser.add_argument("--outformat", "-b", choices=outputformats, help="Format of the output file. If left unspecified, the format does not change.")
    parser.add_argument("--outfile", "-o", help="Path to the file to be created. If unspecified, print each byte to the console as space-separated hex.")
    parser.add_argument("--strictness", "-s", default="pedantic", choices=["lax", "lenient", "pedantic", "nazi"], help="Level of strictness when validating the input.")
    """
    lax: Never raise an exception, regardless of how much the input complies to the format. This assumes that the file exists and is readable.
    Like that conspiracist who expects to find Illuminati references in anything he reads.
    lenient: Read only the necessary portions of the file, but complain if reading fails.
    Like that lazy student who attempts to copypaste the top paragraph of what he assumes to be a Wikipedia article into his essay, only to find out the article is empty.
    pragmatic: Read and validate only the relevant portions of the file.
    Like that unskeptical student who reads the conclusion of a paper and deems it to make sense without reading the full paper.
    pedantic: Validate all data. In case the specification for a format can be interpreted in several ways, complain only if there is no interpretation under which the input is considered valid.
    Like that British peer reviewer who reads a full paper written in American English and does not consider there to be anything wrong with that.
    nazi: Complain about things in the input that do not agree with one certain interpretation of the format specification.
    Like that British grammar nazi who reprimands you for spelling "fuelling" with one L.
    """
    """
    bgr15bpp: Bytestring containing the palette in the form b"XYXYXY...XY"
    where each XY in binary is 0bbbbbgggggrrrrr.
    rgb24bpp: Bytestring containing the palette in the form b"RRGGBBRRGGBB...RRGGBB"
    where 0 <= x <= 255 for each x in {R, G, B}.
    """
    args = parser.parse_args()
    
    formatconvert(args.path, args.informat, args.outformat, args.outfile, args.strictness)
    
    
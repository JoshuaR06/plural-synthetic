#!/usr/bin/env python3
"""Proof-of-concept avatar image generation.

This file is named gen-avatars.py (hyphen). It is not a valid import
identifier. Load it with importlib.util.spec_from_file_location, the same
way generate.py loads gen-pluralbridge.py. Importing this module does not
write files, print, or generate an image.

The callable below returns PNG bytes or an explicit no-avatar result. It does
not read a feed, write a file, or build avatars.zip. gen-import-engine.py resolves avatar settings and calls generate_avatar.
gen-pluralbridge.py and gen-simplyplural.py write the returned bytes as
<member id>.png. gen-pluralkit.py uses the member short id as that file name
and leaves native avatar URL fields null. gen-pluralport.py stores the same
bytes as Asset data_base64 and does not write a PNG directory. This module
does not call generate.py.

Color algorithm
---------------
When no #RRGGBB override is supplied, the base color is the first three
bytes of SHA-256 over the member identifier encoded as UTF-8:

    R, G, B = SHA256(member_id.encode("utf-8")).digest()[:3]

That digest is stable across processes. Python's hash() is not used, and
neither is the clock. An explicit override replaces this color. The returned
base color is lowercase #RRGGBB.

Hatch algorithm
---------------
Crosshatch draws the base color, then a second color on both diagonal
families. A pixel is hatch when either condition is true:

    (x + y) % 8 == 0
    (x - y) % 8 == 0

The period is 8 pixels, so the diagonals stay visible at the default
64 x 64 size and at smaller non-square sizes such as 32 x 48.

The hatch color is black when the base color's relative luminance is at
least 128, and white otherwise:

    luminance = 0.2126 * R + 0.7152 * G + 0.0722 * B

Light bases therefore get a dark hatch, and dark bases get a light hatch.
The two colors are not blended.
"""
import hashlib
import struct
import zlib
from dataclasses import dataclass

DEFAULT_SIZE = 64
STYLES = ("none", "solid", "crosshatch")
HATCH_PERIOD = 8
MIME_TYPE = "image/png"
_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


@dataclass(frozen=True)
class AvatarResult:
    """Image bytes for one member, or an explicit no-avatar result.

    For style "none", png, mime_type, width, height, base_color, and sha256
    are None. For solid and crosshatch, png is the complete PNG file and
    sha256 is the hex digest of those bytes.
    """

    style: str
    png: bytes | None
    mime_type: str | None
    width: int | None
    height: int | None
    base_color: str | None
    sha256: str | None

    @property
    def has_image(self):
        """True only when this result carries PNG bytes."""
        return self.png is not None


def generate_avatar(style, member_id, width=None, height=None, color=None):
    """Build one avatar result.

    style is "none", "solid", or "crosshatch". member_id is the stable
    identifier used for the derived color. width and height default
    independently to 64. color, when given, is an explicit #RRGGBB base
    color. Invalid style, dimensions, color, or identifier raise ValueError.
    This function does not write a file or print.
    """
    style = _require_style(style)
    member_id = _require_member_id(member_id)
    resolved_width = _require_dimension("width", width)
    resolved_height = _require_dimension("height", height)
    if color is None:
        red, green, blue = _color_from_member_id(member_id)
    else:
        red, green, blue = _parse_color(color)
    if style == "none":
        return AvatarResult(style, None, None, None, None, None, None)
    base_color = _format_color(red, green, blue)
    if style == "solid":
        pixels = _solid_rows(resolved_width, resolved_height, (red, green, blue))
    else:
        pixels = _crosshatch_rows(resolved_width, resolved_height, (red, green, blue))
    png = _encode_png(resolved_width, resolved_height, pixels)
    return AvatarResult(
        style=style,
        png=png,
        mime_type=MIME_TYPE,
        width=resolved_width,
        height=resolved_height,
        base_color=base_color,
        sha256=hashlib.sha256(png).hexdigest(),
    )


def _require_style(style):
    """Reject anything other than none, solid, or crosshatch."""
    if style not in STYLES:
        raise ValueError(
            f"style must be one of {', '.join(STYLES)}; got {style!r}"
        )
    return style


def _require_member_id(member_id):
    """The derived color is SHA-256 of this UTF-8 string, so it must be a non-empty str."""
    if not isinstance(member_id, str) or member_id == "":
        raise ValueError(
            f"member_id must be a non-empty string; got {member_id!r}"
        )
    return member_id


def _require_dimension(name, value):
    """None becomes 64. A bool is rejected because bool is a subclass of int."""
    if value is None:
        return DEFAULT_SIZE
    # bool is a subclass of int; True would otherwise become a 1-pixel image.
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{name} must be a positive integer; got {value!r}")
    return value


def _parse_color(color):
    """Accept only #RRGGBB. The leading # and six hex digits are required."""
    if not isinstance(color, str) or len(color) != 7 or not color.startswith("#"):
        raise ValueError(f"color must be #RRGGBB; got {color!r}")
    hex_digits = color[1:]
    if any(digit not in "0123456789abcdefABCDEF" for digit in hex_digits):
        raise ValueError(f"color must be #RRGGBB; got {color!r}")
    return tuple(int(hex_digits[index:index + 2], 16) for index in (0, 2, 4))


def _format_color(red, green, blue):
    """Lowercase #RRGGBB for AvatarResult.base_color."""
    return f"#{red:02x}{green:02x}{blue:02x}"


def _color_from_member_id(member_id):
    """First three SHA-256 bytes of the UTF-8 member id. Not Python hash()."""
    digest = hashlib.sha256(member_id.encode("utf-8")).digest()
    return digest[0], digest[1], digest[2]


def _hatch_rgb(base):
    """Black on a light base, white on a dark base. The threshold is luminance 128."""
    red, green, blue = base
    luminance = 0.2126 * red + 0.7152 * green + 0.0722 * blue
    if luminance >= 128:
        return (0, 0, 0)
    return (255, 255, 255)


def _solid_rows(width, height, rgb):
    """Each row is a list of RGB tuples. A flat repeated tuple would be misread as bytes."""
    row = [rgb] * width
    return [list(row) for _ in range(height)]


def _crosshatch_rows(width, height, base):
    """Base color with both diagonal hatch families. See the module docstring."""
    hatch = _hatch_rgb(base)
    rows = []
    for y in range(height):
        row = []
        for x in range(width):
            if (x + y) % HATCH_PERIOD == 0 or (x - y) % HATCH_PERIOD == 0:
                row.append(hatch)
            else:
                row.append(base)
        rows.append(row)
    return rows


def _zlib_store(data):
    """RFC 1950 zlib stream of stored deflate blocks.

    zlib.compress at level 9 does not emit the same bytes on every zlib
    build. GitHub's Python 3.12 and local zlib-ng disagree, so committed
    avatar digests failed in CI while passing here. Stored blocks are
    defined by the format, and zlib.adler32 is the checksum both builds share.
    """
    header = b"\x78\x01"
    blocks = []
    if not data:
        pieces = [b""]
    else:
        pieces = [data[start:start + 65535] for start in range(0, len(data), 65535)]
    for index, piece in enumerate(pieces):
        final = 1 if index == len(pieces) - 1 else 0
        blocks.append(bytes((final,)) + struct.pack("<HH", len(piece), len(piece) ^ 0xFFFF) + piece)
    checksum = zlib.adler32(data) & 0xFFFFFFFF
    return header + b"".join(blocks) + struct.pack(">I", checksum)


def _encode_png(width, height, rows):
    """Truecolor PNG. Each row is stored with filter byte 0, matching generate.png's layout.

    The IDAT payload is a stored zlib stream, so the file bytes do not follow
    the host zlib compressor. generate.png still uses zlib.compress for Aurora.
    """
    raw = b"".join(b"\x00" + b"".join(bytes(pixel) for pixel in row) for row in rows)
    compressed = _zlib_store(raw)
    if zlib.decompress(compressed) != raw:
        raise RuntimeError("stored zlib stream did not round-trip")
    return (
        _PNG_SIGNATURE
        + _chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + _chunk(b"IDAT", compressed)
        + _chunk(b"IEND", b"")
    )


def _chunk(tag, data):
    """One PNG chunk. The CRC covers the tag and the data, not the length."""
    body = tag + data
    checksum = zlib.crc32(body) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + body + struct.pack(">I", checksum)

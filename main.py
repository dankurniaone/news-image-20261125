#!/usr/bin/env python3
"""Copy the finished broadsheet to the grader's output location.

The finished image lives in this repository as entry.png (a 680x1024 PNG
drawn from real file photos and the verified news text). This program does
nothing creative: it checks the image is exactly the file it expects, then
writes those same bytes to /output/entry.png (or to the directory named by
MAKEFUN_OUTPUT_DIR when that is set). Standard library only, no network,
no randomness, no timestamps, so every run produces byte-identical output.
"""

import os
import struct
import sys
import zlib

SOURCE_FILENAME = "entry.png"
OUTPUT_FILENAME = "entry.png"

EXPECTED_WIDTH = 680
EXPECTED_HEIGHT = 1024
EXPECTED_BYTE_COUNT = 619559
MAX_BYTE_COUNT = 1048576

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
IHDR_LENGTH = 13


def die(message):
    """Report a validation failure and stop without writing anything."""
    print("main.py: refusing to write output: " + message, file=sys.stderr)
    raise SystemExit(1)


def repo_root():
    """The directory this program lives in, i.e. the repository root."""
    return os.path.dirname(os.path.abspath(__file__))


def output_directory():
    """Where the grader expects the finished image.

    MAKEFUN_OUTPUT_DIR wins when it is set to a non-empty value; otherwise
    the grader's default /output is used.
    """
    override = os.environ.get("MAKEFUN_OUTPUT_DIR", "")
    if override.strip():
        return override
    return "/output"


def read_source_bytes(path):
    """Read the source image, failing loudly if it is missing."""
    try:
        with open(path, "rb") as handle:
            return handle.read()
    except FileNotFoundError:
        die("source image not found at " + path)
    except OSError as exc:
        die("could not read source image at " + path + ": " + str(exc))


def check_png_structure(data):
    """Walk the PNG chunk by chunk, verifying sizes and CRCs.

    Returns the (width, height) from the IHDR chunk. Anything malformed,
    truncated, or carrying a bad checksum is rejected before a single byte
    is written to the output.
    """
    if len(data) < 8 or data[:8] != PNG_MAGIC:
        die("source is not a PNG file (bad magic bytes)")
    if len(data) < 8 + 8 + IHDR_LENGTH + 4:
        die("source PNG is truncated before its IHDR chunk")

    offset = 8
    seen_ihdr = False
    seen_iend = False
    width = 0
    height = 0

    while offset + 8 <= len(data):
        chunk_length = struct.unpack(">I", data[offset:offset + 4])[0]
        chunk_type = data[offset + 4:offset + 8]
        if offset == 8 and chunk_type != b"IHDR":
            die("first chunk of source PNG is not IHDR")
        body_start = offset + 8
        body_end = body_start + chunk_length
        if body_end + 4 > len(data):
            die("source PNG is truncated inside chunk " + chunk_type.decode("latin-1", "replace"))
        body = data[body_start:body_end]
        stored_crc = struct.unpack(">I", data[body_end:body_end + 4])[0]
        actual_crc = zlib.crc32(chunk_type + body) & 0xFFFFFFFF
        if stored_crc != actual_crc:
            die("source PNG chunk " + chunk_type.decode("latin-1", "replace") + " has a bad CRC")

        if chunk_type == b"IHDR":
            if seen_ihdr:
                die("source PNG has more than one IHDR chunk")
            if chunk_length != IHDR_LENGTH:
                die("source PNG IHDR chunk has the wrong length")
            width, height = struct.unpack(">II", body[:8])
            seen_ihdr = True
        elif chunk_type == b"IEND":
            if chunk_length != 0:
                die("source PNG IEND chunk should be empty")
            seen_iend = True
            if body_end + 4 != len(data):
                die("source PNG has trailing bytes after IEND")
            break
        offset = body_end + 4

    if not seen_ihdr:
        die("source PNG has no IHDR chunk")
    if not seen_iend:
        die("source PNG has no IEND chunk")
    return width, height


def validate_source(data):
    """Check the source image is the exact file this entry ships."""
    if len(data) != EXPECTED_BYTE_COUNT:
        die(
            "source image is "
            + str(len(data))
            + " bytes, expected "
            + str(EXPECTED_BYTE_COUNT)
        )
    if len(data) > MAX_BYTE_COUNT:
        die("source image exceeds the 1 MiB limit")
    width, height = check_png_structure(data)
    if width != EXPECTED_WIDTH or height != EXPECTED_HEIGHT:
        die(
            "source image is "
            + str(width)
            + "x"
            + str(height)
            + ", expected "
            + str(EXPECTED_WIDTH)
            + "x"
            + str(EXPECTED_HEIGHT)
        )


def write_output(data, path):
    """Write the bytes, then read them back and confirm they match."""
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as handle:
            handle.write(data)
    except OSError as exc:
        die("could not write output to " + path + ": " + str(exc))
    try:
        with open(path, "rb") as handle:
            written = handle.read()
    except OSError as exc:
        die("could not read back output at " + path + ": " + str(exc))
    if written != data:
        die("output at " + path + " does not match the source bytes")


def main():
    source_path = os.path.join(repo_root(), SOURCE_FILENAME)
    data = read_source_bytes(source_path)
    validate_source(data)
    destination = os.path.join(output_directory(), OUTPUT_FILENAME)
    write_output(data, destination)
    print(
        "wrote "
        + str(len(data))
        + " bytes to "
        + destination
    )


if __name__ == "__main__":
    main()

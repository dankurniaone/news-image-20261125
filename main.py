"""Copy the finished 25 November broadsheet to the grader's output.

The entry image is built ahead of time by tools/render.py and shipped in
this repository as entry.png. This program only checks that the image
meets the competition's limits (a whole PNG, 680x1024, at most 1 MiB)
and copies it to /output/entry.png (or $MAKEFUN_OUTPUT_DIR when set),
then reads the copy back and compares it byte for byte with the source,
so a short or corrupted write cannot slip through. Nothing is fetched
and nothing varies between runs, so two runs write identical bytes.
"""
import hashlib
import os
import shutil
import struct
import sys
from pathlib import Path

HERE = Path(__file__).parent
SOURCE = HERE / "entry.png"
LIMIT_BYTES = 1_048_576
SIZE_W, SIZE_H = 680, 1024


def fail(reason):
    sys.exit(f"entry.png rejected: {reason}")


def main():
    raw = SOURCE.read_bytes()

    if len(raw) > LIMIT_BYTES:
        fail(f"{len(raw)} bytes exceeds the {LIMIT_BYTES} cap")
    if raw[:8] != bytes([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A]):
        fail("missing PNG signature")
    if raw[12:16] != b"IHDR":
        fail("missing IHDR chunk")
    width, height = struct.unpack(">II", raw[16:24])
    if (width, height) != (SIZE_W, SIZE_H):
        fail(f"dimensions are {width}x{height}, expected {SIZE_W}x{SIZE_H}")
    if raw[-12:-8] != b"\x00\x00\x00\x00" or raw[-8:-4] != b"IEND":
        fail("file does not end with an IEND chunk")

    target_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / "entry.png"
    shutil.copyfile(SOURCE, target)

    blob = target.read_bytes()
    if blob != raw:
        fail("copy differs from entry.png")
    print(f"wrote {target} ({width}x{height}, {len(blob)} bytes, "
          f"sha256 {hashlib.sha256(raw).hexdigest()})")


if __name__ == "__main__":
    main()

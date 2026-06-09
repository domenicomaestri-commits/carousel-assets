#!/usr/bin/env python3
"""Tolerant golden-master comparison.

Compares freshly rendered slides against the frozen reference. Allows tiny
anti-aliasing differences (font rasterization varies across FreeType versions,
e.g. Mac vs cloud) but fails on any real layout/text/colour regression, which
changes large contiguous areas.

Exit 0 = green (match within tolerance), exit 1 = red (regression).
"""
import sys
from pathlib import Path

try:
    from PIL import Image, ImageChops
except ImportError:
    import subprocess
    for args in (["--quiet", "Pillow>=10"],
                 ["--quiet", "--user", "Pillow>=10"],
                 ["--quiet", "--break-system-packages", "Pillow>=10"]):
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", *args])
            break
        except subprocess.CalledProcessError:
            continue
    from PIL import Image, ImageChops

CHANNEL_THRESH = 50      # per-pixel luminance-diff considered "real"
MAX_FRAC       = 0.0030  # max fraction of pixels allowed to differ that much

def main():
    rendered_dir = Path(sys.argv[1])
    ref_dir = Path(sys.argv[2])
    refs = sorted(ref_dir.glob("slide-*.png"))
    if not refs:
        print("no reference images found", file=sys.stderr); return 1
    ok = True
    for ref in refs:
        name = ref.name
        cand = rendered_dir / name
        if not cand.exists():
            print(f"RED  {name}: missing rendered output"); ok = False; continue
        a = Image.open(ref).convert("RGB")
        b = Image.open(cand).convert("RGB")
        if a.size != b.size:
            print(f"RED  {name}: size {b.size} != reference {a.size}"); ok = False; continue
        diff = ImageChops.difference(a, b).convert("L")
        mask = diff.point(lambda p: 255 if p > CHANNEL_THRESH else 0)
        above = mask.histogram()[255]
        frac = above / (a.width * a.height)
        if frac > MAX_FRAC:
            print(f"RED  {name}: {frac*100:.3f}% pixels differ (> {MAX_FRAC*100:.3f}%)")
            ok = False
        else:
            tag = "exact" if above == 0 else f"{frac*100:.4f}% AA"
            print(f"OK   {name}: {tag}")
    print("RESULT:", "GREEN" if ok else "RED")
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())

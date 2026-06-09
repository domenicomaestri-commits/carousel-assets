#!/usr/bin/env python3
"""Data-driven carousel renderer for the "≠" songwriting posts.

Usage:  python3 render.py <spec.json> [--out DIR]

Design note (do not "tidy"): the render_* functions keep the EXACT block
layout / numeric constants of the original hand-tuned script. Only the text
copy comes from the JSON spec. This is what keeps output identical to the
committed reference (see ../tests + .claude/verify.sh).
"""
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:  # self-bootstrap so it runs on a bare machine (Mac or cloud)
    import subprocess
    for args in (["--quiet", "Pillow>=10"],
                 ["--quiet", "--user", "Pillow>=10"],
                 ["--quiet", "--break-system-packages", "Pillow>=10"]):
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", *args])
            break
        except subprocess.CalledProcessError:
            continue
    from PIL import Image, ImageDraw, ImageFont

SKILL_DIR = Path(__file__).resolve().parent
FONT = str(SKILL_DIR / "assets" / "Inter.ttf")
S = 2                      # render at 2x -> 2160x2700
W, H = 1080 * S, 1350 * S

BG    = (28, 18, 8)
WHITE = (255, 255, 255)
GOLD  = (196, 150, 78)
PILL  = (201, 160, 90)
BODY  = (221, 219, 218)
MUTE  = (150, 146, 140)
WM    = (43, 31, 18)       # faint watermark number
MARGIN = 84 * S

_cache = {}
def F(size, weight, opsz=32):
    size = int(size * S)
    key = (size, weight, opsz)
    if key not in _cache:
        f = ImageFont.truetype(FONT, size)
        f.set_variation_by_axes([opsz, weight])
        _cache[key] = f
    return _cache[key]

# weight aliases
def reg(s):  return F(s, 400, 16)
def med(s):  return F(s, 500, 16)
def semi(s): return F(s, 600, 16)
def bold(s): return F(s, 700, 16)
def black(s):return F(s, 900, 32)

COLORS  = {"BG": BG, "WHITE": WHITE, "GOLD": GOLD, "PILL": PILL,
           "BODY": BODY, "MUTE": MUTE, "WM": WM}
WEIGHTS = {"reg": reg, "med": med, "semi": semi, "bold": bold, "black": black}

def runs_from(spec_runs, default_size):
    """Convert JSON run objects -> (text, font, color) tuples for draw_center_line."""
    out = []
    for r in spec_runs:
        w = r.get("w", "reg")
        size = r.get("size", default_size)
        c = r.get("c", "BODY")
        out.append((r["t"], WEIGHTS[w](size), COLORS[c]))
    return out

def line_w(runs):
    return sum(f.getlength(t) for t, f, c in runs)

def draw_center_line(d, cy, y, runs):
    x = cy - line_w(runs) / 2
    for t, f, c in runs:
        d.text((x, y), t, font=f, fill=c, anchor="lm")
        x += f.getlength(t)

def draw_tracked(d, cx, y, text, font, color, tracking):
    tracking *= S
    total = sum(font.getlength(ch) for ch in text) + tracking * (len(text) - 1)
    x = cx - total / 2
    for ch in text:
        d.text((x, y), ch, font=font, fill=color, anchor="lm")
        x += font.getlength(ch) + tracking

def chrome(d, page, total):
    draw_tracked(d, 0, 0, "", F(15, 600, 14), MUTE, 0)  # noop keeps cache warm
    d.text((MARGIN, 88 * S), f"{page:02d} / {total:02d}", font=F(15, 600, 14),
           fill=MUTE, anchor="lm")
    d.text((W - MARGIN, 88 * S), "≠", font=F(34, 600, 32), fill=WHITE, anchor="rm")

def watermark(d, num):
    d.text((W - 30 * S, H - 20 * S), num, font=black(300), fill=WM, anchor="rs")

def stack(d, blocks, cy_center):
    total = sum(p["h"] for _, p in blocks)
    y = cy_center - total / 2
    cx = W / 2
    for kind, payload in blocks:
        h = payload["h"]
        if kind == "label":
            draw_tracked(d, cx, y + h / 2, payload["text"], payload["font"],
                         payload["color"], payload["track"])
        elif kind == "lines":
            n = len(payload["lines"])
            lh = payload["lh"]
            top = y + (h - lh * n) / 2
            for i, runs in enumerate(payload["lines"]):
                draw_center_line(d, cx, top + lh * i + lh / 2, runs)
        elif kind == "pill":
            payload["fn"](d, y + h / 2)
        y += h

def label_block(text, size=15, color=MUTE, track=4.5, pad=0):
    f = F(size, 700, 14)
    return ("label", {"text": text, "font": f, "color": color,
                      "track": track, "h": size * S * 1.0 + pad * S})

def lines_block(lines, size, weight="black", color=WHITE, lh_mult=1.06, opsz=32):
    fmap = {"black": lambda s: F(s, 900, opsz), "bold": bold, "semi": semi,
            "med": med, "reg": reg}
    norm = []
    for ln in lines:
        if isinstance(ln, str):
            norm.append([(ln, fmap[weight](size), color)])
        else:
            norm.append(ln)
    lh = size * S * lh_mult
    return ("lines", {"lines": norm, "lh": lh, "h": lh * len(norm)})

def gap(px):
    return ("gap", {"h": px * S})

def new_canvas():
    img = Image.new("RGB", (W, H), BG)
    return img, ImageDraw.Draw(img)

# =================== SLIDE RENDERERS (minimal-diff from original) ===========
def render_cover(slide, page, total, out):
    img, d = new_canvas(); chrome(d, page, total)
    ts = slide.get("title_size", 64)
    blocks = [
        label_block(slide["label"], track=5),
        gap(26),
        lines_block(slide["title_white"], size=ts, weight="black", color=WHITE, lh_mult=1.04),
        gap(14),
        lines_block(slide["title_gold"], size=ts, weight="black", color=GOLD, lh_mult=1.04),
    ]
    stack(d, blocks, H * slide.get("cy", 0.5))
    img.save(out)

def render_content(slide, page, total, out):
    img, d = new_canvas(); chrome(d, page, total)
    watermark(d, f"{page:02d}")
    bsize = slide.get("body_size", 23)
    body = [ln if isinstance(ln, str) else runs_from(ln, bsize) for ln in slide["body"]]
    blocks = [
        label_block(slide["label"], size=13, track=4),
        gap(20),
        lines_block(slide["title"], size=slide.get("title_size", 40), weight="black",
                    color=WHITE, lh_mult=1.04),
        gap(34),
        lines_block(body, size=bsize, weight="reg", color=BODY, lh_mult=1.34),
    ]
    stack(d, blocks, H * slide.get("cy", 0.42))
    img.save(out)

def render_cta(slide, page, total, out):
    img, d = new_canvas(); chrome(d, page, total)
    pill_text = slide.get("pill_text", "Link in bio  ↓")
    def pill(d, cy):
        f = bold(22)
        tw = f.getlength(pill_text)
        pw, ph = tw + 80 * S, 64 * S
        x0 = W / 2 - pw / 2; y0 = cy - ph / 2
        d.rounded_rectangle([x0, y0, x0 + pw, y0 + ph], radius=ph / 2, fill=PILL)
        d.text((W / 2, cy), pill_text, font=f, fill=BG, anchor="mm")
    bsize = slide.get("body_size", 27)
    body = [ln if isinstance(ln, str) else runs_from(ln, bsize) for ln in slide["body"]]
    blocks = [
        label_block(slide["label"], size=15, color=GOLD, track=5),
        gap(24),
        lines_block(slide["title"], size=slide.get("title_size", 58), weight="black",
                    color=WHITE, lh_mult=1.04),
        gap(34),
        lines_block(body, size=bsize, weight="reg", color=BODY, lh_mult=1.4),
        gap(46),
        ("pill", {"fn": pill, "h": 64 * S}),
    ]
    stack(d, blocks, H * slide.get("cy", 0.5))
    img.save(out)

RENDERERS = {"cover": render_cover, "content": render_content, "cta": render_cta}

def main():
    import argparse, json
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    spec = json.loads(Path(a.spec).read_text(encoding="utf-8"))
    out_dir = Path(a.out or spec.get("out_dir") or ".").resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    slides = spec["slides"]
    total = len(slides)
    for i, slide in enumerate(slides, start=1):
        out = out_dir / f"slide-{i:02d}.png"
        RENDERERS[slide["type"]](slide, i, total, str(out))
    print(f"done: {total} slides -> {out_dir}")

if __name__ == "__main__":
    main()

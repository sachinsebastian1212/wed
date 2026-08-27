#!/usr/bin/env python3
"""
Renders og-dinner.jpg — the portrait image WhatsApp shows when the
invitation link is shared. Edit CONFIG, then run:

    python3 make_og.py

Fonts are fetched once from the Google Fonts repo and cached in ./fonts.
"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# ------------------------------- CONFIG -------------------------------
CONFIG = {
    "eyebrow":     "AN EVENING BEFORE THE WEDDING",
    "groom":       "Sachin",
    "bride":       "Kesia",
    "invite":      ["would love your company", "at dinner"],
    "when":        ["Saturday", "12 September 2026"],

    "venue_name":  "",          # e.g. "Casino Hotel"
    "venue_lines": [],          # e.g. ["Willingdon Island", "Kochi, Kerala"]

    "note":        "Four days before we marry — 16 September 2026",
    "octaves":     2,
}
OUT_DIR = "/mnt/user-data/outputs"
W, H = 1080, 1350
# ----------------------------------------------------------------------

KEY    = (245, 239, 228)
BLK    = (11, 9, 6)
BRASS  = (201, 149, 74)
LINEN  = (241, 234, 221)
MUTED  = (156, 144, 131)
RULE   = (104, 82, 48)

BOARD_W = 300          # white keys stop here; black keys run flush to the panel
BLACK_X = 116

PANEL_L = BOARD_W + 62
PANEL_R = W - 66
PX = (PANEL_L + PANEL_R) / 2
MAXW = PANEL_R - PANEL_L

FD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
_FONT_URLS = {
    "BodoniModa.ttf":        "ofl/bodonimoda/BodoniModa%5Bopsz,wght%5D.ttf",
    "BodoniModa-Italic.ttf": "ofl/bodonimoda/BodoniModa-Italic%5Bopsz,wght%5D.ttf",
    "Jost.ttf":              "ofl/jost/Jost%5Bwght%5D.ttf",
}


def ensure_fonts():
    import urllib.request
    os.makedirs(FD, exist_ok=True)
    for name, rel in _FONT_URLS.items():
        dest = os.path.join(FD, name)
        if not os.path.exists(dest):
            print("fetching", name)
            urllib.request.urlretrieve(
                "https://raw.githubusercontent.com/google/fonts/main/" + rel, dest)


def bodoni(size, weight=400, opsz=96, italic=False):
    f = ImageFont.truetype(
        os.path.join(FD, "BodoniModa-Italic.ttf" if italic else "BodoniModa.ttf"), int(size))
    f.set_variation_by_axes([weight, opsz])
    return f


def jost(size, weight=300):
    f = ImageFont.truetype(os.path.join(FD, "Jost.ttf"), int(size))
    f.set_variation_by_axes([weight])
    return f


# ----------------------------- background -----------------------------
def background():
    """Warm light spilling from behind the keyboard, falling off to near-black."""
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    cx, cy = W * 0.22, H * 0.02
    d = np.sqrt(((x - cx) / (W * 1.42)) ** 2 + ((y - cy) / (H * 0.90)) ** 2)

    stops = [(0.00, (86, 62, 24)), (0.30, (52, 37, 16)),
             (0.58, (30, 21, 11)), (0.86, (16, 12, 7)), (1.40, (9, 7, 5))]

    img = np.zeros((H, W, 3), np.float32)
    for (t0, c0), (t1, c1) in zip(stops, stops[1:]):
        m = (d >= t0) & (d < t1)
        f = ((d - t0) / (t1 - t0))[..., None]
        img = np.where(m[..., None],
                       np.array(c0, np.float32) * (1 - f) + np.array(c1, np.float32) * f, img)
    img = np.where((d >= stops[-1][0])[..., None], np.array(stops[-1][1], np.float32), img)

    # a faint warm lift along the bottom edge
    lift = np.clip(1 - np.sqrt(((x - W * .58) / (W * .90)) ** 2 +
                               ((y - H * 1.10) / (H * .52)) ** 2), 0, 1) ** 1.8
    img += lift[..., None] * np.array([56, 41, 19], np.float32)

    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB")


# ------------------------------ keyboard ------------------------------
HAS_BLACK = {0, 1, 3, 4, 5}


def keyboard(d, octaves):
    n = octaves * 7
    step = H / n
    gap = 5
    for i in range(n):
        top = i * step
        d.rounded_rectangle([0, top + gap / 2, BOARD_W, top + step - gap / 2],
                            radius=5, fill=KEY, corners=(False, True, True, False))
    bh = step * 0.60
    for i in range(n - 1):
        if i % 7 in HAS_BLACK:
            mid = (i + 1) * step
            d.rounded_rectangle([BLACK_X, mid - bh / 2, BOARD_W, mid + bh / 2],
                                radius=4, fill=BLK, corners=(False, True, True, False))


# -------------------------------- text --------------------------------
def tracked_w(d, text, font, track):
    return sum(d.textlength(c, font=font) for c in text) + track * max(0, len(text) - 1)


def tracked(d, cy, text, font, track, fill):
    x = PX - tracked_w(d, text, font, track) / 2
    for c in text:
        d.text((x, cy), c, font=font, fill=fill, anchor="lm")
        x += d.textlength(c, font=font) + track


def fit(d, text, mk, base, track, max_w):
    size = base
    while size > base * 0.55:
        f = mk(size)
        if tracked_w(d, text, f, track) <= max_w:
            return f
        size -= 2
    return mk(size)


# ------------------------------- compose ------------------------------
def compose(d, k):
    """Rows are [height, draw_fn|None, kind, flex]."""
    C = CONFIG
    S = lambda v: max(8, v * k)
    rows = []
    add = lambda h, fn, kind="", flex=0.0: rows.append([h * k, fn, kind, flex])
    gap = lambda h, flex=1.0, kind="": rows.append([h * k, None, kind, flex])

    if C["eyebrow"]:
        f = fit(d, C["eyebrow"], lambda s: jost(s), S(25), 9 * k, MAXW)
        add(40, lambda y, f=f: tracked(d, y, C["eyebrow"], f, 9 * k, MUTED))

    fn_name = lambda t: fit(d, t, lambda s: bodoni(s, 400, 96), S(122), 0, MAXW)
    gap(54)
    add(110, lambda y: tracked(d, y, C["groom"], fn_name(C["groom"]), 0, LINEN))
    add(76, lambda y: tracked(d, y, "&", bodoni(S(58), 400, 40, italic=True), 0, BRASS))
    add(110, lambda y: tracked(d, y, C["bride"], fn_name(C["bride"]), 0, LINEN))

    gap(40)
    f_inv = bodoni(S(40), 400, 30, italic=True)
    for i, line in enumerate(C["invite"]):
        add(56, lambda y, l=line: tracked(d, y, l, f_inv, 0, (226, 219, 206)))

    gap(46)
    add(30, lambda y: d.line([(PX - 34 * k, y), (PX + 34 * k, y)], fill=(150, 116, 62), width=2))

    gap(38)
    add(46, lambda y: tracked(d, y, "WHEN", jost(S(21)), 7.5 * k, BRASS))
    for line in C["when"]:
        f = fit(d, line, lambda s: bodoni(s, 400, 48), S(46), 1 * k, MAXW)
        add(58, lambda y, l=line, f=f: tracked(d, y, l, f, 1 * k, LINEN))

    if C["venue_name"]:
        gap(52, 1.2, "box-start")
        add(56, lambda y: tracked(d, y, "WHERE", jost(S(21)), 7.5 * k, BRASS))
        f = fit(d, C["venue_name"], lambda s: bodoni(s, 500, 48), S(46), 1 * k, MAXW - 80)
        add(62, lambda y, f=f: tracked(d, y, C["venue_name"], f, 1 * k, LINEN))
        for line in C["venue_lines"]:
            f = fit(d, line, lambda s: jost(s), S(28), 4 * k, MAXW - 80)
            add(48, lambda y, l=line, f=f: tracked(d, y, l, f, 4 * k, MUTED))
        gap(28, 0.0, "box-end")

    if C["note"]:
        gap(58, 1.5)
        f = fit(d, C["note"], lambda s: jost(s), S(24), 4 * k, MAXW)
        add(34, lambda y, f=f: tracked(d, y, C["note"], f, 4 * k, MUTED))

    return rows, sum(r[0] for r in rows)


def build():
    ensure_fonts()
    img = background()
    d = ImageDraw.Draw(img)
    keyboard(d, CONFIG["octaves"])

    TOP, BOTTOM = 150, 1204        # centre-square safe area, in case WhatsApp crops

    k = 1.0
    while k > 0.66 and compose(d, k)[1] > (BOTTOM - TOP):
        k -= 0.01
    rows, total = compose(d, k)

    slack = max(0, (BOTTOM - TOP) - total)
    flex_total = sum(r[3] for r in rows)
    if flex_total:
        for r in rows:
            r[0] += slack * (r[3] / flex_total)
        total = sum(r[0] for r in rows)

    cursor = TOP + max(0, (BOTTOM - TOP - total) / 2)
    placed, box = [], [None, None]
    for h, fn, kind, _flex in rows:
        if kind == "box-start":
            box[0] = cursor + h * 0.55
        if fn:
            placed.append((cursor + h / 2, fn))
        cursor += h
        if kind == "box-end":
            box[1] = cursor

    if box[0] is not None:
        d.rectangle([PANEL_L - 8, box[0], PANEL_R + 8, box[1] or cursor],
                    outline=RULE, width=1)

    for y, fn in placed:
        fn(y)

    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, "og-dinner.jpg")
    img.save(path, "JPEG", quality=90, optimize=True)
    print(path, os.path.getsize(path) // 1024, "KB | scale", round(k, 2))
    return path


if __name__ == "__main__":
    build()

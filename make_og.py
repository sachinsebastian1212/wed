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
    "invite":      ["would love your company", "at Madhuram Veppu"],
    "when":        ["Sunday", "13 September 2026"],
    "time":        "7:00 pm",  # "" leaves the time off the image entirely

    "venue_name":  "Carmel Hall",
    "venue_lines": ["Varapuzha, Kerala"],

    "note":        "",

    "keys":        True,       # a sliver of the keyboard down the left edge
    "octaves":     2,
}
# next to index.html, which is where og:image points
OUT_DIR = os.path.dirname(os.path.abspath(__file__))
W, H = 1080, 1350
# ----------------------------------------------------------------------

# Charcoal ground, ivory type, gold kept for accents — the same palette
# index.html uses. The page states its greys as ivory at an alpha; a JPEG
# has no alpha, so the translucent ones are flattened onto the panel
# background (#252323) here and given as flat RGB.
KEY      = (244, 240, 232)     # --key
BLK      = (10, 9, 9)          # --blk
GOLD     = (201, 168, 76)      # --brass
GOLD_DIM = (158, 134, 68)      # --gold-dim, flattened
LINEN    = (244, 240, 232)     # --ivory
IVORY_72 = (186, 183, 177)     # --ivory-72, flattened
MUTED    = (130, 127, 124)     # --ivory-45, flattened
RULE     = (72, 70, 69)        # --rule, flattened

BOARD_W = 250          # white keys stop here; black keys run flush to the panel
BLACK_X = 97           # ...and start here, keeping the board's own proportion

# set in build(), since they depend on whether the keyboard is drawn
PANEL_L = PANEL_R = PX = MAXW = 0

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
    """The charcoal lift high on the page, falling away to near-black —
    the same gradient body::before draws in index.html."""
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    cx, cy = PX, H * 0.03
    d = np.sqrt(((x - cx) / (W * 1.25)) ** 2 + ((y - cy) / (H * 1.00)) ** 2)

    stops = [(0.00, (58, 56, 56)), (0.28, (46, 43, 43)),
             (0.52, (37, 35, 35)), (0.80, (26, 25, 25)), (1.25, (15, 14, 14))]

    img = np.zeros((H, W, 3), np.float32)
    for (t0, c0), (t1, c1) in zip(stops, stops[1:]):
        m = (d >= t0) & (d < t1)
        f = ((d - t0) / (t1 - t0))[..., None]
        img = np.where(m[..., None],
                       np.array(c0, np.float32) * (1 - f) + np.array(c1, np.float32) * f, img)
    img = np.where((d >= stops[-1][0])[..., None], np.array(stops[-1][1], np.float32), img)

    # the same faint gold spill the page keeps along the bottom edge
    lift = np.clip(1 - np.sqrt(((x - W * .58) / (W * .90)) ** 2 +
                               ((y - H * 1.10) / (H * .52)) ** 2), 0, 1) ** 1.8
    img += lift[..., None] * np.array([26, 22, 11], np.float32)

    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB")


# ------------------------------ keyboard ------------------------------
HAS_BLACK = {0, 1, 3, 4, 5}


def edge_shadow(img, x0, w=44, strength=0.55):
    """The keyboard casts onto the panel, the way .rack does on the page."""
    a = strength * (1 - np.arange(w, dtype=np.float32) / w) ** 2
    arr = np.asarray(img, np.float32).copy()
    arr[:, x0:x0 + w, :] *= (1 - a[None, :, None])
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")


def keyboard(d, octaves):
    n = octaves * 7
    step = H / n
    gap = 5
    # the rack's own ground, so the seams between keys read black and not
    # as whatever the page gradient happens to be doing behind them
    d.rectangle([0, 0, BOARD_W, H], fill=BLK)
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
        add(40, lambda y, f=f: tracked(d, y, C["eyebrow"], f, 9 * k, GOLD_DIM))

    fn_name = lambda t: fit(d, t, lambda s: bodoni(s, 400, 96), S(122), 0, MAXW)
    gap(54)
    add(110, lambda y: tracked(d, y, C["groom"], fn_name(C["groom"]), 0, LINEN))
    add(76, lambda y: tracked(d, y, "&", bodoni(S(58), 400, 40, italic=True), 0, IVORY_72))
    add(110, lambda y: tracked(d, y, C["bride"], fn_name(C["bride"]), 0, LINEN))

    gap(40)
    f_inv = bodoni(S(40), 400, 30, italic=True)
    for i, line in enumerate(C["invite"]):
        add(56, lambda y, l=line: tracked(d, y, l, f_inv, 0, IVORY_72))

    gap(46)
    add(30, lambda y: d.line([(PX - 34 * k, y), (PX + 34 * k, y)], fill=RULE, width=2))

    gap(38)
    add(46, lambda y: tracked(d, y, "WHEN", jost(S(21)), 7.5 * k, GOLD))
    for line in C["when"]:
        f = fit(d, line, lambda s: bodoni(s, 400, 48), S(46), 1 * k, MAXW)
        add(58, lambda y, l=line, f=f: tracked(d, y, l, f, 1 * k, LINEN))

    if C.get("time"):
        f = fit(d, C["time"], lambda s: jost(s), S(28), 4 * k, MAXW)
        add(48, lambda y, f=f: tracked(d, y, C["time"], f, 4 * k, IVORY_72))

    if C["venue_name"]:
        gap(52, 1.2, "box-start")
        add(56, lambda y: tracked(d, y, "WHERE", jost(S(21)), 7.5 * k, GOLD))
        f = fit(d, C["venue_name"], lambda s: bodoni(s, 400, 48), S(46), 1 * k, MAXW - 80)
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
    global PANEL_L, PANEL_R, PX, MAXW
    ensure_fonts()

    keys = CONFIG.get("keys", False)
    PANEL_L = (BOARD_W + 62) if keys else 92
    PANEL_R = W - (66 if keys else 92)
    PX = (PANEL_L + PANEL_R) / 2
    MAXW = PANEL_R - PANEL_L

    img = background()
    if keys:
        img = edge_shadow(img, BOARD_W)
    d = ImageDraw.Draw(img)
    if keys:
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
        # without the keyboard the panel is the full page, and a frame that
        # wide dwarfs the two short lines inside it
        half = min((PANEL_R - PANEL_L) / 2 + 8, 330)
        d.rectangle([PX - half, box[0], PX + half, box[1] or cursor],
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

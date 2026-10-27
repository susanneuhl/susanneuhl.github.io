#!/usr/bin/env python3
"""Figurines for the About page.

Reduced line figurines after costumes from Susanne Uhl's productions, drawn as
single strokes. Every stroke is its own <path>, so the page can scatter the
strokes and let them assemble while scrolling (scripts/figurines.js).

Usage (from the repo root):
    python3 tools/figurines/figurines.py            # writes images/figurines/<slug>.svg
    python3 tools/figurines/figurines.py --preview /tmp/figurines.html

Coordinates: every figurine lives in a 260 x 560 box (feet at ~y 530).
See README.md next to this file.
"""
import argparse
import math
import os

W, H = 260, 560
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT_DIR = os.path.join(REPO, "images", "figurines")

# One signature costume piece per figurine keeps its colour from the production
ACCENTS = {
    "traviata": "#d9a08a",      # rose-coloured drape / train
    "coriolan": "#e2312b",      # red clown nose
    "traum": "#c8232c",         # big red rose
    "kleiner-mann": "#4a6fc4",  # blue checked waistcoat
    "sonne": "#d4ad3a",         # golden sun halo
}


class Fig:
    def __init__(self):
        self.strokes = []  # (d, width, colour or None)
        self.accent = None  # set to a colour while drawing the signature costume piece

    def path(self, d, w=1.2):
        self.strokes.append((d.strip(), w, self.accent))

    def poly(self, pts, w=1.2, close=False):
        d = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts) + (" Z" if close else "")
        self.path(d, w)

    def ellipse(self, cx, cy, rx, ry, w=1.2, a0=0, a1=360, n=40, rot=0):
        r = math.radians(rot)
        pts = []
        for i in range(n + 1):
            t = math.radians(a0 + (a1 - a0) * i / n)
            x, y = rx * math.cos(t), ry * math.sin(t)
            pts.append((cx + x * math.cos(r) - y * math.sin(r), cy + x * math.sin(r) + y * math.cos(r)))
        self.poly(pts, w)

    def scallops(self, x0, x1, y, n, depth, w=1.0, sag=0.0):
        """A row of downward scallops from x0 to x1 (hem of a tier)."""
        step = (x1 - x0) / n
        d = f"M{x0:.1f} {y:.1f}"
        for i in range(n):
            xa = x0 + step * i
            xb = xa + step
            yy = y + sag * math.sin(math.pi * (i + 0.5) / n)
            d += f" Q{(xa + xb) / 2:.1f} {yy + depth:.1f} {xb:.1f} {y + sag * math.sin(math.pi * (i + 1) / n):.1f}"
        self.path(d, w)

    def svg(self):
        out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
               f'fill="none" stroke="#ffffff" stroke-linecap="round" stroke-linejoin="round">']
        for d, w, c in self.strokes:
            if c:
                out.append(f'<path d="{d}" stroke-width="{w}" stroke="{c}" data-accent="1"/>')
            else:
                out.append(f'<path d="{d}" stroke-width="{w}"/>')
        out.append("</svg>")
        return "\n".join(out)


# ----------------------------------------------------------------- figurines
def traviata():
    """La traviata (Staatstheater Braunschweig): off-shoulder bodice, tiered
    scalloped skirt widening to the floor, a soft drape falling to one side."""
    f = Fig()
    # head, slightly turned, hair up with curls
    f.ellipse(128, 74, 13.5, 17.5, 1.3, rot=-8)
    f.path("M116 64 C112 50 122 40 132 42 C142 44 146 54 141 64", 1.1)
    f.ellipse(126, 44, 9, 7, 0.9, rot=-10)
    f.path("M118 40 C114 32 122 26 128 30", 0.9)
    f.path("M134 36 C140 28 148 34 144 41", 0.9)
    # neck and bare shoulders
    f.path("M122 91 L121 104", 1.1)
    f.path("M135 90 L137 104", 1.1)
    f.path("M121 104 C110 107 101 110 96 118", 1.2)
    f.path("M137 104 C148 107 157 110 162 118", 1.2)
    # arms: left resting on the skirt, right bent towards the partner
    f.path("M96 118 C90 145 88 170 96 198 C100 212 108 222 116 228", 1.1)
    f.path("M162 118 C170 140 174 160 166 176 C160 186 150 190 140 188", 1.1)
    # bodice
    f.path("M104 124 Q130 138 156 124", 1.2)
    f.path("M105 125 C107 150 110 175 113 202", 1.2)
    f.path("M155 125 C153 150 150 175 147 202", 1.2)
    f.path("M113 202 Q130 210 147 202", 1.2)
    f.path("M130 136 L130 204", 0.6)
    # tiered skirt: hems widen and drop, each a scalloped edge
    tiers = [(236, 44, 5), (278, 58, 6), (326, 73, 7), (380, 88, 8), (440, 103, 9), (506, 118, 10)]
    for y, hw, n in tiers:
        f.scallops(130 - hw, 130 + hw, y, n, 9 + n * 0.6, 1.0, sag=6)
    # outline of the bell
    f.path("M113 202 C100 280 52 420 12 506", 1.2)
    f.path("M147 202 C160 280 208 420 248 506", 1.2)
    # sequin texture: short dashes on the tiers
    for y, hw, n in tiers[1:]:
        for i in range(n):
            x = 130 - hw * 0.8 + (2 * hw * 0.8) * (i + 0.5) / n
            f.path(f"M{x:.1f} {y - 22:.1f} l2.5 4", 0.6)
    # drape falling from the waist to the side (the rose-coloured train) – signature piece
    f.accent = ACCENTS["traviata"]
    f.path("M143 206 C176 270 150 360 108 430 C88 465 70 500 56 540", 1.0)
    f.path("M150 210 C190 290 170 380 128 450 C112 478 100 508 92 540", 0.8)
    f.path("M56 540 Q74 546 92 540", 0.8)
    f.accent = None
    return f


def _ruffled(f, cx, cy, r, amp, waves, phase=0.0, w=0.9, sy=1.0, a0=0, a1=360, n=120):
    pts = []
    for i in range(n + 1):
        t = math.radians(a0 + (a1 - a0) * i / n)
        rr = r + amp * math.sin(waves * t + phase)
        pts.append((cx + rr * math.cos(t), cy + rr * sy * math.sin(t)))
    f.poly(pts, w)


def _fan(f, cx, cy, r, a0, a1, pleats, w=1.0):
    """Pleated fan: zigzag rim + pleat lines towards the centre."""
    rim = []
    for k in range(pleats * 2 + 1):
        a = math.radians(a0 + (a1 - a0) * k / (pleats * 2))
        rr = r if k % 2 == 0 else r * 0.93
        rim.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    f.poly(rim, w)
    for k in range(pleats * 2 + 1):
        a = math.radians(a0 + (a1 - a0) * k / (pleats * 2))
        rr = r if k % 2 == 0 else r * 0.93
        f.path(f"M{cx + r * 0.22 * math.cos(a):.1f} {cy + r * 0.22 * math.sin(a):.1f} "
               f"L{cx + rr * math.cos(a):.1f} {cy + rr * math.sin(a):.1f}", 0.55)


def traum():
    """Das Leben ist ein Traum (Staatsschauspiel Dresden): a big pleated fan disc
    behind the head with two more at the sides, white face with a small black crown,
    a draped cowl and tunic, a large ruffled rose at the waist, black-gloved arms –
    one open to the side, one holding a rose wreath – pleated skirt with a knotted sash."""
    f = Fig()
    _fan(f, 130, 96, 76, 165, 375, 11, 1.1)
    _fan(f, 66, 128, 54, 105, 300, 8, 1.0)
    _fan(f, 194, 128, 54, -120, 75, 8, 1.0)
    # face and crown
    f.ellipse(130, 106, 13.5, 17, 1.3)
    f.path("M118 92 L119 76 L124 86 L130 72 L136 86 L141 76 L142 92", 1.0)
    f.path("M123 103 L127 103 M133 103 L137 103 M126 116 Q130 119 134 116", 0.7)
    # cowl scarf in soft folds
    f.path("M114 124 C120 134 140 134 146 124", 1.1)
    f.path("M108 130 C116 148 144 148 152 130", 1.0)
    f.path("M102 140 C114 162 146 162 158 140", 0.9)
    # tunic with diagonal drape
    f.path("M102 140 C94 146 90 152 88 164", 1.2)
    f.path("M158 140 C166 146 170 152 172 164", 1.2)
    f.path("M90 164 C90 230 92 290 96 340", 1.2)
    f.path("M170 164 C170 230 168 290 164 340", 1.2)
    f.path("M100 176 C120 200 140 214 160 250", 0.6)
    f.path("M98 196 C116 222 128 236 140 262", 0.6)
    # the rose: ruffled rings + a small spiral heart – signature piece
    f.accent = ACCENTS["traum"]
    _ruffled(f, 130, 270, 46, 4.5, 9, 0.0, 1.1, 0.92)
    _ruffled(f, 130, 270, 33, 3.5, 7, 1.0, 0.9, 0.92)
    _ruffled(f, 130, 270, 21, 2.5, 5, 2.0, 0.8, 0.92)
    pts = [(130 + (2 + 9 * i / 60) * math.cos(i / 60 * 4 * math.pi),
            270 + (2 + 9 * i / 60) * 0.92 * math.sin(i / 60 * 4 * math.pi)) for i in range(61)]
    f.poly(pts, 0.8)
    f.accent = None
    # sash knot and pleated skirt
    f.path("M94 340 C116 350 144 350 166 338", 1.0)
    f.ellipse(126, 352, 8, 5.5, 0.9, rot=-20)
    f.path("M121 357 C116 384 120 404 112 434", 0.8)
    f.path("M130 357 C134 386 132 410 140 438", 0.8)
    f.path("M96 340 C92 400 88 470 84 528", 1.2)
    f.path("M164 340 C168 400 172 470 176 528", 1.2)
    f.path("M84 528 Q130 538 176 528", 1.1)
    for k in range(1, 8):
        x = 96 + 68 * k / 8
        f.path(f"M{x:.1f} 362 L{x + (x - 130) * 0.14:.1f} 526", 0.5)
    # left arm open to the side, gloved hand raised
    f.path("M90 166 C74 154 58 140 44 126", 1.1)
    f.path("M92 184 C76 172 60 156 48 140", 1.0)
    f.path("M44 126 L36 110 M46 128 L38 114 M48 132 L42 118 M48 138 L40 136", 0.8)
    # right arm down, holding a rose wreath
    f.path("M170 166 C184 196 194 224 198 262", 1.1)
    f.path("M168 186 C178 212 184 236 186 266", 1.0)
    _ruffled(f, 212, 300, 26, 3, 10, 0.5, 1.0)
    _ruffled(f, 212, 300, 13, 2, 7, 1.5, 0.8)
    f.path("M210 326 C214 350 206 370 212 396", 0.8)
    return f


def coriolan():
    """Coriolan (Düsseldorfer Schauspielhaus): clown with a big pleated ruff,
    tufted hair, diamond eyes and round nose, striped shirt, suspenders, wide
    jacket, white gloves, baggy trousers and long shoes."""
    f = Fig()
    f.ellipse(130, 92, 15, 19, 1.3)
    for cx, cy in ((108, 82), (104, 94), (112, 70), (152, 82), (156, 94), (148, 70)):
        _ruffled(f, cx, cy, 7, 1.6, 6, cx * 0.1, 0.8)
    f.path("M119 90 L123 83 L127 90 L123 97 Z", 0.8)
    f.path("M133 90 L137 83 L141 90 L137 97 Z", 0.8)
    f.accent = ACCENTS["coriolan"]          # the red clown nose – signature piece
    f.ellipse(130, 101, 4.2, 4.2, 1.6)
    f.ellipse(130, 101, 2.2, 2.2, 1.2)
    f.accent = None
    f.path("M120 109 Q130 116 140 109", 0.8)
    # ruff: zigzag rim, inner ring, pleat lines
    rim = []
    for k in range(49):
        a = math.radians(k * 360 / 48)
        rr = 1.0 if k % 2 == 0 else 0.82
        rim.append((130 + 48 * rr * math.cos(a), 126 + 15 * rr * math.sin(a)))
    f.poly(rim, 1.1)
    f.ellipse(130, 124, 15, 5, 0.8)
    for k in range(0, 48, 2):
        a = math.radians(k * 360 / 48)
        f.path(f"M{130 + 15 * math.cos(a):.1f} {124 + 5 * math.sin(a):.1f} "
               f"L{130 + 48 * math.cos(a):.1f} {126 + 15 * math.sin(a):.1f}", 0.5)
    # striped shirt and suspenders
    for k in range(11):
        y = 148 + k * 11
        f.path(f"M{108:.1f} {y} Q130 {y + 3} {152:.1f} {y}", 0.55)
    f.path("M117 138 L119 262 M143 138 L141 262", 0.9)
    # wide open jacket with sleeves
    f.path("M100 136 C88 140 82 150 80 166 C78 210 80 250 84 290", 1.2)
    f.path("M160 136 C172 140 178 150 180 166 C182 210 180 250 176 290", 1.2)
    f.path("M100 136 C98 190 100 250 100 300", 1.0)
    f.path("M160 136 C162 190 160 250 160 300", 1.0)
    f.path("M100 300 L108 294 M160 300 L152 294", 0.8)
    f.path("M96 170 C92 220 94 260 98 284", 0.8)
    f.path("M164 170 C168 220 166 260 162 284", 0.8)
    # gloves
    f.ellipse(88, 302, 11, 10, 1.1)
    f.ellipse(172, 302, 11, 10, 1.1)
    f.path("M80 296 L74 290 M180 296 L186 290", 0.8)
    # baggy trousers
    f.path("M104 264 C96 330 90 410 90 470", 1.2)
    f.path("M156 264 C164 330 170 410 170 470", 1.2)
    f.path("M130 300 C128 360 126 420 128 470", 1.0)
    f.path("M90 470 Q108 476 126 470 M134 470 Q152 476 170 470", 0.9)
    f.path("M110 320 C106 380 106 420 108 460 M150 320 C154 380 154 420 152 460", 0.5)
    # long shoes
    f.ellipse(98, 486, 26, 9, 1.1, rot=-4)
    f.ellipse(164, 486, 26, 9, 1.1, rot=4)
    return f


def kleiner_mann():
    """Kleiner Mann – was nun? (Düsseldorfer Schauspielhaus): young man with curly
    hair, white shirt with full sleeves and open collar, checked waistcoat with a
    row of buttons, one hand raised to the chest."""
    f = Fig()
    f.ellipse(130, 86, 14.5, 19, 1.3)
    f.path("M114 82 C108 70 112 56 122 56 C124 48 136 48 140 56 C150 54 154 66 148 74 "
           "C154 80 150 90 146 88", 1.1)
    f.path("M116 70 C120 64 126 66 126 72 M132 62 C138 60 142 66 138 70", 0.8)
    f.path("M124 104 L123 116 M137 104 L138 116", 1.0)
    # open shirt collar
    f.path("M120 116 L126 130 L131 120 L136 130 L142 116", 1.0)
    # shoulders and sleeves
    f.path("M120 116 C108 118 98 122 92 132", 1.2)
    f.path("M142 116 C154 118 164 122 170 132", 1.2)
    f.path("M92 132 C82 170 80 230 84 292", 1.1)
    f.path("M104 150 C98 200 96 250 98 292", 0.9)
    f.ellipse(90, 302, 8, 11, 1.0)
    f.path("M170 132 C182 160 186 200 180 230 C176 246 166 256 152 258", 1.1)
    f.path("M160 150 C166 180 168 210 164 228 C162 236 156 240 150 242", 0.9)
    f.path("M152 258 C146 262 140 258 140 252 C140 246 146 242 150 242", 1.0)
    # waistcoat: V-neck, sides, pointed hem, buttons, checks – signature piece
    f.accent = ACCENTS["kleiner-mann"]
    f.path("M112 124 L130 192 L148 124", 1.1)
    f.path("M112 124 C104 128 100 134 98 142 C100 200 102 260 104 300", 1.2)
    f.path("M148 124 C156 128 160 134 162 142 C160 200 158 260 156 300", 1.2)
    f.path("M104 300 L130 314 L156 300", 1.1)
    for k in range(6):
        f.ellipse(130, 202 + k * 18, 1.8, 1.8, 0.8, n=12)
    # checks: horizontal and vertical thin lines inside the vest
    def vest_x(y):
        left = 98 + 6 * (y - 142) / 158 if y >= 142 else 112 - 14 * (y - 124) / 18
        right = 162 - 6 * (y - 142) / 158 if y >= 142 else 148 + 14 * (y - 124) / 18
        return left, right
    for k in range(9):
        y = 146 + k * 17
        l, r = vest_x(y)
        if y < 192:
            vx = 18 * (y - 124) / 68
            f.path(f"M{l + 1:.1f} {y} L{112 + vx - 1:.1f} {y} M{148 - vx + 1:.1f} {y} L{r - 1:.1f} {y}", 0.45)
        else:
            f.path(f"M{l + 1:.1f} {y} L{r - 1:.1f} {y}", 0.45)
    for x in (108, 118, 142, 152):
        f.path(f"M{x} {150 if x in (108, 152) else 168} L{x} 300", 0.45)
    f.accent = None
    # trousers and shoes
    f.path("M104 300 C102 380 100 460 100 520", 1.2)
    f.path("M156 300 C158 380 160 460 160 520", 1.2)
    f.path("M130 316 L130 520", 1.0)
    f.path("M96 520 C96 528 114 530 128 526 L128 520 M132 520 L132 526 C146 530 164 528 164 520", 1.0)
    return f


def sonne():
    """Ewige Sonne (Bühnen Bern): radiating sun halo, white blouse with full
    sleeves, golden scaled breastplate, wide black skirt to the ankles, sneakers."""
    f = Fig()
    # halo with rays – signature piece
    f.accent = ACCENTS["sonne"]
    f.ellipse(130, 66, 36, 36, 1.2)
    f.ellipse(130, 66, 24, 24, 0.8)
    for k in range(28):
        a = math.radians(k * 360 / 28)
        f.path(f"M{130 + 26 * math.cos(a):.1f} {66 + 26 * math.sin(a):.1f} "
               f"L{130 + 34 * math.cos(a):.1f} {66 + 34 * math.sin(a):.1f}", 0.6)
    f.accent = None
    f.ellipse(130, 72, 12.5, 16, 1.3)
    f.path("M124 88 L123 100 M136 88 L137 100", 1.0)
    # blouse with full sleeves
    f.path("M123 100 C112 102 102 106 96 114", 1.2)
    f.path("M137 100 C148 102 158 106 164 114", 1.2)
    f.path("M96 114 C80 128 76 160 86 186 C92 198 102 200 108 192", 1.1)
    f.path("M164 114 C180 128 186 160 176 186 C170 198 160 200 152 192", 1.1)
    f.path("M88 178 C92 186 100 190 108 188", 0.7)
    f.path("M172 178 C168 186 160 190 152 188", 0.7)
    # hands; one holds a small ball
    f.path("M100 196 C96 206 98 214 104 214", 0.9)
    f.ellipse(160, 210, 6, 6, 0.9)
    # breastplate: shield + rows of scales
    f.path("M106 110 L154 110 L150 168 L130 200 L110 168 Z", 1.2)
    for row, (y, hw, n) in enumerate(((122, 20, 5), (136, 18, 5), (150, 16, 4), (164, 13, 4), (178, 9, 3))):
        f.scallops(130 - hw, 130 + hw, y, n, 6, 0.7)
    # wide black skirt
    f.path("M108 196 C84 250 50 370 34 468", 1.2)
    f.path("M152 196 C176 250 210 370 226 468", 1.2)
    f.path("M34 468 C62 482 92 474 118 484 C140 476 170 486 196 476 C210 472 220 474 226 468", 1.1)
    for x0, x1 in ((114, 80), (124, 108), (136, 150), (146, 182)):  # folds
        f.path(f"M{x0} 214 C{x0} 300 {x1} 400 {x1} 474", 0.6)
    # legs and sneakers
    f.path("M118 482 L116 512 M128 482 L128 512", 1.0)
    f.path("M140 480 L142 510 M150 478 L154 508", 1.0)
    f.path("M112 512 C112 522 124 524 132 520 L130 512", 1.0)
    f.path("M140 510 C140 520 154 522 160 516 L156 508", 1.0)
    return f


FIGURINES = {"traviata": traviata, "coriolan": coriolan, "traum": traum, "kleiner-mann": kleiner_mann, "sonne": sonne}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=OUT_DIR)
    ap.add_argument("--preview", metavar="HTML")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    for slug, fn in FIGURINES.items():
        fig = fn()
        path = os.path.join(args.out, slug + ".svg")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(fig.svg() + "\n")
        print(f"{path}  {len(fig.strokes)} strokes")
    if args.preview:
        cards = "".join(f'<img src="file://{os.path.join(args.out, s)}.svg" style="height:560px;margin:20px">' for s in FIGURINES)
        with open(args.preview, "w", encoding="utf-8") as fh:
            fh.write(f"<body style='background:#1a1a1a;margin:0'>{cards}</body>")


if __name__ == "__main__":
    main()

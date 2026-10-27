#!/usr/bin/env python3
"""Venue drawings for the Dates page.

Each venue is a white line drawing of the auditorium *seen from the stage*,
built as a small 3D model (metres) and projected with a one-point perspective.
Output: stroke-only SVGs in images/venues/<slug>.svg (no fills, no styles).

Usage (from the repo root):
    python3 tools/venue-drawings/venue_drawings.py              # all venues
    python3 tools/venue-drawings/venue_drawings.py bern-vidmarhallen
    python3 tools/venue-drawings/venue_drawings.py --preview /tmp/venues.html

No third-party packages needed. See README.md next to this file.
"""
import argparse
import math
import os
import sys

# Canvas of every drawing. Keep identical for all venues so the page can
# position them the same way.
W, H = 1600, 780
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT_DIR = os.path.join(REPO, "images", "venues")


# --------------------------------------------------------------------------- core
class Cam:
    """Camera on the stage looking into the auditorium (+z).
    x: left/right, y: height above stage floor, z: distance from the camera.
    cx/cy: vanishing point on the canvas, f: focal length in px, eye: camera height."""

    def __init__(self, cx=800, cy=560, f=640, eye=2.2):
        self.cx, self.cy, self.f, self.eye = cx, cy, f, eye

    def p(self, x, y, z):
        if z < 0.5:  # behind / too close to the camera: drop
            return None
        return (self.cx + self.f * x / z, self.cy - self.f * (y - self.eye) / z)


class Pen:
    """Collects projected polylines, grouped by stroke width."""

    def __init__(self, cam):
        self.cam, self.groups = cam, {}

    def poly(self, pts3, w=1.5):
        segs, cur = [], []
        for q in pts3:
            p = self.cam.p(*q)
            if p is None:
                if len(cur) > 1:
                    segs.append(cur)
                cur = []
            else:
                cur.append(p)
        if len(cur) > 1:
            segs.append(cur)
        for s in segs:
            self.groups.setdefault(w, []).append("M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in s))

    def line(self, a, b, w=1.5, n=1):
        """Straight 3D line; n > 1 subdivides it (needed when it crosses the camera plane)."""
        self.poly([tuple(a[i] + (b[i] - a[i]) * k / n for i in range(3)) for k in range(n + 1)], w)

    def svg(self):
        out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">']
        for w, ds in sorted(self.groups.items()):
            out.append(f'<path d="{" ".join(ds)}" fill="none" stroke="#ffffff" stroke-width="{w}" '
                       f'stroke-linecap="round" stroke-linejoin="round"/>')
        out.append("</svg>")
        return "\n".join(out)


class Shift:
    """Moves the whole scene away from the camera by dz (camera stands further upstage)."""

    def __init__(self, pen, dz):
        self.pen, self.dz = pen, dz

    def poly(self, pts, w=1.5):
        self.pen.poly([(x, y, z + self.dz) for x, y, z in pts], w)

    def line(self, a, b, w=1.5, n=1):
        self.pen.line((a[0], a[1], a[2] + self.dz), (b[0], b[1], b[2] + self.dz), w, n)

    def svg(self):
        return self.pen.svg()


def resample(pts, step):
    """Points every `step` metres along a 3D polyline (used for seats)."""
    out, carry = [pts[0]], 0.0
    for a, b in zip(pts, pts[1:]):
        L = math.dist(a, b)
        t = step - carry
        while t <= L:
            out.append(tuple(a[i] + (b[i] - a[i]) * t / L for i in range(3)))
            t += step
        carry = L - (t - step)
    return out


def seats_along(pen, path, drop, step=0.56, w=0.8):
    """Seat backs: short vertical ticks every `step` m below a row line."""
    for q in resample(path, step):
        pen.line(q, (q[0], q[1] - drop, q[2]), w)


def ushape(R, zc, zfront, y, n=90):
    """Horseshoe (Rang): straight side from the stage end, semicircle at the back, straight side back."""
    left = [(-R, y, zfront), (-R, y, zc)]
    arc = [(-R * math.cos(math.radians(180 * i / n)), y, zc + R * math.sin(math.radians(180 * i / n)))
           for i in range(n + 1)]
    right = [(R, y, zc), (R, y, zfront)]
    return left + arc[1:-1] + right


# ------------------------------------------------------------------------- venues
def cottbus_grosses_haus():
    """Staatstheater Cottbus, Großes Haus. Layout from the ticket seat map:
    Parkett 11 continuous curved rows, 1. Rang horseshoe reaching the stage with boxes
    (Logen) at the back, 2. Rang with five rows."""
    pen = Pen(Cam(cy=500, f=520, eye=1.6))
    for r in range(11):
        R, zc = 14 + r * 0.92, -11.5
        top = -1.0 + r * 0.09 + 0.9
        a1 = math.asin((6.8 + r * 0.22) / R)
        n = 60
        row = [(R * math.sin(-a1 + 2 * a1 * i / n), top, zc + R * math.cos(-a1 + 2 * a1 * i / n))
               for i in range(n + 1)]
        pen.poly(row, 1.4)
        seats_along(pen, row, 0.32)
    # 1. Rang
    zc, R, y1 = 9.0, 8.4, 3.0
    pen.poly(ushape(R, zc, 1.2, y1), 1.8)
    pen.poly(ushape(R, zc, 1.2, y1 + 0.95), 1.8)
    for dr, dy in ((0.9, 1.45), (1.8, 1.9)):
        row = ushape(R + dr, zc, 1.6, y1 + dy)
        pen.poly(row, 1.0)
        seats_along(pen, row, 0.3, w=0.7)
    for i in range(9):  # box partitions
        a = math.radians(20 + 140 * i / 8)
        x, z = -R * math.cos(a), zc + R * math.sin(a)
        pen.line((x, y1 + 0.95, z), (x, y1 + 3.0, z), 0.9)
    pen.poly([(-R * math.cos(math.radians(a)), y1 + 3.0, zc + R * math.sin(math.radians(a)))
              for a in range(20, 161, 2)], 1.1)
    for q in resample(ushape(R, zc, 1.2, y1), 1.8):  # parapet panels
        pen.line(q, (q[0], q[1] + 0.95, q[2]), 0.9)
    # 2. Rang
    y2, R2 = 6.9, 8.9
    pen.poly(ushape(R2, zc + 0.6, 2.4, y2), 1.8)
    pen.poly(ushape(R2, zc + 0.6, 2.4, y2 + 0.95), 1.8)
    for q in resample(ushape(R2, zc + 0.6, 2.4, y2), 1.8):
        pen.line(q, (q[0], q[1] + 0.95, q[2]), 0.9)
    for k in range(5):
        pen.poly(ushape(R2 + 0.9 * (k + 1), zc + 0.6, 2.8 + 0.3 * k, y2 + 1.4 + 0.5 * k), 0.9)
    # ceiling cornice and ceiling ellipse
    pen.poly(ushape(R2 + 5.6, zc + 0.6, 2.0, y2 + 4.8), 1.3)
    pen.poly([(5.5 * math.cos(math.radians(d)), y2 + 6.2, zc + 2 + 5.5 * math.sin(math.radians(d)))
              for d in range(0, 361, 5)], 1.0)
    return pen


def bern_vidmarhallen():
    """Bühnen Bern, Vidmarhallen (Ewige Sonne). Layout from the ticket seat map:
    square stage in the middle, tribune with 8 straight rows opposite, side blocks with
    3 rows each along the stage; industrial steel hall."""
    pen = Shift(Pen(Cam(cy=590, f=560, eye=1.7)), 4.5)
    s = 5.0  # half stage size
    for r in range(8):
        z, y = s + 1.0 + r * 0.9, 0.2 + r * 0.38
        row = [(-6.6, y + 0.9, z), (6.6, y + 0.9, z)]
        pen.poly(row, 1.4)
        pen.line((-6.6, y, z - 0.45), (6.6, y, z - 0.45), 0.8)
        seats_along(pen, row, 0.4)
    zb, yb = s + 1.0 + 8 * 0.9, 0.2 + 8 * 0.38
    for x in (-6.6, 6.6):
        pen.line((x, 0.2, s + 0.55), (x, yb + 0.9, zb), 1.2)
    for side in (-1, 1):  # side blocks facing inward
        for k in range(3):
            x, y = side * (s + 1.2 + k * 0.9), 0.2 + k * 0.38
            row = [(x, y + 0.9, -4.0), (x, y + 0.9, 4.2)]
            pen.poly(row, 1.3)
            pen.line((x - side * 0.45, y, -4.0), (x - side * 0.45, y, 4.2), 0.8)
            seats_along(pen, row, 0.4)
        pen.line((side * (s + 0.75), 0.2, 4.2), (side * (s + 3.3), 1.3 + 0.9, 4.2), 1.1)
    hw, zend, yr = 15.0, 22.0, 11.0  # the hall
    for x in (-hw, hw):
        pen.line((x, 0, 1.0), (x, 0, zend), 1.3, 20)
        pen.line((x, yr, 1.0), (x, yr, zend), 1.3, 20)
    pen.poly([(-hw, 0, zend), (hw, 0, zend), (hw, yr, zend), (-hw, yr, zend), (-hw, 0, zend)], 1.3)
    for z in (3.0, 7.5, 12.0, 16.5, 21.0):  # portal frames with lattice rafters
        pen.line((-hw, 0, z), (-hw, yr, z), 1.1)
        pen.line((hw, 0, z), (hw, yr, z), 1.1)
        pen.poly([(-hw, yr, z), (0, yr + 1.2, z), (hw, yr, z)], 1.3)
        pen.poly([(-hw, yr - 0.8, z), (0, yr + 0.4, z), (hw, yr - 0.8, z)], 0.8)
        for i in range(20):
            xa, xb = -hw + 2 * hw * i / 20, -hw + 2 * hw * (i + 1) / 20
            pen.line((xa, yr + 1.2 * (1 - abs(xa) / hw), z), (xb, yr - 0.8 + 1.2 * (1 - abs(xb) / hw), z), 0.6)
    for x in (-10, -5, 0, 5, 10):
        yy = yr + 1.2 * (1 - abs(x) / hw)
        pen.line((x, yy, 3.0), (x, yy, 21.0), 0.8, 8)
    for x in (-hw, hw):  # high side windows
        for z0 in (4.0, 8.5, 13.0, 17.5):
            pen.poly([(x, 7.5, z0), (x, 7.5, z0 + 3), (x, 9.8, z0 + 3), (x, 9.8, z0), (x, 7.5, z0)], 0.8)
    for z in (1.5, 3.5):  # lighting bars over the stage
        pen.line((-9, 8.0, z), (9, 8.0, z), 1.0)
    return pen


def frankfurt_bockenheimer_depot():
    """Oper Frankfurt, Bockenheimer Depot (Flavio). Character from interior photos:
    steep tribune wall to wall, arched timber roof with diamond lattice (Zollinger-like),
    lighting trusses over the front rows, lunette in the gable above the last row."""
    HW, SPRING, RISE, ZEND = 9.4, 12.0, 5.0, 25.0

    def roof(t, z):
        return (-HW + 2 * HW * t, SPRING + RISE * math.sin(math.pi * t) ** 0.65, z)

    pen = Pen(Cam(cy=700, f=470, eye=1.7))
    rows, z0, dz, rise = 22, 4.2, 0.85, 0.48
    tops = []
    for r in range(rows):
        z, y = z0 + r * dz, 0.25 + r * rise
        top = y + 0.88
        tops.append((z, top))
        row = [(-HW + 0.4, top, z), (HW - 0.4, top, z)]
        pen.poly(row, 1.3 if r < 8 else 1.0)
        pen.line((-HW + 0.4, y, z - 0.42), (HW - 0.4, y, z - 0.42), 0.6)
        seats_along(pen, row, 0.42 if r < 10 else 0.3, step=0.55, w=0.7 if r < 10 else 0.5)
    zb, ytop = tops[-1]

    def tribune_top(z):
        if z <= z0:
            return 0.0
        return tops[min(int((z - z0) / dz), rows - 1)][1]

    for z in [4.0 + 3.0 * i for i in range(7)] + [ZEND]:  # arched ribs, legs above the seating only
        pen.poly([roof(i / 48, z) for i in range(49)], 1.4 if z < ZEND else 1.6)
        for x in (-HW, HW):
            pen.line((x, max(tribune_top(z), 0.0), z), (x, SPRING, z), 1.1)
    N, L = 9, 3.0  # diamond lattice between the ribs
    for k in range(-4, N + 9):
        for sgn in (1, -1):
            pts, z = [], 4.0
            while z <= ZEND + 1e-6:
                t = (k + sgn * (z - 4.0) / L) / N
                if 0.0 <= t <= 1.0:
                    pts.append(roof(t, z))
                elif pts:
                    break
                z += 0.25
            if len(pts) > 1:
                pen.poly(pts, 0.55)
    for x in (-HW, HW):
        pen.line((x, SPRING, 4.0), (x, SPRING, ZEND), 1.0, 20)
        pen.line((x * 0.957, 0.25, z0 - 0.42), (x * 0.957, ytop, zb), 1.1, 10)
    # lunette: only what shows above the last row (no hidden-line removal otherwise)
    vis = ytop + 0.2
    lr, lc = 5.6, SPRING + 0.2
    arc = [(lr * math.cos(math.radians(a)), lc + lr * math.sin(math.radians(a)), ZEND) for a in range(0, 181, 4)]
    pen.poly([p for p in arc if p[1] >= vis], 1.4)
    for a in range(15, 180, 15):
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        p0, p1 = (0.9 * ca, lc + 0.9 * sa, ZEND), (lr * ca, lc + lr * sa, ZEND)
        if p1[1] >= vis:
            if p0[1] < vis:
                f = (vis - p0[1]) / (p1[1] - p0[1])
                p0 = (p0[0] + (p1[0] - p0[0]) * f, vis, ZEND)
            pen.line(p0, p1, 0.7)
    for rr in (2.6, 4.0):
        pen.poly([(rr * math.cos(math.radians(a)), lc + rr * math.sin(math.radians(a)), ZEND)
                  for a in range(0, 181, 4) if lc + rr * math.sin(math.radians(a)) >= vis], 0.7)
    pen.line((-HW, vis, ZEND), (HW, vis, ZEND), 0.9)
    for z, y in ((9.0, 13.8), (14.0, 14.4)):  # lighting trusses with lamps
        pen.line((-7.6, y, z), (7.6, y, z), 1.2)
        pen.line((-7.6, y - 0.5, z), (7.6, y - 0.5, z), 0.9)
        for i in range(24):
            x0, x1 = -7.6 + 15.2 * i / 24, -7.6 + 15.2 * (i + 1) / 24
            ya, yb = (y, y - 0.5) if i % 2 == 0 else (y - 0.5, y)
            pen.line((x0, ya, z), (x1, yb, z), 0.5)
        for x in (-6.0, -3.6, -1.2, 1.2, 3.6, 6.0):
            pen.line((x, y - 0.5, z), (x, y - 0.85, z), 0.8)
            pen.poly([(x + 0.22 * math.cos(math.radians(d)), y - 1.07 + 0.22 * math.sin(math.radians(d)), z)
                      for d in range(0, 361, 30)], 0.9)
    return pen


# slug -> builder. The slug is the file name in images/venues/ and the key in data/venues.json.
VENUES = {
    "bern-vidmarhallen": bern_vidmarhallen,
    "cottbus-grosses-haus": cottbus_grosses_haus,
    "frankfurt-bockenheimer-depot": frankfurt_bockenheimer_depot,
}


def preview_html(slugs):
    cards = "\n".join(
        f'<figure><figcaption>{s}</figcaption><img src="file://{os.path.join(OUT_DIR, s + ".svg")}" alt=""></figure>'
        for s in slugs)
    return ("<!doctype html><meta charset='utf-8'><title>Venue drawings</title>"
            "<style>body{margin:0;padding:40px;background:#1a1a1a;color:#aaa;font:14px system-ui}"
            "figure{margin:0 0 48px}img{width:100%;max-width:1200px;display:block}</style>" + cards)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("slugs", nargs="*", help="venues to build (default: all)")
    ap.add_argument("--out", default=OUT_DIR, help="output folder (default: images/venues)")
    ap.add_argument("--preview", metavar="HTML", help="also write a preview page showing the drawings")
    args = ap.parse_args()
    slugs = args.slugs or list(VENUES)
    unknown = [s for s in slugs if s not in VENUES]
    if unknown:
        sys.exit(f"unknown venue(s): {', '.join(unknown)} (known: {', '.join(VENUES)})")
    os.makedirs(args.out, exist_ok=True)
    for s in slugs:
        path = os.path.join(args.out, s + ".svg")
        with open(path, "w", encoding="utf-8") as f:
            f.write(VENUES[s]().svg() + "\n")
        print(f"{path}  ({os.path.getsize(path) // 1024} KB)")
    if args.preview:
        with open(args.preview, "w", encoding="utf-8") as f:
            f.write(preview_html(slugs))
        print(f"preview: {args.preview}")


if __name__ == "__main__":
    main()

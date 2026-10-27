#!/usr/bin/env python3
"""Small true-to-scale map for the Dates page (Germany + neighbours).

Reads the clipped Natural Earth borders in geo/countries-central-europe.json,
projects them with a Lambert conformal conic projection (standard parallels
48° and 54° N – the usual choice for Germany, shapes and distances stay true),
and writes:

  images/venues/map.svg       – the border lines (stroke only)
  data/venues.json            – for every venue with "lat"/"lon": "map": {"x": %, "y": %}

Usage (from the repo root):
    python3 tools/venue-drawings/venue_map.py

Run it again whenever a venue is added to data/venues.json.
"""
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
GEO = os.path.join(HERE, "geo", "countries-central-europe.json")
VENUES = os.path.join(REPO, "data", "venues.json")
OUT_SVG = os.path.join(REPO, "images", "venues", "map.svg")

WIDTH = 300.0          # viewBox width; height follows from the frame
MARGIN = 0.05          # empty border around Germany + venues, share of the larger side
SIMPLIFY = 0.35        # Douglas–Peucker tolerance in viewBox units (~1/600 of the width)

# Lambert conformal conic on the sphere
PHI1, PHI2, PHI0, LAM0 = map(math.radians, (48.0, 54.0, 51.0, 10.5))
_n = math.log(math.cos(PHI1) / math.cos(PHI2)) / math.log(
    math.tan(math.pi / 4 + PHI2 / 2) / math.tan(math.pi / 4 + PHI1 / 2))
_F = math.cos(PHI1) * math.tan(math.pi / 4 + PHI1 / 2) ** _n / _n
_rho0 = _F / math.tan(math.pi / 4 + PHI0 / 2) ** _n


def project(lon, lat):
    phi, lam = math.radians(lat), math.radians(lon)
    rho = _F / math.tan(math.pi / 4 + phi / 2) ** _n
    t = _n * (lam - LAM0)
    return rho * math.sin(t), _rho0 - rho * math.cos(t)   # x east, y north


def simplify(pts, tol):
    """Douglas–Peucker."""
    if len(pts) < 3:
        return pts
    (x1, y1), (x2, y2) = pts[0], pts[-1]
    dx, dy = x2 - x1, y2 - y1
    L = math.hypot(dx, dy)
    dmax, idx = 0.0, 0
    for i in range(1, len(pts) - 1):
        if L < 1e-9:  # closed ring: distance to the start point
            d = math.hypot(pts[i][0] - x1, pts[i][1] - y1)
        else:
            d = abs(dy * pts[i][0] - dx * pts[i][1] + x2 * y1 - y2 * x1) / L
        if d > dmax:
            dmax, idx = d, i
    if dmax <= tol:
        return [pts[0], pts[-1]]
    return simplify(pts[:idx + 1], tol)[:-1] + simplify(pts[idx:], tol)


def clip_polyline(pts, x0, y0, x1, y1):
    """Liang–Barsky per segment; returns open polylines inside the rectangle."""
    out, cur = [], []

    def clip(a, b):
        t0, t1 = 0.0, 1.0
        dx, dy = b[0] - a[0], b[1] - a[1]
        for p, q in ((-dx, a[0] - x0), (dx, x1 - a[0]), (-dy, a[1] - y0), (dy, y1 - a[1])):
            if p == 0:
                if q < 0:
                    return None
            else:
                r = q / p
                if p < 0:
                    t0 = max(t0, r)
                else:
                    t1 = min(t1, r)
                if t0 > t1:
                    return None
        return (a[0] + t0 * dx, a[1] + t0 * dy), (a[0] + t1 * dx, a[1] + t1 * dy)

    for a, b in zip(pts, pts[1:]):
        seg = clip(a, b)
        if seg is None:
            if len(cur) > 1:
                out.append(cur)
            cur = []
            continue
        if not cur or cur[-1] != seg[0]:
            if len(cur) > 1:
                out.append(cur)
            cur = [seg[0]]
        cur.append(seg[1])
        if seg[1] != b:  # left the rectangle
            out.append(cur)
            cur = []
    if len(cur) > 1:
        out.append(cur)
    return out


def main():
    geo = json.load(open(GEO, encoding="utf-8"))
    venues = json.load(open(VENUES, encoding="utf-8"))

    # frame: Germany + every venue, plus a margin
    pts = [project(lon, lat) for c in geo["countries"] if c["a3"] == "DEU" for line in c["lines"] for lon, lat in line]
    pts += [project(v["lon"], v["lat"]) for v in venues["venues"].values() if "lat" in v]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    m = MARGIN * max(max(xs) - min(xs), max(ys) - min(ys))
    X0, X1, Y0, Y1 = min(xs) - m, max(xs) + m, min(ys) - m, max(ys) + m
    s = WIDTH / (X1 - X0)
    height = (Y1 - Y0) * s

    def to_view(x, y):  # projected -> viewBox (y down)
        return ((x - X0) * s, (Y1 - y) * s)

    paths = {"DEU": [], "other": []}
    for c in geo["countries"]:
        for line in c["lines"]:
            proj = [to_view(*project(lon, lat)) for lon, lat in line]
            for part in clip_polyline(proj, 0, 0, WIDTH, height):
                part = simplify(part, SIMPLIFY)
                if len(part) > 1:
                    d = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in part)
                    paths["DEU" if c["a3"] == "DEU" else "other"].append(d)

    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH:.0f} {height:.1f}" '
           f'width="{WIDTH:.0f}" height="{height:.1f}">',
           f'<path d="{" ".join(paths["other"])}" fill="none" stroke="#ffffff" stroke-opacity="0.22" '
           f'stroke-width="0.8" stroke-linecap="round" stroke-linejoin="round"/>',
           f'<path d="{" ".join(paths["DEU"])}" fill="none" stroke="#ffffff" stroke-opacity="0.6" '
           f'stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/>',
           "</svg>"]
    os.makedirs(os.path.dirname(OUT_SVG), exist_ok=True)
    with open(OUT_SVG, "w", encoding="utf-8") as f:
        f.write("\n".join(svg) + "\n")
    print(f"{os.path.relpath(OUT_SVG, REPO)}  {WIDTH:.0f} x {height:.1f}  "
          f"({os.path.getsize(OUT_SVG) // 1024} KB, 1 unit ≈ {1 / s * 6371:.1f} km)")

    for slug, v in venues["venues"].items():
        if "lat" not in v:
            continue
        x, y = to_view(*project(v["lon"], v["lat"]))
        v["map"] = {"x": round(100 * x / WIDTH, 2), "y": round(100 * y / height, 2)}
        print(f"  {slug}: {v['map']}")
    with open(VENUES, "w", encoding="utf-8") as f:
        f.write(json.dumps(venues, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()

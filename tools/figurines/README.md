# Figurines (About page)

Line figurines after costumes from Susanne Uhl's productions. On page load
their strokes lie scattered all over the page; while scrolling, one figurine
after the other assembles. One signature costume piece per figurine keeps its
colour from the production.

- **Desktop** (free margin ≥ 190 px beside the text): five figurines
  alternating left/right of photo and text, ~190 px wide.
- **Narrow screens:** all figurines, small (~104 px), one under each of the
  first paragraphs, offset left/right/centre and slightly tilted.
- **Reduced motion:** figurines are simply complete.

## What is where

| Piece | Path |
|---|---|
| Generator (one function per figurine) | `tools/figurines/figurines.py` |
| Figurines | `images/figurines/<slug>.svg` – every stroke is its own `<path>` |
| Page logic (placement, scatter, scroll) | `scripts/figurines.js`, loaded by `about.html` and `about-en.html` |
| Styles | `styles.css`, section "Figurinen auf der About-Seite" |

## Current figurines

| Slug | Production | Coloured piece |
|---|---|---|
| `traviata` | La traviata, Staatstheater Braunschweig | rose drape / train `#d9a08a` |
| `coriolan` | Coriolan, Düsseldorfer Schauspielhaus | red clown nose `#e2312b` |
| `traum` | Das Leben ist ein Traum, Staatsschauspiel Dresden | big red rose `#c8232c` |
| `kleiner-mann` | Kleiner Mann – was nun?, Düsseldorfer Schauspielhaus | blue checked waistcoat `#4a6fc4` |
| `sonne` | Ewige Sonne, Bühnen Bern | golden sun halo `#d4ad3a` |

They are reduced drawings *after* production photos – not Susanne Uhl's own
figurines. When scans of her real figurines exist, they can replace these:
redraw each as single strokes in the same 260 × 560 box.

## Add or change a figurine

1. In `figurines.py`, write a function returning a `Fig` (box 260 × 560, feet
   at ~y 530, centre line x 130). Helpers: `path`, `poly`, `ellipse`,
   `scallops`, `_ruffled` (ruffles, roses, ruffs), `_fan` (pleated fans).
2. Wrap the signature piece in `f.accent = ACCENTS["<slug>"]` … `f.accent = None`
   and add its colour to `ACCENTS`.
3. Register it in `FIGURINES`, then build and look:
   ```bash
   python3 tools/figurines/figurines.py --preview /tmp/figurines.html
   open /tmp/figurines.html
   ```
4. Place it in `scripts/figurines.js`: `MARGIN_FIGURES` (desktop: `side`,
   `at` = height as share of the main area) and `INLINE_FIGURES` (narrow:
   `after` = paragraph index, `align`, `tilt`).
5. Check `about.html` locally (`python3 -m http.server 8000`) at desktop and
   phone width; bump the `?v=` on the stylesheet link if `styles.css` changed.

## Look rules

- White single strokes (0.5–1.3), one coloured signature piece, no fills.
- Frontal, calm, fashion-sketch proportions; 40–100 strokes per figurine
  (fewer strokes = less to fly around).

## Tuning (scripts/figurines.js)

| Value | Meaning |
|---|---|
| `SCATTER_X`, `SCATTER_Y` | start spread as share of window width / height |
| `SCATTER_ROT` | max start rotation of a stroke (deg) |
| `STAGGER` | how unevenly the strokes set off |
| `FADE_IN` | px of scrolling over which the scattered strokes fade in (page is blank before scrolling) |
| `DESK_FIRST`, `DESK_SPAN` | desktop: figurines complete evenly over the whole scroll (first at 30 %), each assembling over 1.6 gaps |
| `FIRST_VISIBLE` | desktop: no figurine completes up in the header area – any figurine that would be closer than this many px to the window top when it completes is moved down (currently La traviata and Coriolan); the others keep their `at` |
| `FIRST_END`, `NEXT_END`, `SPAN` | narrow screens: when (in window heights of scrolling) the figurines are complete, one after the other |
| `LINE_OPACITY`, `ACCENT_OPACITY` | final opacity of white lines / coloured piece |

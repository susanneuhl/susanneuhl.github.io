# Venue drawings & map (Dates page)

Each production on `shows.html` gets a white line drawing of the auditorium
where it plays, **seen from the stage** – the view the costumes have – and its
city on a small true-to-scale map.

- **Desktop:** drawing faint behind the production card, slow scroll zoom into
  the room; a fixed map at the right edge (≥ 1280 px) where the city of the
  production in the middle of the window lights up.
- **Mobile (≤ 900 px):** the drawing as its own full-width strip under the
  photo (gentler zoom), a mini map next to the title with the city lit.

Everything is decorative (`aria-hidden`) and optional: a show without an entry
in `data/venues.json` simply looks like before.

---

## Checklist: a new production appears on the Dates page

The production itself (dates, title, image) comes from the scraper
(`scripts/scrape_shows.py` → `data/shows.json`, rewritten daily). Its key in
`data/shows.json` is the **show id**, e.g. `ewige-sonne`. Then:

1. **Find the actual venue, not just the theatre.** Open the ticket page of a
   date: the venue is listed there. Example: "Bühnen Bern" plays *Ewige Sonne*
   in the **Vidmarhallen**, not in the Stadttheater. One theatre often has
   several stages.
2. **Venue already exists?** (see `venues` in `data/venues.json`)
   → only add `"<show id>": "<venue slug>"` under `shows`. Done, go to step 6.
3. **New venue:** collect
   - the seat map from the ticket shop (row counts, blocks, aisles yes/no,
     Rang/Logen, side blocks) – we take the *arrangement*, never the graphic;
   - 1–2 interior photos (roof, windows, galleries, trusses);
   - the address → latitude/longitude (any map service).
4. **Draw it:** add a builder to `venue_drawings.py` (see "How a drawing is
   made" below), register it in `VENUES`, then
   ```bash
   python3 tools/venue-drawings/venue_drawings.py <slug> --preview /tmp/venues.html
   open /tmp/venues.html
   ```
   The command prints `focus: 50.0% 75.6%` – keep it for step 5.
5. **Register the venue** in `data/venues.json` under `venues`:
   ```json
   "city-venue-name": {
     "name": "Großes Haus",
     "city": "Cottbus",
     "drawing": "images/venues/city-venue-name.svg",
     "focus": "50.0% 64.1%",
     "lat": 51.7579,
     "lon": 14.3279
   }
   ```
   and map the show under `shows`. Then rebuild the map (writes `map.svg` and
   the `map` position of every venue into `data/venues.json`):
   ```bash
   python3 tools/venue-drawings/venue_map.py
   ```
6. **Look at it locally.** `shows.html` loads JSON, so open it through a small
   server, not as a file:
   ```bash
   python3 -m http.server 8000      # in the repo root
   open http://localhost:8000/shows.html
   ```
   Check at ~1440 px, ~1280 px and phone width (browser dev tools): dates and
   "Tickets" clearly in front, drawing felt more than seen, the right city
   lights up, no horizontal scrolling, no console errors.
7. **Ship it** on its own branch; before merging, `git pull --rebase origin main`
   (the scraper bot commits to `main` daily). If `styles.css` changed, bump the
   `?v=` on the stylesheet link in `shows.html`.

---

## What is where

| Piece | Path |
|---|---|
| Drawing generator (3D model → SVG) | `tools/venue-drawings/venue_drawings.py` |
| Map generator | `tools/venue-drawings/venue_map.py` |
| Map borders (Natural Earth, clipped) | `tools/venue-drawings/geo/countries-central-europe.json` |
| Drawings, map | `images/venues/<slug>.svg`, `images/venues/map.svg` |
| Venues + show → venue mapping | `data/venues.json` (hand-maintained, the scraper never touches it) |
| Page logic | `shows.html`: `venuesPromise` + card building in `loadShows()`, `initDatesScroll()`, `buildDatesMap()` |
| Styles | `styles.css`: `.event-venue`, `.dates-map*`, `.event-venue-strip`, `.event-minimap*` |

## How a drawing is made

Each venue is a small model in metres, projected with one-point perspective
(`Cam`) and drawn as polylines (`Pen`). No hidden-line removal: keep the model
sparse enough that lines don't pile up in the centre.

1. **Layout from facts.** Rows, blocks, tiers and their order from the seat map.
2. **Character from photos.** Model what makes the room recognisable in a few
   simple lines.
3. **Camera.** On the stage looking into the house: `eye` 1.6–1.7 m,
   `f` 470–560, `cy` 500–700 (higher `cy` = horizon lower, more roof visible).
   `Shift` moves the camera upstage when side blocks would be behind it.
4. **Line weights.** 1.3–1.8 main edges (rows, parapets, ribs), 0.5–1.0 detail
   (seat ticks, lattice, glazing). White stroke, no fill.
5. **Canvas.** Always 1600 × 780, so every drawing sits the same way.

Start from the closest existing builder:

| Room type | Start from |
|---|---|
| Horseshoe theatre with Ränge/Logen | `cottbus_grosses_haus` |
| Hall with one steep tribune, special roof | `frankfurt_bockenheimer_depot` |
| Hall with stage in the room, seating on three sides | `bern_vidmarhallen` |

### Look rules

- Frontal, calm, architectural – a backdrop, not an illustration.
- Keep the centre readable: thin out lines converging into the vanishing point.
- Clip what would show *through* the seating (see the lunette in
  `frankfurt_bockenheimer_depot`, only drawn above the last row).
- One tick per seat (~0.55 m) on near rows, thinner further back.
- Approved by eye before shipping – the previews in the Claude design canvas
  were used for the first three.

## The map

- Projection: Lambert conformal conic, standard parallels 48° / 54° N (true to
  scale for Germany). The frame covers Germany plus every venue with a margin;
  a venue far outside (e.g. Vienna) simply widens it – rerun `venue_map.py`.
- Borders: Natural Earth 1:10m Admin 0 countries, public domain.
- The lit city switches only when the next production is clearly closer to
  the middle of the window (`SWITCH_MARGIN = 0.25` in `shows.html`); crossfade
  1.1 s (`styles.css`).

## Tuning values (styles.css)

| What | Desktop | Mobile strip |
|---|---|---|
| Scroll zoom | scale 1 → 1.25 | scale 1 → 1.14 |
| Opacity with motion | 0.06 → 0.24 → 0.06 | 0.26 → 0.42 → 0.26 |
| Opacity, reduced motion | 0.14 (static) | 0.38 (static) |

The scroll position is written by `initDatesScroll()` as `--venue-p` (0 = card
enters at the bottom, 0.5 = middle, 1 = leaves at the top) and `--venue-near`
(1 = card in the middle) on each card; desktop drawing and mobile strip both
read them. Zoom origin = the drawing's `focus`. Everything is off with
`prefers-reduced-motion`.

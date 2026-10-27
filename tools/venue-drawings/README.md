# Venue drawings (Dates page)

Behind each production on `shows.html` sits a faint white line drawing of the
auditorium where it plays, **seen from the stage** – the view the costumes have.
Desktop only for now; on screens ≤ 900 px the drawing is hidden.

## What is where

| Piece | Path |
|---|---|
| Generator (3D model → SVG) | `tools/venue-drawings/venue_drawings.py` |
| Drawings | `images/venues/<slug>.svg` |
| Which show uses which venue | `data/venues.json` (`shows`: show id → venue slug) |
| Rendering on the page | `shows.html` (`loadVenues`, `.event-venue`) |
| Styling (opacity, fade, position) | `styles.css`, section "Venue drawings" |
| Map generator + borders | `tools/venue-drawings/venue_map.py`, `geo/` |
| Map | `images/venues/map.svg` |

`data/shows.json` is rewritten daily by the scraper – never put venue data there.
A show without an entry in `data/venues.json` simply gets no drawing.

## How a drawing is made

Each venue is a small model in metres, projected with one-point perspective
(`Cam`) and drawn as polylines (`Pen`). No hidden-line removal: keep the model
sparse enough that lines don't pile up in the centre.

1. **Layout from facts, not from graphics.** Rows, blocks, tiers and their
   order come from the venue's ticket seat map (row counts, aisles yes/no,
   side blocks, Rang/Logen). Never trace, embed or redraw the seat-map graphic
   or a photo – we only take the arrangement.
2. **Character from photos.** What makes the room recognisable (roof
   structure, windows, galleries, trusses) is taken from interior photos and
   modelled in simple lines.
3. **Camera.** Stand on the stage looking into the house. Typical values:
   `eye` 1.6–1.7 m, `f` 470–560, `cy` 500–700 (higher `cy` = horizon lower,
   more roof visible). Use `Shift` to move the camera upstage when side blocks
   would otherwise be behind it.
4. **Line weights.** 1.3–1.8 for main edges (row lines, parapets, ribs),
   0.5–1.0 for detail (seat ticks, lattice, glazing). White stroke, no fill.
5. **Canvas.** Always 1600 × 780 (`W`, `H`), so every drawing sits the same
   way on the page.

### Look rules

- Frontal, calm, architectural. It's a backdrop, not an illustration.
- The centre must stay readable: thin out lines that converge into the
  vanishing point (purlins, longitudinal beams).
- Clip things that would show *through* the seating (see the lunette in
  `frankfurt_bockenheimer_depot`, only drawn above the last row).
- Seats: one tick per seat (~0.55 m) on near rows, thinner ticks further back.

## Add a new venue

1. Collect: seat map (row counts, blocks, tiers) and 1–2 interior photos.
2. In `venue_drawings.py`, write `def <city>_<venue>():` returning a `Pen`
   (start from the closest existing venue: horseshoe theatre → `cottbus_grosses_haus`,
   hall with tribune → `frankfurt_bockenheimer_depot`, three-sided seating in a
   hall → `bern_vidmarhallen`). Add it to `VENUES` with a slug like
   `city-venue-name`.
3. Build and look at it:
   ```bash
   python3 tools/venue-drawings/venue_drawings.py <slug> --preview /tmp/venues.html
   open /tmp/venues.html
   ```
4. Register it in `data/venues.json`: add the venue under `venues` with
   `drawing`, `lat` / `lon` (then run `venue_map.py`) and `focus` (the generator prints `focus`, e.g. `50.0% 75.6%` – the
   vanishing point the scroll zoom moves into), and map the show id (the key in
   `data/shows.json`) under `shows`.
5. Check `shows.html` on desktop: dates and "Tickets" must stay clearly in
   front; the drawing should be felt more than seen.

## Map (sticky, right side)

A small true-to-scale map of Germany and its neighbours sits fixed at the right
edge (screens ≥ 1280 px). The city of the production in the middle of the
window lights up in the site's rose; the others stay as grey dots.

- Borders: Natural Earth 1:10m Admin 0 countries (public domain), clipped and
  vendored in `geo/countries-central-europe.json`.
- Projection: Lambert conformal conic, standard parallels 48° / 54° N – true to
  scale for Germany. The frame covers Germany plus every venue with a margin.
- Build: `python3 tools/venue-drawings/venue_map.py` writes `images/venues/map.svg`
  and the dot positions (`map: {x, y}` in %) into `data/venues.json`. It reads
  `lat` / `lon` of each venue – add those when you add a venue, then run it.
  A venue far outside Germany (e.g. Vienna) simply widens the frame.
- Page: `buildDatesMap()` and `initDatesScroll()` in `shows.html`, styles in
  `styles.css` (`.dates-map`). Decorative (`aria-hidden`).

## Page settings (styles.css)

- Opacity `0.14` when static (reduced motion). With motion, opacity runs
  0.06 → 0.24 → 0.06 as the card passes the middle of the window.
- Scroll zoom: scale 1.0 → 1.25 from the vanishing point (`focus`) while the
  card moves through the window. Values in `styles.css`, driven by
  `initVenueDolly()` in `shows.html` via `--venue-p` / `--venue-near`.
  Desktop only, off with `prefers-reduced-motion`.
- Radial mask fades the drawing out towards the photo (left) and the bottom.
- `pointer-events: none`, `aria-hidden`, empty `alt`: purely decorative.

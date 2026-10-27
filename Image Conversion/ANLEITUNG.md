# Bild-Konvertierung

Dieses Skript erstellt aus einem Original-Bild alle benötigten Varianten für die Website.

## Was wird erstellt?

Aus `images/beispiel.jpg` werden erzeugt:

| Ordner | Dateien | Zweck |
|--------|---------|-------|
| `images/compressed/` | `.jpg` + `.avif` | Fullscreen/Lightbox (volle Größe) |
| `images/thumbs/` | `.jpg` + `.avif` | Grid-Thumbnails (max. 1000px Höhe) |
| `images/tiny/` | `.jpg` | LQIP Blur-Placeholder (~20px) |

## Voraussetzungen

Einmalig installieren:
```bash
pip3 install Pillow pillow-avif-plugin
```

## Verwendung

### Einzelnes Bild konvertieren
```bash
python3 "Image Conversion/convert_image.py" bildname.jpg
```

### Alle nicht-konvertierten Bilder auflisten
```bash
python3 "Image Conversion/convert_image.py" --list
```

### Alle auf einmal konvertieren
```bash
python3 "Image Conversion/convert_image.py" --all
```

### Bestehende Dateien überschreiben
```bash
python3 "Image Conversion/convert_image.py" bildname.jpg --force
```

## Workflow für neue Bilder

1. Original-Bild in `images/` ablegen (z.B. `images/neues-projekt.jpg`)
2. Skript ausführen: `python3 "Image Conversion/convert_image.py" neues-projekt.jpg`
3. HTML in `index.html` ergänzen (neuen `<li>`-Eintrag hinzufügen)

## Depth Maps für den 3D-/Parallax-Effekt

Die Tiefenkarten (`images/maps/`) werden **nicht** von diesem Skript erstellt, 
sondern online erzeugt.

Generator: https://huggingface.co/spaces/depth-anything/Depth-Anything-V2

1. Original-Produktionsbild hochladen (z.B. `images/ewige-sonne.jpg`)
2. Depth Map mit Depth Anything V2 erzeugen
3. PNG herunterladen
4. Prüfen: hell = nah/Vordergrund, dunkel = fern/Hintergrund
5. Datei benennen: `<bildname>_map.png`
6. Ablegen in `images/maps/`
7. In `index.html` am `<li>` anbinden: `data-depth-map="images/maps/<bildname>_map.png"`

Beispiel: `images/ewige-sonne.jpg` → `images/maps/ewige-sonne_map.png`

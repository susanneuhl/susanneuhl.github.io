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

## Hinweis zu Depth Maps

Die 3D-Tiefenkarten (`images/maps/`) werden **nicht** automatisch erstellt. 
Diese müssen manuell in Photoshop/GIMP als Graustufen-Bild erstellt werden, 
falls der 3D-Parallax-Effekt gewünscht ist.

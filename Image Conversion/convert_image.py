#!/usr/bin/env python3
"""
Bild-Konvertierungs-Skript für susanneuhl.github.io

Erstellt aus einem Original-Bild alle benötigten Varianten:
- compressed/ (AVIF + JPG) - Volle Größe, optimiert
- thumbs/ (AVIF + JPG) - Thumbnails für Grid
- tiny/ (JPG) - LQIP Placeholder (sehr klein, für Blur-Effekt)

Verwendung:
    python "Image Conversion/convert_image.py" bildname.jpg
    python "Image Conversion/convert_image.py" --all  # Alle Bilder in images/ konvertieren
"""

import os
import sys
import argparse
from pathlib import Path

try:
    from PIL import Image, ImageFilter
except ImportError:
    print("Fehler: Pillow ist nicht installiert.")
    print("Bitte installieren mit: pip install Pillow pillow-avif-plugin")
    sys.exit(1)

try:
    import pillow_avif
except ImportError:
    print("Fehler: pillow-avif-plugin ist nicht installiert.")
    print("Bitte installieren mit: pip install pillow-avif-plugin")
    sys.exit(1)

# Basis-Verzeichnis (Repository-Root)
SCRIPT_DIR = Path(__file__).parent
REPO_ROOT = SCRIPT_DIR.parent
IMAGES_DIR = REPO_ROOT / "images"

# Ausgabe-Verzeichnisse
COMPRESSED_DIR = IMAGES_DIR / "compressed"
THUMBS_DIR = IMAGES_DIR / "thumbs"
TINY_DIR = IMAGES_DIR / "tiny"

# Einstellungen (basierend auf vorhandenen Bildern ermittelt)
THUMB_MAX_HEIGHT = 1000  # Thumbnails: max 1000px Höhe
TINY_MAX_HEIGHT = 20     # LQIP: max 20px Höhe (sehr klein für Blur-Effekt)

# Qualitätseinstellungen
AVIF_QUALITY = 80
JPG_QUALITY = 85


def ensure_dirs():
    """Erstellt Ausgabe-Verzeichnisse falls nicht vorhanden."""
    COMPRESSED_DIR.mkdir(exist_ok=True)
    THUMBS_DIR.mkdir(exist_ok=True)
    TINY_DIR.mkdir(exist_ok=True)


def get_image_path(name: str) -> Path:
    """Findet das Original-Bild basierend auf dem Namen."""
    # Wenn vollständiger Pfad angegeben
    if os.path.isabs(name):
        return Path(name)
    
    # Wenn relativer Pfad mit images/ angegeben
    if name.startswith("images/"):
        return REPO_ROOT / name
    
    # Sonst im images/ Ordner suchen
    path = IMAGES_DIR / name
    if path.exists():
        return path
    
    # Auch ohne Extension suchen
    for ext in ['.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG']:
        test_path = IMAGES_DIR / f"{name}{ext}"
        if test_path.exists():
            return test_path
    
    return path  # Gibt den erwarteten Pfad zurück (für Fehlermeldung)


def convert_image(source_path: Path, force: bool = False) -> bool:
    """
    Konvertiert ein Bild in alle benötigten Varianten.
    
    Args:
        source_path: Pfad zum Original-Bild
        force: Wenn True, werden bestehende Dateien überschrieben
        
    Returns:
        True wenn erfolgreich, False bei Fehler
    """
    if not source_path.exists():
        print(f"❌ Datei nicht gefunden: {source_path}")
        return False
    
    # Basis-Name ohne Extension
    base_name = source_path.stem
    
    # Prüfen ob bereits konvertiert (wenn nicht force)
    if not force:
        existing = []
        if (COMPRESSED_DIR / f"{base_name}.avif").exists():
            existing.append("compressed/avif")
        if (COMPRESSED_DIR / f"{base_name}.jpg").exists():
            existing.append("compressed/jpg")
        if (THUMBS_DIR / f"{base_name}.avif").exists():
            existing.append("thumbs/avif")
        if (THUMBS_DIR / f"{base_name}.jpg").exists():
            existing.append("thumbs/jpg")
        if (TINY_DIR / f"{base_name}.jpg").exists():
            existing.append("tiny/jpg")
        
        if len(existing) == 5:
            print(f"⏭️  {base_name}: Bereits vollständig konvertiert (--force zum Überschreiben)")
            return True
    
    print(f"🔄 Konvertiere: {base_name}")
    
    try:
        # Bild öffnen
        with Image.open(source_path) as img:
            # In RGB konvertieren falls nötig (für JPEG-Ausgabe)
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            original_width, original_height = img.size
            print(f"   Original: {original_width} × {original_height} px")
            
            # 1. COMPRESSED (volle Größe, optimiert)
            # JPG
            compressed_jpg = COMPRESSED_DIR / f"{base_name}.jpg"
            img.save(compressed_jpg, 'JPEG', quality=JPG_QUALITY, optimize=True)
            print(f"   ✓ compressed/{base_name}.jpg ({compressed_jpg.stat().st_size // 1024} KB)")
            
            # AVIF
            compressed_avif = COMPRESSED_DIR / f"{base_name}.avif"
            img.save(compressed_avif, 'AVIF', quality=AVIF_QUALITY)
            print(f"   ✓ compressed/{base_name}.avif ({compressed_avif.stat().st_size // 1024} KB)")
            
            # 2. THUMBS (skaliert auf max 1000px Höhe)
            thumb_ratio = min(1.0, THUMB_MAX_HEIGHT / original_height)
            thumb_width = int(original_width * thumb_ratio)
            thumb_height = int(original_height * thumb_ratio)
            
            if thumb_ratio < 1.0:
                thumb_img = img.resize((thumb_width, thumb_height), Image.LANCZOS)
            else:
                thumb_img = img.copy()
            
            # JPG
            thumbs_jpg = THUMBS_DIR / f"{base_name}.jpg"
            thumb_img.save(thumbs_jpg, 'JPEG', quality=JPG_QUALITY, optimize=True)
            print(f"   ✓ thumbs/{base_name}.jpg ({thumb_width} × {thumb_height} px, {thumbs_jpg.stat().st_size // 1024} KB)")
            
            # AVIF
            thumbs_avif = THUMBS_DIR / f"{base_name}.avif"
            thumb_img.save(thumbs_avif, 'AVIF', quality=AVIF_QUALITY)
            print(f"   ✓ thumbs/{base_name}.avif ({thumbs_avif.stat().st_size // 1024} KB)")
            
            # 3. TINY / LQIP (sehr klein für Blur-Placeholder)
            tiny_ratio = TINY_MAX_HEIGHT / original_height
            tiny_width = max(1, int(original_width * tiny_ratio))
            tiny_height = max(1, int(original_height * tiny_ratio))
            
            tiny_img = img.resize((tiny_width, tiny_height), Image.LANCZOS)
            
            # JPG (kein AVIF nötig für so kleine Bilder)
            tiny_jpg = TINY_DIR / f"{base_name}.jpg"
            tiny_img.save(tiny_jpg, 'JPEG', quality=JPG_QUALITY, optimize=True)
            print(f"   ✓ tiny/{base_name}.jpg ({tiny_width} × {tiny_height} px, {tiny_jpg.stat().st_size // 1024} KB)")
            
        print(f"✅ {base_name}: Fertig!")
        return True
        
    except Exception as e:
        print(f"❌ Fehler bei {base_name}: {e}")
        return False


def find_unconverted_images() -> list:
    """Findet alle Bilder in images/ die noch nicht konvertiert wurden."""
    unconverted = []
    
    for path in IMAGES_DIR.iterdir():
        if not path.is_file():
            continue
        if path.suffix.lower() not in ['.jpg', '.jpeg', '.png']:
            continue
        
        base_name = path.stem
        
        # Prüfen ob alle Varianten existieren
        has_all = (
            (COMPRESSED_DIR / f"{base_name}.avif").exists() and
            (COMPRESSED_DIR / f"{base_name}.jpg").exists() and
            (THUMBS_DIR / f"{base_name}.avif").exists() and
            (THUMBS_DIR / f"{base_name}.jpg").exists() and
            (TINY_DIR / f"{base_name}.jpg").exists()
        )
        
        if not has_all:
            unconverted.append(path)
    
    return unconverted


def main():
    parser = argparse.ArgumentParser(
        description="Konvertiert Bilder für susanneuhl.github.io",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
    python scripts/convert_image.py neues-projekt.jpg
    python scripts/convert_image.py images/neues-projekt.jpg
    python scripts/convert_image.py --all
    python scripts/convert_image.py --all --force
        """
    )
    parser.add_argument('image', nargs='?', help='Bildname oder Pfad zum Bild')
    parser.add_argument('--all', action='store_true', help='Alle nicht-konvertierten Bilder verarbeiten')
    parser.add_argument('--force', action='store_true', help='Bestehende Dateien überschreiben')
    parser.add_argument('--list', action='store_true', help='Nicht-konvertierte Bilder auflisten')
    
    args = parser.parse_args()
    
    # Verzeichnisse erstellen
    ensure_dirs()
    
    if args.list:
        unconverted = find_unconverted_images()
        if unconverted:
            print(f"Nicht konvertierte Bilder ({len(unconverted)}):")
            for path in unconverted:
                print(f"  - {path.name}")
        else:
            print("Alle Bilder sind bereits konvertiert.")
        return
    
    if args.all:
        unconverted = find_unconverted_images()
        if not unconverted:
            print("Alle Bilder sind bereits konvertiert.")
            if args.force:
                print("Mit --force werden alle Bilder neu konvertiert...")
                unconverted = [p for p in IMAGES_DIR.iterdir() 
                              if p.is_file() and p.suffix.lower() in ['.jpg', '.jpeg', '.png']]
        
        if unconverted:
            print(f"\nKonvertiere {len(unconverted)} Bilder...\n")
            success = 0
            for path in sorted(unconverted):
                if convert_image(path, force=args.force):
                    success += 1
                print()
            print(f"\n{'='*40}")
            print(f"Fertig: {success}/{len(unconverted)} Bilder konvertiert")
        return
    
    if not args.image:
        parser.print_help()
        print("\n❌ Fehler: Bitte Bildname angeben oder --all verwenden")
        sys.exit(1)
    
    source_path = get_image_path(args.image)
    success = convert_image(source_path, force=args.force)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

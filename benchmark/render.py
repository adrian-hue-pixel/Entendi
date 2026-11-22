"""Render synthetic notices with explicit script-appropriate fonts."""

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from benchmark.generate import OUT

CJK = {"zh": "SC", "ja": "JP", "ko": "KR"}


def font_for(lang, size, font_dir):
    all_fonts = tuple(font_dir.rglob("*")) if font_dir.exists() else ()
    if lang in CJK:
        tag = CJK[lang]
        path = next((p for p in all_fonts if p.name == f"NotoSansCJK{tag}-Regular.otf"), None)
        if path:
            return ImageFont.truetype(str(path), size)
        ttc = next((p for p in all_fonts if p.name == "NotoSansCJK-Regular.ttc"), None)
        if ttc:
            return ImageFont.truetype(str(ttc), size, index={"JP": 0, "KR": 1, "SC": 2}[tag])
        raise FileNotFoundError(f"Install Noto Sans CJK for {lang}, or pass its directory with --fonts.")
    if lang == "th":
        path = next((p for p in all_fonts if p.name in {"NotoSansThai-Regular.ttf", "NotoSansThai-Regular.otf"}), None)
        if not path:
            raise FileNotFoundError("Install Noto Sans Thai, or pass its directory with --fonts.")
        return ImageFont.truetype(str(path), size)
    return ImageFont.load_default(size=size)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--fonts", type=Path, default=Path("/usr/share/fonts"))
    parser.add_argument("--language", choices=("en", "es", "fr", "de", "zh", "ja", "th"), action="append")
    args = parser.parse_args()
    requested = set(args.language or ("en", "es", "fr", "de", "zh", "ja"))
    args.out.mkdir(parents=True, exist_ok=True)
    rows = (json.loads(line) for line in OUT.read_text(encoding="utf-8").splitlines())
    for row in rows:
        if row["language"] not in requested:
            continue
        surface = Image.new("RGB", (1240, 860), "#fdfcf8")
        draw = ImageDraw.Draw(surface)
        font = font_for(row["language"], 38, args.fonts)
        draw.text((72, 72), "ENTENDI  ·  SYNTHETIC NOTICE", fill="#47396b", font=ImageFont.load_default(size=30))
        draw.line((72, 145, 1170, 145), fill="#aaa5ad", width=2)
        for i, line in enumerate(row["text"].splitlines()):
            draw.text((72, 190 + 85 * i), line, fill="#17141d", font=font)
        surface.save(args.out / f"{row['id']}.jpg", quality=94)


if __name__ == "__main__":
    main()

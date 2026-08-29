#!/usr/bin/env python3
"""Maintenance utility: extract the bundled palette cards into a JSON catalog."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image

from star_palette import LAYOUTS, normalized_samples, rgb_to_hex


CLASSIC_01 = [
    (3, 3, 3),
    (21, 33, 63),
    (250, 163, 21),
    (229, 229, 229),
]


def color_records(colors):
    return [{"hex": rgb_to_hex(color), "rgb": list(color)} for color in colors]


def extract_genshin(path):
    image = Image.open(path).convert("RGB")
    layout = "genshin-landscape-9" if image.height < 800 else "genshin-portrait-5"
    return normalized_samples(image, LAYOUTS[layout])


def extract_classic(path):
    image = Image.open(path).convert("RGB")
    return normalized_samples(image, LAYOUTS["classic-7"])


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--palette-root", type=Path, default=Path("StarPalette/ref"))
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("StarPalette/references/palette_catalog.json"),
    )
    return parser.parse_args()


def main():
    args = parse_args()
    root = args.palette_root.resolve()

    genshin = []
    for path in sorted((root / "Genshin_palette_19").glob("*.jpg")):
        genshin.append(
            {
                "id": path.stem,
                "colors": color_records(extract_genshin(path)),
                "source": f"Genshin_palette_19/{path.name}",
            }
        )

    classic = [
        {
            "id": "01",
            "colors": color_records(CLASSIC_01),
            "source": "Classic_palette_30 overview card No.001",
        }
    ]
    for path in sorted((root / "Classic_palette_30").glob("*.png")):
        classic.append(
            {
                "id": path.stem,
                "colors": color_records(extract_classic(path)),
                "source": f"Classic_palette_30/{path.name}",
            }
        )

    catalog = {
        "schema_version": 1,
        "description": "Extracted StarPalette swatches; normal variant generation does not require the source images.",
        "families": [
            {"id": "genshin", "count": len(genshin), "palettes": genshin},
            {"id": "classic", "count": len(classic), "palettes": classic},
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(catalog, indent=2), encoding="utf-8")
    print(f"Wrote {len(genshin)} + {len(classic)} palettes to {args.output}")


if __name__ == "__main__":
    main()

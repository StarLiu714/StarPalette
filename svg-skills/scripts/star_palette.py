#!/usr/bin/env python3
"""Generate SVG color variants from palette-card images.

The script is intentionally configuration-driven. It samples palette cards,
maps known source SVG colors to palette roles, preserves selected SVG groups,
renders PNG previews when `sips` is available, and builds a contact sheet.
"""

from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from statistics import median

from PIL import Image, ImageDraw, ImageFont


SVG_NS = "http://www.w3.org/2000/svg"
XLINK_NS = "http://www.w3.org/1999/xlink"
ET.register_namespace("", SVG_NS)
ET.register_namespace("xlink", XLINK_NS)


def rgb_to_hex(color):
    return "#%02X%02X%02X" % tuple(max(0, min(255, round(v))) for v in color)


def hex_to_rgb(value):
    value = value.lstrip("#")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))


def mix(color, other, amount):
    return tuple(color[i] * (1 - amount) + other[i] * amount for i in range(3))


def tint(color, amount):
    return mix(color, (255, 255, 255), amount)


def shade(color, amount):
    return mix(color, (0, 0, 0), amount)


def luminance(color):
    def channel(value):
        value = value / 255
        return value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4

    r, g, b = (channel(v) for v in color)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def sample_patch(image, x, y, radius=10):
    pixels = []
    for yy in range(max(0, y - radius), min(image.height, y + radius + 1)):
        for xx in range(max(0, x - radius), min(image.width, x + radius + 1)):
            pixels.append(image.getpixel((xx, yy))[:3])
    return tuple(int(median([pixel[i] for pixel in pixels])) for i in range(3))


def normalized_samples(image, coordinates):
    return [
        sample_patch(image, round(image.width * x), round(image.height * y))
        for x, y in coordinates
    ]


LAYOUTS = {
    "classic-7": [(x, 0.25) for x in (0.065, 0.204, 0.347, 0.490, 0.630, 0.773, 0.920)],
    "genshin-landscape-9": [
        (x, 0.18) for x in (0.441, 0.502, 0.565, 0.625, 0.686, 0.747, 0.809, 0.870, 0.931)
    ],
    "genshin-portrait-5": [(x, 0.79) for x in (0.086, 0.261, 0.437, 0.612, 0.787)],
}


def extract_palette(path, source_spec):
    image = Image.open(path).convert("RGB")
    layout = source_spec.get("layout", "normalized")
    if layout == "genshin-auto":
        layout = "genshin-landscape-9" if image.height < 800 else "genshin-portrait-5"
    if layout == "normalized":
        coordinates = source_spec["samples"]
    else:
        if layout not in LAYOUTS:
            raise ValueError(f"Unknown palette layout: {layout}")
        coordinates = LAYOUTS[layout]
    return normalized_samples(image, coordinates)


def palette_color(spec, colors):
    selector = spec.get("palette", 0)
    if selector == "darkest":
        color = min(colors, key=luminance)
    elif selector == "lightest":
        color = max(colors, key=luminance)
    else:
        color = colors[int(selector) % len(colors)]

    operation = spec.get("operation", "direct")
    amount = float(spec.get("amount", 0))
    if operation == "direct":
        return color
    if operation == "tint":
        return tint(color, amount)
    if operation == "shade":
        return shade(color, amount)
    if operation == "ink":
        return shade(color, 0.45 if luminance(color) > 0.18 else 0.08)
    raise ValueError(f"Unknown color operation: {operation}")


def build_mapping(config, colors):
    mapping = {}
    for rule in config["mappings"]:
        output = rgb_to_hex(palette_color(rule, colors)).upper()
        for source in rule["sources"]:
            mapping[source.upper()] = output
    return mapping


def group_signature(svg_root, group_id):
    for element in svg_root.iter():
        if element.attrib.get("id") == group_id:
            return [
                (
                    child.tag.split("}")[-1],
                    tuple(
                        sorted(
                            (key, value)
                            for key, value in child.attrib.items()
                            if key in {"fill", "stroke", "x", "y", "cx", "cy", "points", "d"}
                        )
                    ),
                    (child.text or "").strip(),
                )
                for child in element.iter()
            ]
    raise KeyError(f"Protected SVG group not found: {group_id}")


def recolor_svg(base_svg, output_svg, mapping, protected_ids):
    tree = ET.parse(base_svg)
    root = tree.getroot()

    def visit(element, protected=False):
        if protected or element.attrib.get("id") in protected_ids:
            return
        for attribute in ("fill", "stroke", "stop-color", "flood-color"):
            value = element.attrib.get(attribute)
            if value and value.upper() in mapping:
                element.attrib[attribute] = mapping[value.upper()]
        for child in element:
            visit(child, False)

    visit(root)
    tree.write(output_svg, encoding="utf-8", xml_declaration=True)


def render_png(svg_path, png_path, renderer):
    if renderer == "none":
        return False
    if renderer == "sips":
        executable = shutil.which("sips")
        if not executable:
            raise RuntimeError("The requested `sips` renderer is not available")
        subprocess.run(
            [executable, "-s", "format", "png", str(svg_path), "--out", str(png_path)],
            check=True,
            stdout=subprocess.DEVNULL,
        )
        return True
    raise ValueError(f"Unsupported renderer: {renderer}")


def font(size=18, bold=False):
    candidates = [
        Path("/System/Library/Fonts/Supplemental") / ("Arial Bold.ttf" if bold else "Arial.ttf"),
        Path("/usr/share/fonts/truetype/dejavu") / ("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"),
    ]
    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def contact_sheet(items, output_path, settings):
    if not items or not all(item.get("png") for item in items):
        return
    columns = int(settings.get("columns", 4))
    preview_width = int(settings.get("preview_width", 410))
    preview_height = int(settings.get("preview_height", 148))
    cell_width = preview_width + 20
    cell_height = preview_height + 42
    rows = math.ceil(len(items) / columns)
    sheet = Image.new("RGB", (columns * cell_width, rows * cell_height), "white")
    draw = ImageDraw.Draw(sheet)
    title_font = font(18, bold=True)

    for index, item in enumerate(items):
        col = index % columns
        row = index // columns
        x = col * cell_width
        y = row * cell_height
        preview = Image.open(item["png"]).convert("RGB")
        preview.thumbnail((preview_width, preview_height), Image.Resampling.LANCZOS)
        sheet.paste(preview, (x + 10, y + 28))
        draw.text((x + 10, y + 5), item["label"], font=title_font, fill="#111111")
        swatch_x = x + 225
        for color in item["colors"]:
            draw.rounded_rectangle(
                (swatch_x, y + 5, swatch_x + 18, y + 21), radius=3, fill=rgb_to_hex(color)
            )
            swatch_x += 22
    sheet.save(output_path)


def resolve(path_value, base):
    path = Path(path_value)
    return path if path.is_absolute() else (base / path).resolve()


def load_palette_catalog(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    entries = []
    for family in data["families"]:
        family_id = family["id"]
        for palette in family["palettes"]:
            colors = []
            for color in palette["colors"]:
                if isinstance(color, str):
                    colors.append(hex_to_rgb(color))
                elif "rgb" in color:
                    colors.append(tuple(color["rgb"]))
                else:
                    colors.append(hex_to_rgb(color["hex"]))
            entries.append(
                (
                    family_id,
                    str(palette["id"]),
                    palette.get("source", f"catalog:{family_id}/{palette['id']}"),
                    colors,
                )
            )
    return entries


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-svg", required=True, help="Source SVG to recolor")
    palette_input = parser.add_mutually_exclusive_group(required=True)
    palette_input.add_argument("--palette-catalog", help="JSON catalog containing extracted palette colors")
    palette_input.add_argument("--palette-root", help="Legacy mode: root directory containing palette-card images")
    parser.add_argument("--config", required=True, help="JSON mapping and palette-source configuration")
    parser.add_argument("--output-dir", required=True, help="Destination for generated variants")
    parser.add_argument("--renderer", choices=("sips", "none"), default="sips")
    return parser.parse_args()


def main():
    args = parse_args()
    cwd = Path.cwd()
    base_svg = resolve(args.base_svg, cwd)
    config_path = resolve(args.config, cwd)
    output_dir = resolve(args.output_dir, cwd)
    output_dir.mkdir(parents=True, exist_ok=True)

    config = json.loads(config_path.read_text(encoding="utf-8"))
    protected_ids = set(config.get("protected_group_ids", []))
    base_root = ET.parse(base_svg).getroot()
    locked = {group_id: group_signature(base_root, group_id) for group_id in protected_ids}

    if args.palette_catalog:
        palette_catalog = resolve(args.palette_catalog, cwd)
        palette_entries = load_palette_catalog(palette_catalog)
        palette_root = None
    else:
        palette_root = resolve(args.palette_root, cwd)
        palette_entries = []
        for source_spec in config["palette_sources"]:
            family = source_spec["family"]
            matches = sorted(palette_root.glob(source_spec["glob"]))
            if not matches:
                raise FileNotFoundError(f"No palette cards matched: {source_spec['glob']}")
            for path in matches:
                palette_entries.append((family, path.stem, path, extract_palette(path, source_spec)))

    manifest = []
    contact_items = []
    errors = []
    for family, number, source, colors in palette_entries:
        family_dir = output_dir / family
        family_dir.mkdir(parents=True, exist_ok=True)
        stem = f"{family}_{number}"
        svg_path = family_dir / f"{stem}.svg"
        png_path = family_dir / f"{stem}.png"

        mapping = build_mapping(config, colors)
        recolor_svg(base_svg, svg_path, mapping, protected_ids)
        output_root = ET.parse(svg_path).getroot()
        for group_id, signature in locked.items():
            if group_signature(output_root, group_id) != signature:
                errors.append(f"{stem}: protected group changed: {group_id}")

        rendered = render_png(svg_path, png_path, args.renderer)
        label = f"{family.title()} {number}"
        contact_items.append(
            {"label": label, "png": png_path if rendered else None, "colors": colors}
        )
        manifest.append(
            {
                "family": family,
                "number": number,
                "source": str(source.relative_to(palette_root)) if palette_root is not None else str(source),
                "colors": [rgb_to_hex(color) for color in colors],
                "svg": str(svg_path.relative_to(output_dir)),
                "png": str(png_path.relative_to(output_dir)) if rendered else None,
            }
        )

    if errors:
        raise RuntimeError("\n".join(errors))

    (output_dir / "palettes.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    if args.renderer != "none":
        contact_sheet(
            contact_items,
            output_dir / "contact_sheet.png",
            config.get("contact_sheet", {}),
        )
    print(f"Generated {len(manifest)} variants in {output_dir}")


if __name__ == "__main__":
    main()

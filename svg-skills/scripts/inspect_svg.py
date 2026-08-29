#!/usr/bin/env python3
"""Inspect an SVG and emit a draft StarPalette mapping configuration.

The draft is a starting point, not a semantic decision. Review component roles,
merge related fill/outline/token colors, and add protected group IDs before use.
"""

from __future__ import annotations

import argparse
import json
import re
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path


HEX_COLOR = re.compile(r"^#[0-9A-Fa-f]{6}$")


def hex_to_rgb(value):
    value = value.lstrip("#")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))


def luminance(value):
    r, g, b = hex_to_rgb(value)

    def channel(v):
        v = v / 255
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4

    r, g, b = (channel(v) for v in (r, g, b))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--svg", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--protect-id", action="append", default=[])
    return parser.parse_args()


def main():
    args = parse_args()
    root = ET.parse(args.svg).getroot()
    counts = Counter()
    attributes = defaultdict(Counter)
    tags = defaultdict(Counter)
    group_ids = []

    def visit(element, protected=False):
        group_id = element.attrib.get("id")
        if group_id:
            group_ids.append(group_id)
        if protected or group_id in set(args.protect_id):
            return
        tag = element.tag.split("}")[-1]
        for attribute in ("fill", "stroke", "stop-color", "flood-color"):
            value = element.attrib.get(attribute)
            if value and HEX_COLOR.match(value):
                value = value.upper()
                counts[value] += 1
                attributes[value][attribute] += 1
                tags[value][tag] += 1
        for child in element:
            visit(child, False)

    visit(root)
    ordered = [color for color, _ in counts.most_common()]
    draft_rules = []
    palette_index = 0
    for color in ordered:
        lum = luminance(color)
        usage = attributes[color]
        text_or_line = tags[color]["text"] + tags[color]["polyline"] + tags[color]["line"] + tags[color]["path"]
        if lum < 0.28 and text_or_line:
            palette = "darkest"
            operation = "ink"
            amount = None
        elif usage["fill"] and lum > 0.72:
            palette = palette_index
            operation = "tint"
            amount = 0.82
            palette_index += 1
        elif usage["stroke"]:
            palette = palette_index
            operation = "shade"
            amount = 0.1
            palette_index += 1
        else:
            palette = palette_index
            operation = "direct"
            amount = None
            palette_index += 1

        rule = {
            "sources": [color],
            "palette": palette,
            "operation": operation,
            "observed": {
                "count": counts[color],
                "attributes": dict(usage),
                "elements": dict(tags[color]),
            },
        }
        if amount is not None:
            rule["amount"] = amount
        draft_rules.append(rule)

    config = {
        "protected_group_ids": args.protect_id,
        "contact_sheet": {
            "columns": 4,
            "preview_width": 410,
            "preview_height": 148,
        },
        "mappings": draft_rules,
        "analysis": {
            "source_svg": str(args.svg),
            "group_ids_found": sorted(set(group_ids)),
            "instructions": [
                "Review every rule before generation.",
                "Merge fill/outline colors that belong to the same semantic role.",
                "Merge repeated token colors that must remain consistent.",
                "Add semantically fixed regions to protected_group_ids.",
                "Move globally recolored titles outside protected groups.",
            ],
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(config, indent=2), encoding="utf-8")

    print(f"Found {len(ordered)} literal colors and {len(set(group_ids))} group IDs")
    print(f"Draft mapping written to {args.output}")
    for color in ordered:
        print(f"{color} count={counts[color]} attrs={dict(attributes[color])} tags={dict(tags[color])}")


if __name__ == "__main__":
    main()

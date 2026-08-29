# Star-Palette-svg

`Star-Palette-svg` 是 StarPalette 项目下的 SVG 批量配色 skill。它面向结构化 SVG：先识别图中的语义颜色角色，再用内置或外置色卡批量生成候选版本。

## 环境要求

- Python 3.9 或更高版本
- Pillow
- macOS 上可使用 `sips` 将 SVG 渲染为 PNG

如果环境中没有 `sips`，可以使用 `--renderer none` 仅生成 SVG。

## 主要文件

```text
svg-skills/
├── SKILL.md
├── agents/
│   └── openai.yaml
├── scripts/
│   ├── star_palette.py
│   ├── inspect_svg.py
│   └── extract_palette_catalog.py
└── references/
    ├── palette_catalog.json
    ├── mapping-template.json
    ├── adapting-to-new-svg.md
    ├── configuration.md
    ├── palette-card-layouts.md
    └── validation.md
```

## Workflow

1. Render and inspect the source SVG. Do not reuse mappings from a previous figure without re-analysis.
2. Use the inspector to create a draft config and color report:

   ```bash
   python3 StarPalette/svg-skills/scripts/inspect_svg.py \
     --svg /path/to/new-figure.svg \
     --output /path/to/mapping-draft.json
   ```

3. Review the draft semantically:

   - merge fill/outline colors that belong to the same module;
   - merge repeated token roles that must stay visually consistent;
   - identify global text, arrows, accents, and fixed regions;
   - remove unused definition colors.

4. Wrap fixed regions in unique SVG groups such as `<g id="locked-brand-region">`.
5. Finalize the mapping config.
6. Generate variants:

   ```bash
   python3 StarPalette/svg-skills/scripts/star_palette.py \
     --base-svg /path/to/figure.svg \
     --palette-catalog StarPalette/svg-skills/references/palette_catalog.json \
     --config /path/to/mapping-config.json \
     --output-dir /path/to/palette-variants
   ```

7. Review `contact_sheet.png` and representative full-size SVGs.
8. Validate protected groups, XML correctness, contrast, and token consistency.

For the complete adaptation prompt, see [`references/adapting-to-new-svg.md`](references/adapting-to-new-svg.md).

## Mapping Config

The config separates SVG-specific decisions from reusable palette sampling.

```json
{
  "protected_group_ids": ["fixed-brand-region"],
  "mappings": [
    {
      "sources": ["#001B4D", "#0B2A66"],
      "palette": "darkest",
      "operation": "ink"
    },
    {
      "sources": ["#EAF2FF"],
      "palette": 0,
      "operation": "tint",
      "amount": 0.84
    }
  ]
}
```

`palette` can be an integer index, `darkest`, or `lightest`.

`operation` can be:

- `direct`: use the sampled swatch directly;
- `tint`: mix toward white, usually for large fills;
- `shade`: mix toward black, usually for outlines and emphasis;
- `ink`: derive a readable dark foreground.

For the full schema, see [`references/configuration.md`](references/configuration.md).

## Protected Regions

For areas that must not change, add a unique group ID in the source SVG:

```svg
<g id="fixed-brand-region">
  ...
</g>
```

Then list the ID in config:

```json
{
  "protected_group_ids": ["fixed-brand-region"]
}
```

The generator skips that subtree and compares the protected group after generation.

If a title should follow the global text color, keep the title outside the protected group even when the module graphic itself is fixed.

## Token Consistency

StarPalette allows token colors to change across palettes, but the same semantic token must stay consistent inside one generated figure. If two elements should share a token role, give them the same literal source color or put their source colors in the same mapping rule.

## External Palette Cards

External palette cards can be sampled directly with `--palette-root`. Put the images under the palette root:

```text
StarPalette/ref/my_palette_family/
├── 01.png
├── 02.png
└── 03.png
```

Add a `palette_sources` block to the config:

```json
{
  "palette_sources": [
    {
      "family": "my_palette_family",
      "glob": "my_palette_family/*.png",
      "layout": "normalized",
      "samples": [[0.12, 0.25], [0.32, 0.25], [0.52, 0.25], [0.72, 0.25]]
    }
  ]
}
```

Run:

```bash
python3 StarPalette/svg-skills/scripts/star_palette.py \
  --base-svg /path/to/figure.svg \
  --palette-root StarPalette/ref \
  --config /path/to/mapping-config.json \
  --output-dir /path/to/palette-variants
```

See [`references/palette-card-layouts.md`](references/palette-card-layouts.md) before adding a new layout.

## Built-In Catalog Maintenance

Normal generation should use:

```text
svg-skills/references/palette_catalog.json
```

The archived cards under `ref/` are only needed when rebuilding the built-in catalog:

```bash
python3 StarPalette/svg-skills/scripts/extract_palette_catalog.py \
  --palette-root StarPalette/ref \
  --output StarPalette/svg-skills/references/palette_catalog.json
```

The current maintenance extractor is tailored to the bundled Genshin and Classic card families. For new external families, use `--palette-root` directly or add a dedicated extractor once the card layout is stable.

## Outputs

The generator writes:

- one SVG per palette;
- optional PNG previews via `sips`;
- `palettes.json` with extracted swatches and output paths;
- `contact_sheet.png` for visual comparison.

## Validation

Check at least:

1. The number of generated SVGs matches the selected palette source.
2. All generated SVGs parse as XML.
3. Protected regions remain unchanged.
4. Text and arrows stay readable on very light and very dark palettes.
5. Repeated token roles stay consistent.
6. The contact sheet has no obviously washed-out, over-saturated, or semantically confusing variants.

Detailed checks are in [`references/validation.md`](references/validation.md).

## Finalist Overrides

Generate broad palette candidates first. Apply finalist-only tweaks afterward with a small deterministic script, and update the general mapping only when the change should affect every generated palette.

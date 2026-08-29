---
name: star-palette-svg
description: Generate and review batches of SVG color variants from extracted palette catalogs or palette-card images while preserving protected semantic regions. Use for scientific figures, diagrams, and other structured SVGs that need many palette trials, PNG previews, contact sheets, or deterministic finalist overrides; do not use for raster-only artwork or a single trivial color edit.
---

# Star-Palette-svg

Generate non-destructive SVG palette variants from any structured SVG and an extracted palette catalog.

## Required inputs

- A valid source SVG.
- A palette JSON catalog, normally `references/palette_catalog.json`.
- A JSON mapping configuration.
- A separate output directory.
- The IDs of SVG groups whose colors must not change.

## Workflow

1. Render and inspect the new source SVG. Do not reuse mappings from a previous figure without re-analysis. Identify:
   - global foreground colors;
   - module fill/outline pairs;
   - repeated semantic token colors;
   - embedded raster images;
   - regions that must remain fixed.
2. Run the SVG inspector to create a draft config and color-usage report:

   ```bash
   python3 scripts/inspect_svg.py \
     --svg /path/to/figure.svg \
     --output /path/to/mapping-draft.json
   ```

3. Review the draft semantically. Merge related fill/outline colors, merge repeated token roles, and choose protected regions. Read [references/adapting-to-new-svg.md](references/adapting-to-new-svg.md) for the complete adaptation workflow and reusable prompt.
4. Wrap fixed regions in unique SVG groups such as `<g id="locked-brand-region">`. Keep titles outside a protected group when they should follow the global foreground color.
5. Use the committed palette catalog for normal generation. Read [references/palette-card-layouts.md](references/palette-card-layouts.md) only when adding or re-extracting a card family.
6. Finalize the mapping config. Use light tints for large fills, stronger swatches for outlines, and the darkest suitable swatch for text/arrows. Read [references/configuration.md](references/configuration.md) for the schema and neutral template.
7. Generate variants with the bundled script:

   ```bash
     python3 scripts/star_palette.py \
       --base-svg /path/to/figure.svg \
       --palette-catalog references/palette_catalog.json \
       --config /path/to/mapping-config.json \
       --output-dir /path/to/palette-variants
   ```

8. Review the generated contact sheet, then inspect representative full-size variants.
9. Validate protected groups, token consistency, XML correctness, and contrast. Use [references/validation.md](references/validation.md).
10. Apply finalist-only overrides after batch generation with a deterministic script; do not mutate the general mapping unless the change should affect every palette.

## Invariants

- Never overwrite the source SVG.
- Never assume that literal colors have the same semantic role across different SVGs.
- Never recolor a protected group or embedded raster image unless the user explicitly requests it.
- Repeated token meanings must retain the same fill and stroke within each variant.
- Palette changes may alter token colors, but not their semantic consistency.
- Preserve geometry, text, arrows, and layout unless the user asks for structural edits.
- Derive readable fills and outlines rather than assigning saturated swatches indiscriminately.
- If a palette produces insufficient foreground contrast, darken its foreground role instead of changing the protected regions.

## Bundled palette catalog

`references/palette_catalog.json` contains 19 Genshin palettes and 30 Classic palettes as explicit hex/RGB values. Normal generation does not read `ref/` images. The cards under `ref/` are archival sources used only when maintaining the catalog with `scripts/extract_palette_catalog.py`.

## Outputs

The script writes:

- one SVG per palette;
- optional PNG previews via `sips`;
- `palettes.json` with extracted swatches and output paths;
- `contact_sheet.png` for visual comparison.

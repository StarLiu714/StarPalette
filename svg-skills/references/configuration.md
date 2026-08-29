# StarPalette configuration

Use a JSON mapping configuration to separate SVG-specific semantic decisions from the reusable batch engine. Palette values normally come from [palette_catalog.json](palette_catalog.json), not from image files.

## Top-level fields

### `protected_group_ids`

SVG `<g id="...">` subtrees that must remain byte-for-byte equivalent in color and geometry. Put embedded raster images and semantically fixed modules inside protected groups. Keep any text that should follow the global palette outside those groups.

### `palette_sources` — maintenance/legacy mode

Each entry defines one family of palette cards:

```json
{
  "family": "classic",
  "glob": "Classic_palette_30/*.png",
  "layout": "classic-7"
}
```

Supported layouts:

- `classic-7`
- `genshin-auto`
- `genshin-landscape-9`
- `genshin-portrait-5`
- `normalized`, with an explicit `samples` array of normalized `[x, y]` coordinates

This field is ignored when `--palette-catalog` is supplied. Keep it only when the same config must also support direct image-card extraction.

### `mappings`

Each rule maps one or more literal source SVG colors to a sampled palette role:

```json
{
  "sources": ["#001B4D", "#0B2A66"],
  "palette": "darkest",
  "operation": "ink"
}
```

`palette` accepts:

- an integer index, wrapped modulo the number of sampled colors;
- `darkest`;
- `lightest`.

`operation` accepts:

- `direct` — use the sampled swatch;
- `tint` — mix toward white by `amount`;
- `shade` — mix toward black by `amount`;
- `ink` — derive a readable dark foreground automatically.

Use one fill/outline pair per semantic role. Derive light fills with `tint` and stronger outlines with `shade`; do not apply saturated swatches directly to every surface.

### `contact_sheet`

Optional preview settings:

```json
{
  "columns": 4,
  "preview_width": 410,
  "preview_height": 148
}
```

## Token consistency

Map every occurrence of a semantic token color through the same source-color rule. For example, if `N` and masked commitment slots must match, give them the same literal source fill and stroke before generating variants, or list both source colors in the same mapping rule.

## Neutral template

Copy [mapping-template.json](mapping-template.json), replace its source colors with colors observed in the new SVG, and revise the role assignments after visual inspection. The template is illustrative and must not be applied unchanged to an unrelated SVG.

# Palette-card extraction

This reference is for maintaining [palette_catalog.json](palette_catalog.json). Normal variant generation reads the catalog and does not require palette-card images. When re-extracting cards, StarPalette samples swatches at normalized coordinates; use a built-in layout only when the template matches.

## Built-in layouts

### `classic-7`

Seven horizontal swatches near the top of a wide card. This matches `ref/Classic_palette_30/`.

### `genshin-auto`

Selects one of two templates by image height:

- landscape cards: nine horizontal swatches;
- portrait cards: five swatches near the lower part of the card.

This matches `ref/Genshin_palette_19/`.

## Adding a custom template

Inspect several cards from the family, choose the center of each swatch, divide coordinates by the image width and height, and add them as normalized samples:

```json
{
  "family": "custom",
  "glob": "custom/*.png",
  "layout": "normalized",
  "samples": [[0.10, 0.20], [0.30, 0.20], [0.50, 0.20]]
}
```

Sample the interior of a swatch, not its rounded border, label, shadow, or anti-aliased edge. Test the first and last card in a family before starting a large batch.

## Extraction validation

Always inspect `palettes.json` and the swatches printed above each contact-sheet preview. A wrong coordinate usually produces white, black, skin tone, or illustration colors that do not match the printed reference swatches.

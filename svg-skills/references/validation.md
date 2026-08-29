# Validation checklist

## Before generation

- Validate the source SVG with an XML parser.
- Confirm that every protected region is wrapped in a uniquely named `<g id="...">`.
- Move any title that should follow the global foreground color outside the protected group.
- Record the exact source colors used for each semantic role.
- Ensure repeated token meanings use the same source fill and stroke.

## After generation

- Confirm the expected number of SVGs and PNGs.
- Parse every generated SVG.
- Compare each protected-group signature with the source SVG.
- Check foreground/background contrast in the darkest and lightest palettes.
- Inspect one warm, one cool, one low-saturation, and one high-saturation variant at full size.
- Verify token consistency across inputs, intermediate states, and outputs.
- Check that raster images embedded in the SVG were not recolored.
- Review the contact sheet before selecting finalists.

## Selection overrides

Apply finalist-specific overrides only after batch generation. Keep them in a deterministic script, regenerate their PNG previews, and record exact colors. Do not silently fold one finalist override into every palette unless it is a global design rule.

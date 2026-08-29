# Adapting StarPalette to a new SVG

Every SVG has its own semantic color system. Treat the existing mapping as an example of the workflow, not a reusable answer.

## 1. Inspect the figure

Render the SVG at its intended size and identify:

- primary text and arrow colors;
- module outlines and their corresponding light fills;
- accent modules;
- dashed section boundaries;
- repeated token or legend colors;
- embedded raster images;
- colors that encode fixed scientific, brand, or categorical meaning.

Do not decide from hex values alone. Two identical colors may be reused accidentally for unrelated roles, while two different colors may represent the same semantic role.

## 2. Inspect literal SVG colors

Generate a draft report:

```bash
python3 scripts/inspect_svg.py \
  --svg /path/to/new-figure.svg \
  --output /path/to/mapping-draft.json
```

If fixed groups already have IDs, pass them repeatedly:

```bash
python3 scripts/inspect_svg.py \
  --svg /path/to/new-figure.svg \
  --protect-id fixed-logo \
  --protect-id semantic-legend \
  --output /path/to/mapping-draft.json
```

The generated mapping is intentionally provisional. It records color counts, attributes, and element types to support review.

## 3. Add or revise protected groups

Wrap fixed regions in explicit groups:

```svg
<g id="fixed-logo">
  ...
</g>
```

Protect the smallest complete semantic region. Do not protect a title if it should follow the global text palette; place that title outside the protected group.

Embedded raster images are not recolored by the XML color mapper, but grouping them still makes the invariant explicit and testable.

## 4. Convert observed colors into semantic roles

Edit the draft configuration:

- merge global text and arrow colors into one `ink` rule when appropriate;
- pair each module outline with its light fill;
- map large fills with `tint` and outlines with `shade`;
- group every repeated token meaning into a consistent rule;
- keep unrelated roles separate even if their source colors happen to match;
- remove colors belonging only to unused SVG definitions;
- add colors embedded in `style` attributes only after confirming the engine can address them, or normalize them into regular attributes first.

Use [mapping-template.json](mapping-template.json) as a structural example only.

## 5. Test before the full batch

Create a temporary catalog containing a small, diverse subset:

- one dark palette;
- one pale palette;
- one warm palette;
- one cool palette.

Generate and inspect those variants first. Fix contrast or semantic inconsistencies in the mapping config, then run the complete catalog.

## 6. Validate invariants

Use [validation.md](validation.md). In particular:

- compare protected-group signatures;
- confirm token consistency;
- inspect main-text contrast;
- verify that layout and geometry did not change;
- check titles adjacent to protected groups;
- ensure every output SVG parses successfully.

## Reusable model prompt

```text
Use $star-palette-svg on <SOURCE_SVG> with <PALETTE_CATALOG>.
First render and inspect the SVG. Run scripts/inspect_svg.py to create a draft mapping.
Identify global ink, module fill/outline pairs, accents, repeated token roles,
embedded rasters, and semantically fixed regions. Add explicit protected group IDs.
Do not copy mappings or protected IDs from a previous figure. Refine the draft config,
test a dark/pale/warm/cool subset, then generate the full SVG/PNG batch and contact sheet.
Validate protected groups, token consistency, XML correctness, and contrast.
```

## Common failure modes

- Reusing a previous figure's source hex values without inspecting the new SVG.
- Protecting a whole section when only one icon or module must stay fixed.
- Leaving a globally recolored title inside a protected group.
- Recoloring every shape directly with saturated swatches instead of deriving fills.
- Assigning different colors to repeated instances of the same token meaning.
- Trusting the automatically drafted config without visual review.

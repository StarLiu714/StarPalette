# StarPalette

输入一份画好layout的会议论文主图，给出49份经典配色方案。
目前支持的输入格式 `.svg`；
即将支持matplotlib和`.ai`，敬请期待。
<br>
Given a conference-style figure layout, **StarPalette** generates 49 ready-to-use re-colored variants.
We currently supported `.svg` input;
matplotlib diagrams *coming soon*.


## 内置色卡

Skills已经内置49套经典配色，已经结构化存储在<br>
49 built-in hierarchical palettes are located at:
```text
svg-skills/references/palette_catalog.json
```

来源详见[30+19套色卡](ref/)。<br>
See [30+19 palette sources](ref/) for the original references.

### (Optional)自定义配置色卡

若要初始化自定义色卡，请首先将图片文件(e.g.: `.png`,`.jpg`) 放进 `ref/` 下的独立目录
<br>
To customize palettes, place the palette images (e.g. `.png`, `.jpg`) in a directory under `ref/`:
```text
StarPalette/ref/my_palette/
├── 01.png
├── 02.png
└── ...
```

在 mapping config 中增加 `palette_sources`，用 `glob` 指向图片，并用 layout 或归一化采样点初始化取色<br>
Then, add `palette_sources` to the mapping config, use `glob` to link the images, and initialize color samples with either a layout or normalized samples:
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

然后用自定义色卡根目录运行<br>
Then, generate with the custom palette root dir via:
```bash
python3 StarPalette/svg-skills/scripts/star_palette.py \
  --base-svg /path/to/figure.svg \
  --palette-root StarPalette/ref \
  --config /path/to/figure-mapping.json \
  --output-dir /path/to/palette-variants
```

自定义版式可使用 `normalized` + `samples`。
更多维护细节见 [`svg-skills/references/palette-card-layouts.md`](svg-skills/references/palette-card-layouts.md)。<br>
Custom layouts can use `normalized` + `samples`.
For more maintenance details, see [`svg-skills/references/palette-card-layouts.md`](svg-skills/references/palette-card-layouts.md).


## SVG 配色 Skills

`star-palette-svg`核心实现<br>
The core implementation of `star-palette-svg`:

- 先分组 `.SVG` 矢量图当中的色块<br>
First, groups colors in the `.SVG` vector figure:
  - 语义角色，e.g. 文字、箭头、模块填充、模块描边、token等<br>
  semantic roles, e.g. text, arrows, module fills, outlines, tokens, etc.
  - 锁定区域，e.g. 需要全图一致表示的某种type的大分子、modulation、迭代操作等<br>
  fixed color-module pairs, e.g. macro-molecule types, modulations, iterative strategies, or other consistency-sensitive components across the figure
- 再把这些角色映射到色卡中的 swatches <br>
  Then maps these roles to swatches in the palette.

因此, 给定一份figure layout，可以通过这份skills一条prompt给出数十套配色方案，同时保留原有结构和语义一致性。<br>
From one layout, the skills give tens of ready-to-use re-colored variants (by concise instructions) while preserving the structural and semantic consistency.


## Quick Start

To generate ready-to-use recolored variants:

```bash
python3 StarPalette/svg-skills/scripts/star_palette.py \
  --base-svg /path/to/figure.svg \
  --palette-catalog StarPalette/svg-skills/references/palette_catalog.json \
  --config /path/to/figure-mapping.json \
  --output-dir /path/to/palette-variants
```

`figure-mapping.json` 具体说明源 SVG 当中的部分组件应跟随哪些色卡角色。
配置细节见 [`svg-skills/README.md`](svg-skills/README.md)。
<br>
`figure-mapping.json` specifies which components in the source SVG should follow which palette roles.
For configuration details, see [`svg-skills/README.md`](svg-skills/README.md).



## Usage in Codex

`svg-skills/` 模块作为已封装的独立 Codex Skill 加载，调用名 <br>
The `svg-skills/` module is packaged as an independent Codex Skill, with the invocation name:
```bash
$star-palette-svg
```

## 色卡来源与版权 Copyrights

内置参考色卡的来源、链接与版权说明保存在 [`ref/README.md`](ref/README.md)。
仅作为来源存档和**非商业学习**研究参考; 使用者应自行遵守原作者及发布平台的授权要求。<br>
The sources, links, and copyright notes for the built-in reference palettes are kept in [`ref/README.md`](ref/README.md).
They are provided only as source archives and for **non-commercial study** and research; 
users should follow the license of the original authors and publishers.

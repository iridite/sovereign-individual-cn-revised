# Clean Source Layer

This directory contains a normalized, ETL-ready source layer extracted from the Chinese LaTeX edition under `tex-zh/`.

## What This Keeps

- chapter, section, and subsection hierarchy
- body paragraphs
- quotation blocks from `tcolorbox`
- footnotes
- links
- ordered and unordered lists
- semantic emphasis
  - `\textbf{...}` -> `**...**`
  - `\uline{...}` -> `**...**`

## What This Drops

- cover layout, copyright-page decoration, and CIP page styling
- page-break commands and page-number logic
- font switches such as `\kaishu`
- TikZ ornaments, box skins, geometry, and print-only spacing
- print-only title-page composition details

## What This Normalizes

- forced line breaks inside headings become single-line headings
- `tcolorbox` quote panels become Markdown blockquotes
- `\footnote{...}` becomes Markdown footnotes with stable per-file IDs
- simple inline math wrappers such as `$ 4 \times 2 $` become plain text like `4 × 2`
- signature blocks such as author/date flush-right areas become plain lines

## Source Families

- `primary/`
  - canonical clean extraction from `tex-zh/maincontents/*.tex`, in the same reading order as `tex-zh/main.tex`
- `book.md`
  - one-file concatenation of the normalized primary text
- `manifest.json`
  - structural inventory for downstream ETL
  - includes per-section counts and an inventory of the secondary Markdown mirror under `tex-zh/md-files`

## Source Authority

- The LaTeX composition under `tex-zh/maincontents/` is treated as the authoritative source for normalized output.
- The Markdown files under `tex-zh/md-files/` are treated as a secondary mirror or auxiliary source for cross-checking.
- `原书评.md`, `README.md`, and `end2.md` exist in the secondary Markdown set but are not part of the primary LaTeX reading order represented by `tex-zh/main.tex`.

## Regeneration

Run:

```powershell
python tools\extract_clean_source.py
```

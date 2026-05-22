# sovereign-individual-cn-revised

目标很明确：保留《主权个人》中文版的最终可维护 Markdown 源文件，并提供可复现的 EPUB 构建脚本（面向微信读书等可重排阅读器）。

## 下载

- 直接下载最新版 EPUB：[主权个人.epub](https://github.com/iridite/sovereign-individual-cn-revised/releases/latest/download/default.epub)

## 来源与说明

- 本仓库最初克隆自 [Macin20/sovereign-individual-cn](https://github.com/Macin20/sovereign-individual-cn)。
- 中文文本基础来自该仓库所收录的《主权个人》中文版 LaTeX 源稿（译者署名见原仓库说明）。
- 当前版本在该译稿基础上做了二次复校、文本修订与 EPUB 整理，目标是把文本变成“可长期维护的出版级源文件”，而不只是一次性生成电子书。

## 仓库结构

- `source/`
  - 最终 Markdown 源文件（构建 EPUB 的真源）
  - `book-main.md` 汇总稿
  - `metadata.yaml` EPUB 元数据、`style.css` 样式、`cover.png` 封面
- `scripts/`
  - 构建脚本
  - `build_epub.py` / `build_epub.ps1`
- `reference/`
  - 对照与溯源材料（英文原文、中文 PDF、历史 ePub 等）
  - 见 `reference/README.md`（包含每个二进制文件的用途与出处说明）
- `dist/`（构建输出，不进入版本控制）
  - `主权个人.epub`
  - `validation-report.md`
- `.work/`（构建中间产物，不进入版本控制）

## 生成 EPUB

Windows 下运行：

```powershell
.\scripts\build_epub.ps1
```

或：

```powershell
python .\scripts\build_epub.py
```

## 校对 / 对照

- 英文原文、中文 PDF、以及其他对照材料统一放在 `reference/` 下，方便读者自行校对与复核（见 `reference/README.md`）。

## 内容修改原则

- 构建脚本不会对正文进行“自动替换/修补”。任何文本修改都应直接在 `source/` 下完成，并通过版本控制追踪。

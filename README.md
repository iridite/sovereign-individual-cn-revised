# sovereign-individual-cn-revised

基于 [Macin20/sovereign-individual-cn](https://github.com/Macin20/sovereign-individual-cn) 的本地修订版工作仓库。当前仓库重点不再是单纯保留原始 LaTeX 排版，而是围绕以下三条主线组织：

- 保留中文 LaTeX 主源 `tex-zh`
- 保留逐章审校、清洗与修订成果 `derived`
- 产出适合微信读书导入的中文修订版 EPUB

## 当前仓库内容

- `books/original`
  - 原版英文参考书文件。目前保留英文 PDF 作为来源参考。
- `tex-zh`
  - 中文 LaTeX 主源、版式资源、PDF 版本与中间 Markdown 镜像。
- `derived/clean-source`
  - 从中文 LaTeX 抽取并清洗出的干净正文源。
- `derived/translation-review`
  - 全书中英对照审校记录与问题台账。
- `derived/revised-edition`
  - 当前最终工作主线：修订版源文件、术语表、终检报告、构建输出。
- `templates/epub`
  - 旧版 EPUB 构建所用的模板资源，包括样式、元数据、书名页和版权页模板。
- `tools`
  - Python 构建脚本与抽取脚本。
- `tools/scripts`
  - PowerShell 入口脚本，便于在 Windows 本地直接重建产物。

## 当前产物

修订版终稿当前位于：

- `derived/revised-edition/build/output/主权个人-修订版.epub`

已冻结的 Git 节点：

- `v1-baseline`
  - 终修前稳定基线
- `v1-final`
  - 终稿验收通过后的冻结版本

## 本地构建入口

Windows 下可直接使用：

- `tools/scripts/build_revised_edition.ps1`
  - 生成修订版 EPUB
- `tools/scripts/build_epub.ps1`
  - 生成较早的基础 EPUB 管线产物

对应 Python 脚本：

- `tools/build_revised_edition.py`
- `tools/build_epub.py`
- `tools/extract_clean_source.py`

## 说明

1. 本仓库保留了原项目中文 LaTeX 主源，但已经移除了未进入当前工作流的中英双语试验目录和零散 TXT 对照稿。
2. `derived/revised-edition` 是当前应优先查看和继续维护的主目录。
3. `derived/translation-review` 保留了完整的逐章审校过程，适合作为修订依据和 fork 后的公开报告基础。
4. 本项目仅供学习、研究与个人阅读使用，请勿商用。

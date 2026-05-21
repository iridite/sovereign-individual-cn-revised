# sovereign-individual-cn-revised

这是一个极简整理版仓库，目标只有一件事：保留《主权个人》中文版的**最终 Markdown 源**，并提供可复现的 EPUB 构建脚本。

## 下载

- 直接下载最新版 EPUB：[主权个人.epub](https://github.com/iridite/sovereign-individual-cn-revised/releases/latest/download/%E4%B8%BB%E6%9D%83%E4%B8%AA%E4%BA%BA.epub)

## 来源

- 本仓库最初克隆自 [Macin20/sovereign-individual-cn](https://github.com/Macin20/sovereign-individual-cn)。
- 中文文本基础来自该仓库所收录的《主权个人》中文版 LaTeX 源稿，译者署名为 `陈三省`。
- 当前版本在该译稿基础上做了独立的二次复校、文本修订与 EPUB 整理，形成现在这份可直接维护的 Markdown 成稿。

## 本次修订内容

- 将原始 LaTeX 内容整理为结构清晰、可持续维护的 Markdown 源文件。
- 系统清理正文中的病句、错字、断词、格式残留和明显误译。
- 统一全书关键术语与行文口径，尽量保证正文的连续性、准确性和书面度。
- 清理无关宣传、口语旁白和不适合进入正式文本的脚注内容，仅保留必要注释。
- 重建前置页、附录、封面、元数据与样式文件，使整书可以稳定生成 EPUB。

## 仓库结构

- `source/`
  - 最终 Markdown 源文件
  - 书名页、版权页、前言、译者序、11 章正文、后记、两份附录
  - `book-main.md` 汇总稿
  - `metadata.yaml` EPUB 元数据
  - `style.css` EPUB 样式
  - `cover.png` 封面图
- `build_epub.py`
  - 从 `source/` 直接生成 EPUB
- `build_epub.ps1`
  - Windows 下的一键入口

## 生成 EPUB

在 Windows 下直接运行：

```powershell
.\build_epub.ps1
```

或直接运行：

```powershell
python .\build_epub.py
```

生成结果默认输出到：

- `dist/主权个人.epub`
- `dist/validation-report.md`

构建过程中的中间文件会放到：

- `.work/`

这两个目录都不进入版本控制。

## 说明

1. 当前仓库只保留最终可读、可构建、可复现的核心内容。
2. 更早的审校记录、清洗中间层、旧目录结构和历史构建产物不再保留在当前树中，但仍可从 Git 历史中追溯。
3. 本项目仅供学习、研究与个人阅读使用，请勿商用。

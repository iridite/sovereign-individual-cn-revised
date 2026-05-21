# sovereign-individual-cn-revised

这是一个极简整理版仓库，目标只有一件事：保留《主权个人》中文版的**最终 Markdown 源**，并提供可复现的 EPUB 构建脚本。

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

- `dist/主权个人-修订版.epub`
- `dist/validation-report.md`

构建过程中的中间文件会放到：

- `.work/`

这两个目录都不进入版本控制。

## 说明

1. 当前仓库只保留最终可读、可构建、可复现的核心内容。
2. 更早的审校记录、清洗中间层、旧目录结构和历史构建产物不再保留在当前树中，但仍可从 Git 历史中追溯。
3. 本项目仅供学习、研究与个人阅读使用，请勿商用。

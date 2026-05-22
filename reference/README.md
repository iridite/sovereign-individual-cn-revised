# reference/

这个目录放“对照/溯源材料”，用途只有一个：让其他人能在不翻 Git 历史、不依赖外部链接的情况下，直接拿到原文与对照件来校对、复核、或复现构建流程。

## 目录结构

- `reference/pdf/`
  - 英文原文 PDF（用于忠实性校对、专名/术语核验）
  - 中文 PDF（不同排版/编辑版对照件）
- `reference/epub/`
  - 历史 ePub / 外部来源 ePub（用于对照目录结构、检查是否夹带额外内容等）

## 文件说明

- `reference/pdf/The Sovereign Individual - James Dale Davidson.pdf`
  - 英文原文（从本仓库 git 历史对象导出，便于复现与溯源）
  - 原始 blob：`a3a6e34e9278557bc859e6e1e8311ffc9ebdf0a8`
- `reference/pdf/主权个人 陈三省译.pdf`
  - 中文 PDF 对照件（由维护者加入；不参与构建）
- `reference/pdf/主权个人 Gao译.pdf`
  - 中文 PDF 对照件（由维护者加入；不参与构建）
- `reference/epub/The_Sovereign_Individual_Z-Library_(Translated).epub`
  - 历史来源 ePub（从本仓库 git 历史对象导出）
  - 原始 blob：`970e9033183e9b9d339645207bed57154305e603`

## 复现导出（可选）

如果你想验证英文原文 PDF 是否来自 git 历史对象，可以用：

```bash
git cat-file -p a3a6e34e9278557bc859e6e1e8311ffc9ebdf0a8 > "reference/pdf/The Sovereign Individual - James Dale Davidson.pdf"
```


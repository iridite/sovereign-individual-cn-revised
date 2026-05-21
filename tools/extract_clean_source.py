from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
TEX_ROOT = ROOT / "tex-zh"
MAINCONTENTS_ROOT = TEX_ROOT / "maincontents"
OUTPUT_ROOT = ROOT / "derived" / "clean-source"
PRIMARY_OUTPUT_ROOT = OUTPUT_ROOT / "primary"


IGNORED_COMMAND_LINES = (
    r"\thispagestyle",
    r"\addcontentsline",
    r"\let\cleardoublepage\clearpage",
    r"\clearpage",
    r"\cleardoublepage",
    r"\newpage",
)


@dataclass
class Footnote:
    id: str
    content: str


@dataclass
class SectionRecord:
    order: int
    slug: str
    kind: str
    title: str
    short_title: str | None
    source_path: str
    output_path: str
    heading_count: dict[str, int]
    paragraph_count: int
    blockquote_count: int
    list_count: int
    footnote_count: int
    emphasis_count: dict[str, int]
    source_family: str = "primary_tex"


@dataclass
class ConversionState:
    section_slug: str
    footnotes: list[Footnote] = field(default_factory=list)
    blockquote_count: int = 0
    list_count: int = 0
    paragraph_count: int = 0
    headings: dict[str, int] = field(
        default_factory=lambda: {"chapter": 0, "section": 0, "subsection": 0}
    )
    emphasis_count: dict[str, int] = field(
        default_factory=lambda: {"strong": 0, "emphasis": 0}
    )
    _footnote_index: int = 0

    def next_footnote_id(self) -> str:
        self._footnote_index += 1
        return f"{self.section_slug}-fn-{self._footnote_index}"


def strip_tex_comments(text: str) -> str:
    cleaned_lines = []
    for line in text.splitlines():
        escaped = False
        cut_at = None
        for index, char in enumerate(line):
            if char == "\\" and not escaped:
                escaped = True
                continue
            if char == "%" and not escaped:
                cut_at = index
                break
            escaped = False
        cleaned_lines.append(line if cut_at is None else line[:cut_at])
    return "\n".join(cleaned_lines)


def normalize_spacing(text: str) -> str:
    text = text.replace("\u3000", " ")
    text = text.replace("\xa0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    return text.strip()


def normalize_title(text: str) -> str:
    return normalize_spacing(text.replace("\n", " "))


def slugify(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def extract_braced(text: str, start: int) -> tuple[str, int]:
    if start >= len(text) or text[start] != "{":
        raise ValueError(f"expected '{{' at position {start}")
    depth = 0
    buffer: list[str] = []
    index = start
    while index < len(text):
        char = text[index]
        if char == "{":
            depth += 1
            if depth > 1:
                buffer.append(char)
        elif char == "}":
            depth -= 1
            if depth == 0:
                return "".join(buffer), index + 1
            buffer.append(char)
        else:
            buffer.append(char)
        index += 1
    raise ValueError("unterminated braced content")


def extract_bracketed(text: str, start: int) -> tuple[str, int]:
    if start >= len(text) or text[start] != "[":
        raise ValueError(f"expected '[' at position {start}")
    depth = 0
    buffer: list[str] = []
    index = start
    while index < len(text):
        char = text[index]
        if char == "[":
            depth += 1
            if depth > 1:
                buffer.append(char)
        elif char == "]":
            depth -= 1
            if depth == 0:
                return "".join(buffer), index + 1
            buffer.append(char)
        else:
            buffer.append(char)
        index += 1
    raise ValueError("unterminated bracketed content")


def cleanup_inline_text(text: str) -> str:
    text = text.replace("\\\\", "\n")
    text = text.replace("$", "")
    text = text.replace(r"\%", "%")
    text = text.replace(r"\&", "&")
    text = text.replace(r"\$", "$")
    text = text.replace(r"\_", "_")
    text = text.replace(r"\#", "#")
    text = text.replace("~", " ")
    text = re.sub(r"\s+\n", "\n", text)
    text = re.sub(r"\n\s+", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def convert_inline(text: str, state: ConversionState) -> str:
    output: list[str] = []
    index = 0
    while index < len(text):
        if text.startswith("\\\\", index):
            output.append("\n")
            index += 2
            continue
        if text.startswith(r"\%", index):
            output.append("%")
            index += 2
            continue
        if text.startswith(r"\&", index):
            output.append("&")
            index += 2
            continue
        if text.startswith(r"\$", index):
            output.append("$")
            index += 2
            continue
        if text.startswith(r"\_", index):
            output.append("_")
            index += 2
            continue
        if text.startswith(r"\#", index):
            output.append("#")
            index += 2
            continue
        if text.startswith(r"\times", index):
            output.append("×")
            index += len(r"\times")
            continue
        if text.startswith(r"\LaTeX", index):
            output.append("LaTeX")
            index += len(r"\LaTeX")
            continue
        if text.startswith(r"\kaishu", index):
            index += len(r"\kaishu")
            continue
        if text[index] == "$":
            index += 1
            continue
        if text[index] == "\\":
            command_match = re.match(r"\\([A-Za-z]+\*?)", text[index:])
            if command_match:
                command = command_match.group(1)
                index += len(command) + 1
                if command in {"textbf", "uline"}:
                    inner, index = extract_braced(text, index)
                    state.emphasis_count["strong"] += 1
                    output.append(f"**{convert_inline(inner, state)}**")
                    continue
                if command in {"textit", "emph"}:
                    inner, index = extract_braced(text, index)
                    state.emphasis_count["emphasis"] += 1
                    output.append(f"*{convert_inline(inner, state)}*")
                    continue
                if command == "href":
                    url, index = extract_braced(text, index)
                    label, index = extract_braced(text, index)
                    output.append(f"[{convert_inline(label, state)}]({normalize_spacing(url)})")
                    continue
                if command == "footnote":
                    note, index = extract_braced(text, index)
                    note_id = state.next_footnote_id()
                    note_md = cleanup_inline_text(convert_inline(note, state))
                    state.footnotes.append(Footnote(id=note_id, content=note_md))
                    output.append(f"[^{note_id}]")
                    continue
                if command == "circled":
                    inner, index = extract_braced(text, index)
                    output.append(f"({convert_inline(inner, state)})")
                    continue
                if index < len(text) and text[index] == "{":
                    inner, index = extract_braced(text, index)
                    output.append(convert_inline(inner, state))
                    continue
                continue
        if text[index] in "{}":
            index += 1
            continue
        output.append(text[index])
        index += 1
    return cleanup_inline_text("".join(output))


def split_paragraphs(lines: Iterable[str]) -> list[list[str]]:
    paragraphs: list[list[str]] = []
    current: list[str] = []
    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            if current:
                paragraphs.append(current)
                current = []
            continue
        current.append(line)
    if current:
        paragraphs.append(current)
    return paragraphs


def convert_flushright_block(lines: list[str], state: ConversionState) -> list[str]:
    paragraphs = split_paragraphs(lines)
    output: list[str] = []
    for paragraph in paragraphs:
        converted = convert_inline(" ".join(paragraph), state)
        for line in converted.splitlines():
            clean = line.strip()
            if clean:
                output.append(clean)
    return output


def convert_tcolorbox(lines: list[str], state: ConversionState) -> list[str]:
    state.blockquote_count += 1
    body_lines: list[str] = []
    attribution_lines: list[str] = []
    index = 0
    while index < len(lines):
        stripped = lines[index].strip()
        if stripped.startswith(r"\begin{flushright}"):
            block, next_index = collect_environment(lines, index, "flushright")
            attribution_lines = block[1:-1]
            index = next_index
            continue
        body_lines.append(lines[index])
        index += 1

    body_paragraphs = split_paragraphs(body_lines)
    output: list[str] = []
    for paragraph in body_paragraphs:
        converted = convert_inline(" ".join(paragraph), state)
        for line in converted.splitlines():
            clean = line.strip()
            if clean:
                output.append(f"> {clean}")
        output.append(">")
    if output and output[-1] == ">":
        output.pop()

    if attribution_lines:
        if output:
            output.append(">")
        attribution = convert_inline(" ".join(line.strip() for line in attribution_lines), state)
        for line in attribution.splitlines():
            clean = line.strip()
            if clean:
                output.append(f"> {clean}")
    return output


def collect_environment(lines: list[str], start: int, env_name: str) -> tuple[list[str], int]:
    depth = 0
    block: list[str] = []
    index = start
    begin_token = rf"\begin{{{env_name}}}"
    end_token = rf"\end{{{env_name}}}"
    while index < len(lines):
        stripped = lines[index].strip()
        if stripped.startswith(begin_token):
            depth += 1
        if stripped.startswith(end_token):
            depth -= 1
            block.append(lines[index])
            index += 1
            if depth == 0:
                return block, index
            continue
        block.append(lines[index])
        index += 1
    raise ValueError(f"unterminated environment: {env_name}")


def parse_list_environment(lines: list[str], state: ConversionState, ordered: bool, level: int = 0) -> list[str]:
    state.list_count += 1
    inner_lines = lines[1:-1]
    output: list[str] = []
    index = 0
    current_lines: list[str] = []
    nested_lines: list[str] = []

    def flush_item() -> None:
        nonlocal current_lines, nested_lines
        if not current_lines and not nested_lines:
            return
        prefix = "1. " if ordered else "- "
        indent = "    " * level
        item_text = convert_inline(" ".join(line.strip() for line in current_lines), state).strip()
        if item_text:
            output.append(f"{indent}{prefix}{item_text}")
        elif nested_lines:
            output.append(f"{indent}{prefix}")
        for nested in nested_lines:
            output.append(f"{indent}    {nested}" if nested else "")
        current_lines = []
        nested_lines = []

    while index < len(inner_lines):
        stripped = inner_lines[index].strip()
        if not stripped:
            index += 1
            continue
        if stripped.startswith(r"\begin{enumerate}"):
            block, next_index = collect_environment(inner_lines, index, "enumerate")
            nested_lines.extend(parse_list_environment(block, state, ordered=True, level=level + 1))
            index = next_index
            continue
        if stripped.startswith(r"\begin{itemize}"):
            block, next_index = collect_environment(inner_lines, index, "itemize")
            nested_lines.extend(parse_list_environment(block, state, ordered=False, level=level + 1))
            index = next_index
            continue
        if stripped.startswith(r"\item"):
            flush_item()
            current_lines.append(stripped[len(r"\item") :].strip())
            index += 1
            continue
        current_lines.append(stripped)
        index += 1

    flush_item()
    return output


def parse_heading(line: str, command: str) -> tuple[str, str | None]:
    stripped = line.strip()
    index = len(command) + 1
    short_title = None
    if index < len(stripped) and stripped[index] == "[":
        short_title, index = extract_bracketed(stripped, index)
    title, _ = extract_braced(stripped, index)
    title = normalize_title(convert_inline(title, ConversionState(section_slug="heading")))
    if short_title is not None:
        short_title = normalize_title(convert_inline(short_title, ConversionState(section_slug="heading")))
    return title, short_title


def is_ignored_line(line: str) -> bool:
    stripped = line.strip()
    return any(stripped.startswith(token) for token in IGNORED_COMMAND_LINES)


def is_block_start(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return True
    if is_ignored_line(stripped):
        return True
    return any(
        stripped.startswith(prefix)
        for prefix in (
            r"\chapter",
            r"\section",
            r"\subsection",
            r"\begin{tcolorbox}",
            r"\begin{enumerate}",
            r"\begin{itemize}",
            r"\begin{flushright}",
        )
    )


def convert_tex_file(section_slug: str, text: str) -> tuple[str, ConversionState, str, str | None]:
    state = ConversionState(section_slug=section_slug)
    text = strip_tex_comments(text)
    lines = text.splitlines()
    output: list[str] = []
    title = ""
    short_title: str | None = None
    index = 0
    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        if not stripped or is_ignored_line(stripped):
            index += 1
            continue
        if stripped.startswith(r"\chapter*"):
            title, short_title = parse_heading(stripped, "chapter*")
            state.headings["chapter"] += 1
            output.append(f"# {title}")
            output.append("")
            index += 1
            continue
        if stripped.startswith(r"\chapter"):
            title, short_title = parse_heading(stripped, "chapter")
            state.headings["chapter"] += 1
            output.append(f"# {title}")
            output.append("")
            index += 1
            continue
        if stripped.startswith(r"\section{"):
            heading, _ = parse_heading(stripped, "section")
            state.headings["section"] += 1
            output.append(f"## {heading}")
            output.append("")
            index += 1
            continue
        if stripped.startswith(r"\subsection{"):
            heading, _ = parse_heading(stripped, "subsection")
            state.headings["subsection"] += 1
            output.append(f"### {heading}")
            output.append("")
            index += 1
            continue
        if stripped.startswith(r"\begin{tcolorbox}"):
            block, next_index = collect_environment(lines, index, "tcolorbox")
            output.extend(convert_tcolorbox(block[1:-1], state))
            output.append("")
            index = next_index
            continue
        if stripped.startswith(r"\begin{enumerate}"):
            block, next_index = collect_environment(lines, index, "enumerate")
            output.extend(parse_list_environment(block, state, ordered=True))
            output.append("")
            index = next_index
            continue
        if stripped.startswith(r"\begin{itemize}"):
            block, next_index = collect_environment(lines, index, "itemize")
            output.extend(parse_list_environment(block, state, ordered=False))
            output.append("")
            index = next_index
            continue
        if stripped.startswith(r"\begin{flushright}"):
            block, next_index = collect_environment(lines, index, "flushright")
            output.extend(convert_flushright_block(block[1:-1], state))
            output.append("")
            index = next_index
            continue

        paragraph_lines = [stripped]
        index += 1
        while index < len(lines) and not is_block_start(lines[index]):
            if lines[index].strip():
                paragraph_lines.append(lines[index].strip())
            index += 1
        paragraph = convert_inline(" ".join(paragraph_lines), state).strip()
        if paragraph:
            state.paragraph_count += 1
            output.append(paragraph)
            output.append("")

    while output and not output[-1].strip():
        output.pop()

    if state.footnotes:
        output.append("")
        for footnote in state.footnotes:
            output.append(f"[^{footnote.id}]: {footnote.content}")

    markdown = "\n".join(output).strip() + "\n"
    return markdown, state, title, short_title


def parse_main_inputs(text: str) -> list[str]:
    return re.findall(r"\\input\{(maincontents/[^}]+)\}", text)


def build_section_kind(filename: str) -> str:
    if filename in {"preface.tex", "preface2.tex"}:
        return "frontmatter"
    if filename.startswith("chapter"):
        return "chapter"
    if filename in {"afterword.tex", "appendix.tex", "appendix2.tex"}:
        return "backmatter"
    return "other"


def build_secondary_inventory() -> list[dict[str, object]]:
    md_root = TEX_ROOT / "md-files"
    mapping = {
        "新版序言.md": "maps_to_preface",
        "译者序.md": "maps_to_preface2",
        "cpt1.md": "maps_to_chapter1",
        "cpt2.md": "maps_to_chapter2",
        "cpt3.md": "maps_to_chapter3",
        "cpt4.md": "maps_to_chapter4",
        "cpt5.md": "maps_to_chapter5",
        "cpt6.md": "maps_to_chapter6",
        "cpt7.md": "maps_to_chapter7",
        "cpt8.md": "maps_to_chapter8",
        "cpt9.md": "maps_to_chapter9",
        "cpt10.md": "maps_to_chapter10",
        "cpt11.md": "maps_to_chapter11",
        "end1.md": "maps_to_afterword",
        "end3.md": "maps_to_appendix",
        "end4.md": "maps_to_appendix2",
    }
    records: list[dict[str, object]] = []
    for path in sorted(md_root.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        records.append(
            {
                "path": str(path.relative_to(ROOT)).replace("\\", "/"),
                "line_count": len(text.splitlines()),
                "html_tag_count": len(re.findall(r"<[^>]+>", text)),
                "status": mapping.get(path.name, "auxiliary_only_or_variant"),
            }
        )
    return records


def build_book_metadata(main_tex: str) -> dict[str, object]:
    def clean_metadata_value(value: str | None) -> str | None:
        if value is None:
            return None
        value = re.sub(r"\\fontsize\{[^}]+\}\{[^}]+\}\\selectfont", "", value)
        value = re.sub(r"\\hspace\{[^}]+\}", " ", value)
        value = value.replace(r"\selectfont", " ")
        return normalize_spacing(value)

    def extract_simple_command(command: str) -> str | None:
        matches = list(re.finditer(rf"\\{command}\s*\{{", main_tex))
        if not matches:
            return None
        brace_start = matches[-1].end() - 1
        value, _ = extract_braced(main_tex, brace_start)
        return clean_metadata_value(value)

    return {
        "title": extract_simple_command("title"),
        "subtitle": extract_simple_command("subtitle"),
        "edition": extract_simple_command("edition"),
        "pressname": extract_simple_command("pressname"),
        "source_entrypoint": str((TEX_ROOT / "main.tex").relative_to(ROOT)).replace("\\", "/"),
    }


def main() -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    PRIMARY_OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

    main_tex_path = TEX_ROOT / "main.tex"
    main_tex = main_tex_path.read_text(encoding="utf-8")
    ordered_inputs = parse_main_inputs(main_tex)

    records: list[SectionRecord] = []
    combined_sections: list[str] = []

    export_order = 0
    for input_path in ordered_inputs:
        relative_path = Path(input_path)
        if relative_path.suffix != ".tex":
            relative_path = relative_path.with_suffix(".tex")
        if relative_path.name == "titlepage.tex":
            continue
        export_order += 1
        source_path = TEX_ROOT / relative_path
        section_slug = f"{export_order:02d}-{slugify(relative_path.stem)}"
        markdown, state, title, short_title = convert_tex_file(
            section_slug=section_slug,
            text=source_path.read_text(encoding="utf-8"),
        )
        output_filename = f"{section_slug}.md"
        output_path = PRIMARY_OUTPUT_ROOT / output_filename
        output_path.write_text(markdown, encoding="utf-8")

        combined_sections.append(markdown.rstrip())
        records.append(
            SectionRecord(
                order=export_order,
                slug=section_slug,
                kind=build_section_kind(relative_path.name),
                title=title,
                short_title=short_title,
                source_path=str(source_path.relative_to(ROOT)).replace("\\", "/"),
                output_path=str(output_path.relative_to(ROOT)).replace("\\", "/"),
                heading_count=state.headings,
                paragraph_count=state.paragraph_count,
                blockquote_count=state.blockquote_count,
                list_count=state.list_count,
                footnote_count=len(state.footnotes),
                emphasis_count=state.emphasis_count,
            )
        )

    combined_book = "\n\n".join(combined_sections).strip() + "\n"
    (OUTPUT_ROOT / "book.md").write_text(combined_book, encoding="utf-8")

    manifest = {
        "book": build_book_metadata(main_tex),
        "source_families": [
            {
                "name": "primary_tex",
                "description": "Authoritative Chinese LaTeX composition used by tex-zh/main.tex",
                "root": "tex-zh/maincontents",
            },
            {
                "name": "secondary_md",
                "description": "Markdown mirror / auxiliary text set; useful for cross-checking but not used as the canonical source here",
                "root": "tex-zh/md-files",
            },
        ],
        "secondary_inventory": build_secondary_inventory(),
        "sections": [record.__dict__ for record in records],
        "totals": {
            "section_count": len(records),
            "footnote_count": sum(record.footnote_count for record in records),
            "blockquote_count": sum(record.blockquote_count for record in records),
            "list_count": sum(record.list_count for record in records),
            "paragraph_count": sum(record.paragraph_count for record in records),
            "strong_count": sum(record.emphasis_count["strong"] for record in records),
            "emphasis_count": sum(record.emphasis_count["emphasis"] for record in records),
        },
    }
    (OUTPUT_ROOT / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()

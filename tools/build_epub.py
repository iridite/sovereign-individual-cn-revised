from __future__ import annotations

import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

import fitz


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "source" / "clean" / "primary"
EPUB_ROOT = ROOT / "templates" / "epub"
BUILD_ROOT = ROOT / "build" / "legacy-epub"
OUTPUT_ROOT = BUILD_ROOT / "output"
REPORT_ROOT = BUILD_ROOT / "reports"
WORK_ROOT = BUILD_ROOT / "_work"
STAGING_ROOT = WORK_ROOT / "staging"
ASSET_ROOT = WORK_ROOT / "assets"
RAW_UNPACKED_ROOT = WORK_ROOT / "raw-unpacked"

TITLEPAGE_SOURCE = EPUB_ROOT / "titlepage.md"
IMPRINT_SOURCE = EPUB_ROOT / "imprint.md"
STYLE_SOURCE = EPUB_ROOT / "style.css"
METADATA_SOURCE = EPUB_ROOT / "metadata.yaml"
PDF_COVER_SOURCE = ROOT / "tex-zh" / "versions" / "Sovereign_Individual_V2.pdf"
ALT_COVER_SOURCE = Path(r"C:\Users\ollama\Downloads\the-sovereign-individual-9781797103389_hr.jpg")

STAGED_TITLEPAGE = STAGING_ROOT / "00-titlepage.md"
STAGED_IMPRINT = STAGING_ROOT / "01-imprint.md"
RAW_EPUB = OUTPUT_ROOT / "sovereign_individual_raw.epub"
FINAL_EPUB = OUTPUT_ROOT / "主权个人.epub"
LOG_PATH = REPORT_ROOT / "build.log"
REPORT_PATH = REPORT_ROOT / "validation-report.md"
COVER_PATH = ASSET_ROOT / "cover.png"
BOOK_COVER_RATIO = 2 / 3

XHTML_NS = "http://www.w3.org/1999/xhtml"
EPUB_NS = "http://www.idpf.org/2007/ops"
OPF_NS = "http://www.idpf.org/2007/opf"
NCX_NS = "http://www.daisy.org/z3986/2005/ncx/"
NAMESPACES = {
    "xhtml": XHTML_NS,
    "epub": EPUB_NS,
    "opf": OPF_NS,
    "ncx": NCX_NS,
}

ET.register_namespace("", XHTML_NS)
ET.register_namespace("epub", EPUB_NS)
ET.register_namespace("opf", OPF_NS)


def print_status(message: str) -> None:
    print(message, flush=True)


def reset_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def ensure_dirs() -> None:
    BUILD_ROOT.mkdir(parents=True, exist_ok=True)
    reset_dir(OUTPUT_ROOT)
    reset_dir(REPORT_ROOT)
    reset_dir(WORK_ROOT)
    reset_dir(STAGING_ROOT)
    reset_dir(ASSET_ROOT)
    reset_dir(RAW_UNPACKED_ROOT)


def find_executable(name: str, fallbacks: list[Path] | None = None) -> str:
    path = shutil.which(name)
    if path:
        return path
    for candidate in fallbacks or []:
        if candidate.exists():
            return str(candidate)
    raise FileNotFoundError(f"missing executable: {name}")


def run_command(command: list[str], log_lines: list[str]) -> None:
    log_lines.append("$ " + " ".join(f'"{part}"' if " " in part else part for part in command))
    result = subprocess.run(
        command,
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if result.stdout:
        log_lines.append(result.stdout.rstrip())
    if result.stderr:
        log_lines.append(result.stderr.rstrip())
    log_lines.append("")
    if result.returncode != 0:
        raise RuntimeError(f"command failed with exit code {result.returncode}: {command[0]}")


def normalize_heading_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text.strip())
    text = text.replace("： ", "：")
    text = text.replace(" : ", ": ")
    return text


def normalize_markdown(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.rstrip() for line in text.split("\n")]
    output: list[str] = []
    blank_count = 0
    for line in lines:
        if line.startswith("#"):
            hashes, heading = line.split(" ", 1)
            line = f"{hashes} {normalize_heading_text(heading)}"
        if line.strip():
            blank_count = 0
            output.append(line)
        else:
            blank_count += 1
            if blank_count <= 1:
                output.append("")
    cleaned = "\n".join(output).strip() + "\n"
    return cleaned


def stage_markdown() -> list[Path]:
    staged_files: list[Path] = []
    STAGED_TITLEPAGE.write_text(normalize_markdown(TITLEPAGE_SOURCE.read_text(encoding="utf-8")), encoding="utf-8")
    staged_files.append(STAGED_TITLEPAGE)
    STAGED_IMPRINT.write_text(normalize_markdown(IMPRINT_SOURCE.read_text(encoding="utf-8")), encoding="utf-8")
    staged_files.append(STAGED_IMPRINT)

    for source_path in sorted(SOURCE_ROOT.glob("*.md")):
        target_path = STAGING_ROOT / source_path.name
        target_path.write_text(
            normalize_markdown(source_path.read_text(encoding="utf-8")),
            encoding="utf-8",
        )
        staged_files.append(target_path)
    return staged_files


def render_cover() -> None:
    if ALT_COVER_SOURCE.exists():
        document = fitz.open(ALT_COVER_SOURCE)
        try:
            page = document.load_page(0)
            rect = page.rect
            target_width = rect.height * BOOK_COVER_RATIO
            x_offset = max((rect.width - target_width) / 2, 0)
            clip = fitz.Rect(x_offset, 0, x_offset + target_width, rect.height)
            pixmap = page.get_pixmap(matrix=fitz.Matrix(3, 3), clip=clip, alpha=False)
            pixmap.save(str(COVER_PATH))
        finally:
            document.close()
        return

    document = fitz.open(PDF_COVER_SOURCE)
    try:
        page = document.load_page(0)
        pixmap = page.get_pixmap(matrix=fitz.Matrix(2.2, 2.2), alpha=False)
        pixmap.save(str(COVER_PATH))
    finally:
        document.close()


def build_epub(pandoc: str, staged_files: list[Path], log_lines: list[str]) -> None:
    pandoc_command = [
        pandoc,
        "--from=markdown+footnotes+raw_html+fenced_divs",
        "--to=epub3",
        "--output",
        str(RAW_EPUB),
        "--css",
        str(STYLE_SOURCE),
        "--metadata-file",
        str(METADATA_SOURCE),
        "--epub-cover-image",
        str(COVER_PATH),
        "--epub-title-page=false",
        "--toc",
        "--toc-depth=2",
        "--split-level=1",
        "--standalone",
    ] + [str(path) for path in staged_files]
    run_command(pandoc_command, log_lines)


def rewrite_epub_from_dir(source_dir: Path, output_path: Path) -> None:
    with zipfile.ZipFile(output_path, "w") as archive:
        mimetype_path = source_dir / "mimetype"
        archive.write(mimetype_path, "mimetype", compress_type=zipfile.ZIP_STORED)
        for path in sorted(source_dir.rglob("*")):
            if path.is_dir() or path == mimetype_path:
                continue
            archive.write(path, path.relative_to(source_dir).as_posix(), compress_type=zipfile.ZIP_DEFLATED)


def xhtml_tag(name: str) -> str:
    return f"{{{XHTML_NS}}}{name}"


def opf_tag(name: str) -> str:
    return f"{{{OPF_NS}}}{name}"


def ncx_tag(name: str) -> str:
    return f"{{{NCX_NS}}}{name}"


def discover_book_paths(root_dir: Path) -> tuple[Path, Path, Path]:
    opf_candidates = list(root_dir.rglob("content.opf"))
    if not opf_candidates:
        raise FileNotFoundError("missing content.opf in extracted EPUB")
    opf_path = opf_candidates[0]
    epub_root = opf_path.parent
    text_root = epub_root / "text"
    if not text_root.exists():
        raise FileNotFoundError("missing EPUB text directory")
    return epub_root, opf_path, text_root


def get_heading_text(root: ET.Element) -> str:
    for tag_name in ("h1", "h2", "h3"):
        heading = root.find(f".//xhtml:{tag_name}", NAMESPACES)
        if heading is not None:
            text = "".join(heading.itertext()).strip()
            if text:
                return text
    raise ValueError("missing chapter heading")


def replace_note_refs(root: ET.Element) -> None:
    for anchor in root.findall(".//xhtml:a", NAMESPACES):
        href = anchor.get("href", "")
        ref_id = anchor.get("id", "")
        footnote_match = re.fullmatch(r"#fn(\d+)", href)
        ref_match = re.fullmatch(r"fnref(\d+)", ref_id)
        if footnote_match:
            note_number = footnote_match.group(1)
            anchor.set("href", f"#note-{note_number}")
            anchor.set("id", f"noteref-{note_number}")
            anchor.set("class", "note-ref")
            anchor.attrib.pop(f"{{{EPUB_NS}}}type", None)
            anchor.attrib.pop("role", None)
        elif ref_match:
            note_number = ref_match.group(1)
            anchor.set("id", f"noteref-{note_number}")
            anchor.set("class", "note-ref")
            anchor.attrib.pop(f"{{{EPUB_NS}}}type", None)
            anchor.attrib.pop("role", None)


def append_backlink(container: ET.Element, note_number: str) -> None:
    backlink = ET.Element(
        xhtml_tag("a"),
        {"href": f"#noteref-{note_number}", "class": "note-backref"},
    )
    backlink.text = "↩"

    paragraphs = [child for child in list(container) if child.tag == xhtml_tag("p")]
    target = paragraphs[-1] if paragraphs else None
    if target is None:
        target = ET.SubElement(container, xhtml_tag("p"))
    target.append(backlink)


def replace_footnote_sections(root: ET.Element) -> None:
    for section in root.findall(".//xhtml:section", NAMESPACES):
        class_name = section.get("class", "")
        if "footnotes" not in class_name.split():
            continue

        section.set("id", "chapter-notes")
        section.set("class", "chapter-notes")
        section.attrib.pop(f"{{{EPUB_NS}}}type", None)

        children = list(section)
        for child in children:
            section.remove(child)

        hr = ET.SubElement(section, xhtml_tag("hr"))
        hr.tail = "\n"
        heading = ET.SubElement(section, xhtml_tag("h2"), {"class": "notes-title"})
        heading.text = "注释"
        heading.tail = "\n"
        note_list = ET.SubElement(section, xhtml_tag("ol"), {"class": "endnotes"})
        note_list.tail = "\n"

        for child in children:
            if child.tag != xhtml_tag("aside"):
                continue

            note_id = child.get("id", "")
            match = re.fullmatch(r"fn(\d+)", note_id)
            if not match:
                continue
            note_number = match.group(1)
            note_item = ET.SubElement(note_list, xhtml_tag("li"), {"id": f"note-{note_number}"})

            moved = False
            for grandchild in list(child):
                child.remove(grandchild)
                grandchild.attrib.pop(f"{{{EPUB_NS}}}type", None)
                grandchild.attrib.pop("role", None)
                for anchor in grandchild.findall(".//xhtml:a", NAMESPACES):
                    if anchor.get("class") == "footnote-backref":
                        anchor.set("href", f"#noteref-{note_number}")
                        anchor.set("class", "note-backref")
                        anchor.attrib.pop(f"{{{EPUB_NS}}}type", None)
                        anchor.attrib.pop("role", None)
                note_item.append(grandchild)
                moved = True

            if not moved:
                paragraph = ET.SubElement(note_item, xhtml_tag("p"))
                paragraph.text = (child.text or "").strip()

            existing_backlink = note_item.find('.//xhtml:a[@class="note-backref"]', NAMESPACES)
            if existing_backlink is None:
                append_backlink(note_item, note_number)


def retag_heading(element: ET.Element, new_tag: str, class_name: str | None = None) -> None:
    element.tag = xhtml_tag(new_tag)
    if class_name:
        element.set("class", class_name)
    else:
        element.attrib.pop("class", None)


def rewrite_titlepage_document(root: ET.Element) -> None:
    body = root.find("xhtml:body", NAMESPACES)
    if body is None:
        return

    section = body.find("xhtml:section", NAMESPACES)
    if section is None:
        return

    section.set(f"{{{EPUB_NS}}}type", "titlepage")
    section.set("id", "titlepage")

    heading = section.find("xhtml:h1", NAMESPACES)
    if heading is not None:
        heading.set("class", "tp-title")


def set_body_semantics(root: ET.Element, chapter_name: str) -> None:
    body = root.find("xhtml:body", NAMESPACES)
    if body is None:
        return

    if chapter_name in {"ch001", "ch002", "ch003", "ch004"}:
        body.set(f"{{{EPUB_NS}}}type", "frontmatter")
    else:
        body.set(f"{{{EPUB_NS}}}type", "bodymatter")


def rewrite_chapter_documents(text_root: Path) -> dict[str, str]:
    chapter_titles: dict[str, str] = {}
    for xhtml_path in sorted(text_root.glob("ch*.xhtml")):
        tree = ET.parse(xhtml_path)
        root = tree.getroot()
        chapter_name = xhtml_path.stem
        title_text = "主权个人" if chapter_name == "ch001" else get_heading_text(root)
        chapter_titles[chapter_name] = title_text

        title_element = root.find("xhtml:head/xhtml:title", NAMESPACES)
        if title_element is not None:
            title_element.text = title_text

        replace_note_refs(root)
        replace_footnote_sections(root)
        set_body_semantics(root, chapter_name)
        if chapter_name == "ch001":
            rewrite_titlepage_document(root)
        tree.write(xhtml_path, encoding="utf-8", xml_declaration=True)

    return chapter_titles


def build_landmarks() -> ET.Element:
    nav = ET.Element(
        xhtml_tag("nav"),
        {f"{{{EPUB_NS}}}type": "landmarks", "id": "landmarks", "role": "doc-landmarks"},
    )
    heading = ET.SubElement(nav, xhtml_tag("h2"))
    heading.text = "位置"
    ordered = ET.SubElement(nav, xhtml_tag("ol"))

    items = [
        ("text/cover.xhtml", "封面", "cover"),
        ("text/ch001.xhtml", "扉页", "titlepage"),
        ("text/ch002.xhtml", "版权与编目信息", "copyright-page"),
        ("text/ch003.xhtml", "前言", "preface"),
        ("text/ch005.xhtml", "正文", "bodymatter"),
    ]
    for href, label, landmark_type in items:
        item = ET.SubElement(ordered, xhtml_tag("li"))
        anchor = ET.SubElement(item, xhtml_tag("a"), {"href": href, f"{{{EPUB_NS}}}type": landmark_type})
        anchor.text = label
    return nav


def rewrite_nav_document(nav_path: Path) -> None:
    tree = ET.parse(nav_path)
    root = tree.getroot()
    toc_nav = root.find('.//xhtml:nav[@epub:type="toc"]', NAMESPACES)
    if toc_nav is None:
        raise ValueError("missing toc nav in nav.xhtml")

    title_heading = toc_nav.find("xhtml:h1", NAMESPACES)
    if title_heading is not None:
        title_heading.text = "目录"

    ordered = toc_nav.find("xhtml:ol", NAMESPACES)
    if ordered is not None:
        top_items = ordered.findall("xhtml:li", NAMESPACES)
        if len(top_items) >= 1:
            first_anchor = top_items[0].find("xhtml:a", NAMESPACES)
            if first_anchor is not None:
                first_anchor.text = "书名页"
        if len(top_items) >= 2:
            second_anchor = top_items[1].find("xhtml:a", NAMESPACES)
            if second_anchor is not None:
                second_anchor.text = "版权页"

    for nav in root.findall('.//xhtml:nav[@epub:type="landmarks"]', NAMESPACES):
        parent = root.find("xhtml:body", NAMESPACES)
        if parent is not None:
            parent.remove(nav)

    body = root.find("xhtml:body", NAMESPACES)
    if body is None:
        raise ValueError("missing body in nav.xhtml")
    body.append(build_landmarks())
    tree.write(nav_path, encoding="utf-8", xml_declaration=True)


def rewrite_ncx(ncx_path: Path) -> None:
    tree = ET.parse(ncx_path)
    root = tree.getroot()
    nav_map = root.find("ncx:navMap", NAMESPACES)
    if nav_map is None:
        return

    top_points = nav_map.findall("ncx:navPoint", NAMESPACES)
    if len(top_points) >= 1:
        first_text = top_points[0].find("ncx:navLabel/ncx:text", NAMESPACES)
        if first_text is not None:
            first_text.text = "书名页"
    if len(top_points) >= 2:
        second_text = top_points[1].find("ncx:navLabel/ncx:text", NAMESPACES)
        if second_text is not None:
            second_text.text = "版权页"

    tree.write(ncx_path, encoding="utf-8", xml_declaration=True)


def rewrite_package_document(opf_path: Path) -> tuple[list[str], str | None]:
    tree = ET.parse(opf_path)
    root = tree.getroot()
    spine = root.find("opf:spine", NAMESPACES)
    if spine is None:
        raise ValueError("missing spine in content.opf")

    removed_idrefs = {"cover_xhtml", "nav"}
    kept_spine: list[str] = []
    for itemref in list(spine):
        idref = itemref.get("idref", "")
        if idref in removed_idrefs:
            spine.remove(itemref)
            continue
        kept_spine.append(idref)

    guide = root.find("opf:guide", NAMESPACES)
    if guide is None:
        guide = ET.SubElement(root, opf_tag("guide"))
    else:
        for child in list(guide):
            guide.remove(child)

    guide_entries = [
        ("cover", "封面", "text/cover.xhtml"),
        ("toc", "目录", "nav.xhtml"),
        ("title-page", "扉页", "text/ch001.xhtml"),
        ("copyright-page", "版权与编目信息", "text/ch002.xhtml"),
        ("text", "正文", "text/ch005.xhtml"),
    ]
    for entry_type, title, href in guide_entries:
        ET.SubElement(guide, opf_tag("reference"), {"type": entry_type, "title": title, "href": href})

    tree.write(opf_path, encoding="utf-8", xml_declaration=True)
    first_linear = kept_spine[0] if kept_spine else None
    return kept_spine, first_linear


def postprocess_final_epub() -> dict[str, object]:
    with zipfile.ZipFile(RAW_EPUB) as archive:
        archive.extractall(RAW_UNPACKED_ROOT)

    epub_root, opf_path, text_root = discover_book_paths(RAW_UNPACKED_ROOT)
    chapter_titles = rewrite_chapter_documents(text_root)
    rewrite_nav_document(epub_root / "nav.xhtml")

    ncx_path = epub_root / "toc.ncx"
    if ncx_path.exists():
        rewrite_ncx(ncx_path)

    spine_items, first_linear = rewrite_package_document(opf_path)
    rewrite_epub_from_dir(RAW_UNPACKED_ROOT, FINAL_EPUB)
    return {
        "chapter_titles": chapter_titles,
        "spine_items": spine_items,
        "first_linear": first_linear,
    }


def is_ascii_path(path: str) -> bool:
    try:
        path.encode("ascii")
        return True
    except UnicodeEncodeError:
        return False


def validate_epub() -> dict[str, object]:
    issues: list[str] = []
    latex_hits = 0
    nav_candidates: list[str] = []
    title_mismatches: list[str] = []
    spine_items: list[str] = []
    first_linear: str | None = None

    with zipfile.ZipFile(FINAL_EPUB) as archive:
        names = archive.namelist()
        if "mimetype" not in names:
            issues.append("missing mimetype")
        if "META-INF/container.xml" not in names:
            issues.append("missing META-INF/container.xml")

        for name in names:
            lower = name.lower()
            if lower.endswith("nav.xhtml"):
                nav_candidates.append(name)
            if not is_ascii_path(name):
                issues.append(f"non-ascii path: {name}")

            if lower.endswith((".xhtml", ".html", ".css", ".opf", ".ncx")):
                text = archive.read(name).decode("utf-8", errors="replace")
                if "C:\\" in text or "file://" in text:
                    issues.append(f"absolute path reference in {name}")
                if re.search(r"\\(?:chapter|section|subsection|textbf|footnote|uline)\b", text):
                    latex_hits += 1
                if "footnotes" in text or re.search(r"\bfn\d+\b", text):
                    issues.append(f"internal footnote marker leaked in {name}")

        if not nav_candidates:
            issues.append("missing nav.xhtml")

        nav_name = nav_candidates[0] if nav_candidates else None
        if nav_name:
            nav_root = ET.fromstring(archive.read(nav_name))
            toc_nav = nav_root.find('.//xhtml:nav[@epub:type="toc"]', NAMESPACES)
            if toc_nav is None:
                issues.append("missing toc nav")
            else:
                toc_links = [anchor.get("href", "") for anchor in toc_nav.findall(".//xhtml:a", NAMESPACES)]
                if not any(link.startswith("text/ch001.xhtml") for link in toc_links):
                    issues.append("title page missing from main toc")
                if not any(link.startswith("text/ch002.xhtml") for link in toc_links):
                    issues.append("imprint page missing from main toc")
            landmarks = nav_root.find('.//xhtml:nav[@epub:type="landmarks"]', NAMESPACES)
            if landmarks is None:
                issues.append("missing landmarks nav")

        opf_name = next((name for name in names if name.endswith("content.opf")), None)
        if opf_name:
            opf_root = ET.fromstring(archive.read(opf_name))
            spine = opf_root.find("opf:spine", NAMESPACES)
            if spine is None:
                issues.append("missing spine in content.opf")
            else:
                spine_items = [itemref.get("idref", "") for itemref in spine.findall("opf:itemref", NAMESPACES)]
                first_linear = spine_items[0] if spine_items else None
                if "nav" in spine_items:
                    issues.append("nav.xhtml still present in spine")
                if "cover_xhtml" in spine_items:
                    issues.append("cover page still present in spine")
                if first_linear != "ch001_xhtml":
                    issues.append(f"unexpected first linear chapter: {first_linear}")

        for name in names:
            if re.search(r"/text/ch\d+\.xhtml$", name):
                root = ET.fromstring(archive.read(name))
                title_element = root.find("xhtml:head/xhtml:title", NAMESPACES)
                heading_text = "主权个人" if name.endswith("/text/ch001.xhtml") else get_heading_text(root)
                title_text = (title_element.text or "").strip() if title_element is not None else ""
                if title_text != heading_text:
                    title_mismatches.append(name)

    return {
        "issues": issues,
        "nav_candidates": nav_candidates,
        "latex_residue_file_count": latex_hits,
        "title_mismatches": title_mismatches,
        "spine_items": spine_items,
        "first_linear": first_linear,
    }


def write_report(validation: dict[str, object]) -> None:
    lines = [
        "# EPUB Validation Report",
        "",
        f"- Final EPUB: `{FINAL_EPUB.relative_to(ROOT).as_posix()}`",
        f"- Raw EPUB: `{RAW_EPUB.relative_to(ROOT).as_posix()}`",
        f"- Cover asset: `{COVER_PATH.relative_to(ROOT).as_posix()}`",
        "",
        "## Checks",
        "",
        f"- `nav.xhtml` candidates: {', '.join(validation['nav_candidates']) if validation['nav_candidates'] else 'none'}",
        f"- First linear chapter: {validation['first_linear'] or 'none'}",
        f"- Spine items: {', '.join(validation['spine_items']) if validation['spine_items'] else 'none'}",
        f"- LaTeX residue files: {validation['latex_residue_file_count']}",
        f"- XHTML title mismatches: {len(validation['title_mismatches'])}",
        "",
        "## Issues",
        "",
    ]
    issues = validation["issues"]
    if issues:
        lines.extend([f"- {issue}" for issue in issues])
    else:
        lines.append("- none")
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    log_lines: list[str] = []
    try:
        ensure_dirs()

        pandoc = find_executable(
            "pandoc",
            [
                Path.home() / "AppData/Local/Microsoft/WinGet/Links/pandoc.exe",
                Path.home() / "AppData/Local/Microsoft/WinGet/Packages/JohnMacFarlane.Pandoc_Microsoft.Winget.Source_8wekyb3d8bbwe/pandoc-3.9.0.2/pandoc.exe",
            ],
        )

        staged_files = stage_markdown()
        render_cover()
        build_epub(pandoc, staged_files, log_lines)
        postprocess_final_epub()
        validation = validate_epub()
        write_report(validation)
        LOG_PATH.write_text("\n".join(log_lines) + "\n", encoding="utf-8")

        print_status(f"Built: {FINAL_EPUB}")
        print_status(f"Report: {REPORT_PATH}")
        return 0 if not validation["issues"] else 1
    except Exception as exc:  # noqa: BLE001
        log_lines.append(f"ERROR: {exc}")
        REPORT_PATH.write_text(f"# EPUB Validation Report\n\n- build failed: {exc}\n", encoding="utf-8")
        LOG_PATH.write_text("\n".join(log_lines) + "\n", encoding="utf-8")
        print_status(str(exc))
        return 1


if __name__ == "__main__":
    sys.exit(main())

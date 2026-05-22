from __future__ import annotations

import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

# Repo layout:
# - source/: canonical book sources (do all text edits here)
# - scripts/: build entrypoints
# - dist/: outputs
# - .work/: scratch

REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE_ROOT = REPO_ROOT / "source"
DIST_ROOT = REPO_ROOT / "dist"
WORK_ROOT = REPO_ROOT / ".work"

METADATA_PATH = SOURCE_ROOT / "metadata.yaml"
STYLE_PATH = SOURCE_ROOT / "style.css"
COVER_PATH = SOURCE_ROOT / "cover.png"

RAW_EPUB = DIST_ROOT / "主权个人-raw.epub"
FINAL_EPUB = DIST_ROOT / "主权个人.epub"
REPORT_PATH = DIST_ROOT / "validation-report.md"
LOG_PATH = DIST_ROOT / "build.log"

MAIN_FILE_ORDER = [
    "00-titlepage.md",
    "01-imprint.md",
    "01-preface.md",
    "02-preface2.md",
    "03-chapter1.md",
    "04-chapter2.md",
    "05-chapter3.md",
    "06-chapter4.md",
    "07-chapter5.md",
    "08-chapter6.md",
    "09-chapter7.md",
    "10-chapter8.md",
    "11-chapter9.md",
    "12-chapter10.md",
    "13-chapter11.md",
    "14-afterword.md",
    "15-appendix.md",
    "16-appendix2.md",
]


def run(command: list[str], log_lines: list[str]) -> None:
    log_lines.append("$ " + " ".join(command))
    proc = subprocess.run(
        command,
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if proc.stdout:
        log_lines.append(proc.stdout.rstrip())
    if proc.stderr:
        log_lines.append(proc.stderr.rstrip())
    log_lines.append("")
    if proc.returncode != 0:
        raise RuntimeError(f"command failed ({proc.returncode}): {command[0]}")


def find_pandoc() -> str:
    pandoc = shutil.which("pandoc")
    if pandoc:
        return pandoc

    candidates = [
        Path.home() / "AppData/Local/Microsoft/WinGet/Links/pandoc.exe",
        Path.home()
        / "AppData/Local/Microsoft/WinGet/Packages/JohnMacFarlane.Pandoc_Microsoft.Winget.Source_8wekyb3d8bbwe/pandoc-3.9.0.2/pandoc.exe",
    ]
    for c in candidates:
        if c.exists():
            return str(c)
    raise FileNotFoundError("pandoc not found")


def reset_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def validate_sources() -> list[str]:
    issues: list[str] = []
    for name in MAIN_FILE_ORDER:
        if not (SOURCE_ROOT / name).exists():
            issues.append(f"missing: source/{name}")
    for required in [METADATA_PATH, STYLE_PATH, COVER_PATH]:
        if not required.exists():
            issues.append(f"missing: {required.as_posix()}")
    return issues


def build_epub(pandoc: str, log_lines: list[str]) -> None:
    DIST_ROOT.mkdir(parents=True, exist_ok=True)
    reset_dir(WORK_ROOT)

    inputs = [str(SOURCE_ROOT / name) for name in MAIN_FILE_ORDER]
    cmd = [
        pandoc,
        "--from=markdown+footnotes+raw_html+fenced_divs",
        "--to=epub3",
        "--output",
        str(RAW_EPUB),
        "--css",
        str(STYLE_PATH),
        "--metadata-file",
        str(METADATA_PATH),
        "--epub-cover-image",
        str(COVER_PATH),
        "--epub-title-page=false",
        "--toc",
        "--toc-depth=2",
        "--split-level=1",
        "--standalone",
        *inputs,
    ]
    run(cmd, log_lines)

    # Repack to ensure mimetype is first and stored (compatibility across readers).
    unpack = WORK_ROOT / "raw-unpacked"
    reset_dir(unpack)
    with zipfile.ZipFile(RAW_EPUB, "r") as zf:
        zf.extractall(unpack)

    mimetype_path = unpack / "mimetype"
    if not mimetype_path.exists():
        raise RuntimeError("raw epub missing mimetype")

    if FINAL_EPUB.exists():
        FINAL_EPUB.unlink()
    with zipfile.ZipFile(FINAL_EPUB, "w") as out:
        out.writestr("mimetype", mimetype_path.read_bytes(), compress_type=zipfile.ZIP_STORED)
        for p in sorted(unpack.rglob("*")):
            if p.is_dir():
                continue
            rel = p.relative_to(unpack).as_posix()
            if rel == "mimetype":
                continue
            out.write(p, rel, compress_type=zipfile.ZIP_DEFLATED)


def write_report(source_issues: list[str], build_error: str | None) -> None:
    DIST_ROOT.mkdir(parents=True, exist_ok=True)
    lines = ["# EPUB 构建报告", ""]
    if source_issues:
        lines.append("## Source Issues")
        for i in source_issues:
            lines.append(f"- {i}")
        lines.append("")
    if build_error:
        lines.append("## Build Error")
        lines.append(f"- {build_error}")
        lines.append("")
    if not source_issues and not build_error:
        lines.append("- OK")
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    log_lines: list[str] = []
    build_error: str | None = None
    source_issues = validate_sources()
    try:
        if source_issues:
            raise RuntimeError("source validation failed")
        pandoc = find_pandoc()
        build_epub(pandoc, log_lines)
    except Exception as exc:
        build_error = str(exc)

    write_report(source_issues, build_error)
    DIST_ROOT.mkdir(parents=True, exist_ok=True)
    LOG_PATH.write_text("\n".join(log_lines) + "\n", encoding="utf-8", errors="ignore")

    if build_error or source_issues:
        return 1

    print(f"Built: {FINAL_EPUB}")
    print(f"Report: {REPORT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


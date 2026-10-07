"""Shared helpers for the PaperViet scripts (standard library only)."""
from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path

FORMAT = "paperviet/1"
DOC_FILE = "document.json"

# Block types that are shown as-is and never need a Vietnamese translation.
KEEP_TYPES = {"authors", "equation", "table", "reference", "code"}

# Marker that introduces a block in chunk files and translation files: <!-- b12 | paragraph -->
MARKER_RE = re.compile(r"^[ \t]*<!--\s*(b\d+)\b[^>]*-->[ \t]*$", re.M)


def setup_stdio() -> None:
    """Make print() safe for Vietnamese text on Windows consoles (cp1252 etc.)."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
        except (AttributeError, ValueError):
            pass


def nfc(text: str) -> str:
    return unicodedata.normalize("NFC", text)


# Old-style vs new-style tone placement (hoá / hóa, thuỷ / thủy ...). Both are accepted in
# Vietnamese; for matching we map the "new" style (mark on the 2nd vowel) to the old one.
_TONE_PAIRS = {
    "oá": "óa", "oà": "òa", "oả": "ỏa", "oã": "õa", "oạ": "ọa",
    "oé": "óe", "oè": "òe", "oẻ": "ỏe", "oẽ": "õe", "oẹ": "ọe",
    "uý": "úy", "uỳ": "ùy", "uỷ": "ủy", "uỹ": "ũy", "uỵ": "ụy",
}
_TONE_RE = re.compile("|".join(map(re.escape, _TONE_PAIRS)))


def vi_key(text: str) -> str:
    """Normalise Vietnamese text for comparison: NFC, lower case, unified tone placement,
    unified dashes and whitespace."""
    t = nfc(text).lower()
    t = _TONE_RE.sub(lambda m: _TONE_PAIRS[m.group(0)], t)
    t = t.replace("‐", "-").replace("‑", "-").replace("–", "-")
    return re.sub(r"\s+", " ", t)


def load_document(workdir: Path) -> dict:
    path = Path(workdir) / DOC_FILE
    if not path.is_file():
        raise SystemExit(
            f"error: {path} not found. Run extract_pdf.py first to create the work folder.")
    doc = json.loads(path.read_text(encoding="utf-8"))
    if doc.get("format") != FORMAT:
        print(f"warning: {path} has format {doc.get('format')!r}, expected {FORMAT!r}", file=sys.stderr)
    return doc


def parse_marked_text(text: str) -> dict[str, str]:
    """Parse '<!-- b12 ... -->' separated text into {block_id: text}."""
    out: dict[str, str] = {}
    matches = list(MARKER_RE.finditer(text))
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[m.end():end]
        # Drop other HTML comments (chunk headers, notes) that may sit inside the body.
        body = re.sub(r"<!--.*?-->", "", body, flags=re.S).strip()
        out[m.group(1)] = nfc(body)
    return out


def parse_translation_json(data) -> dict[str, str]:
    """Accept {"b1": "...", ...}, {"blocks": [{"id": "b1", "vi": "..."}]} or a bare list."""
    items = data.get("blocks", data) if isinstance(data, dict) else data
    out: dict[str, str] = {}
    if isinstance(items, dict):
        for k, v in items.items():
            if re.fullmatch(r"b\d+", str(k)) and isinstance(v, str):
                out[str(k)] = nfc(v.strip())
    elif isinstance(items, list):
        for it in items:
            if isinstance(it, dict) and "id" in it:
                vi = it.get("vi", it.get("text", ""))
                if isinstance(vi, str):
                    out[str(it["id"])] = nfc(vi.strip())
    return out


def load_translations(workdir: Path) -> tuple[dict[str, str], list[str]]:
    """Read every translations/*.vi.md and *.vi.json. Returns (mapping, warnings)."""
    tdir = Path(workdir) / "translations"
    result: dict[str, str] = {}
    origin: dict[str, str] = {}
    warnings: list[str] = []
    if not tdir.is_dir():
        return result, warnings
    files = sorted(list(tdir.glob("*.md")) + list(tdir.glob("*.json")))
    for f in files:
        try:
            if f.suffix == ".json":
                part = parse_translation_json(json.loads(f.read_text(encoding="utf-8-sig")))
            else:
                part = parse_marked_text(f.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError) as e:
            warnings.append(f"{f.name}: cannot read ({e})")
            continue
        for bid, txt in part.items():
            if not txt:
                continue
            if bid in result and result[bid] != txt:
                warnings.append(f"{bid}: translated in both {origin[bid]} and {f.name}; using {f.name}")
            result[bid] = txt
            origin[bid] = f.name
    return result, warnings


def strip_heading_marks(text: str) -> str:
    return re.sub(r"^\s*#{1,6}\s+", "", text)


def word_count(text: str) -> int:
    return len(re.findall(r"\w+", text))

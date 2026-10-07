#!/usr/bin/env python3
"""PaperViet - extract an English paper (PDF, or text/markdown) into a resumable work folder.

    python extract_pdf.py paper.pdf                 # -> paper.paperviet/
    python extract_pdf.py paper.pdf --out work/ --pages 1-12 --chunk-words 1200
    python extract_pdf.py paper.txt                 # text you already have (e.g. read by the agent)

The work folder contains:
    document.json        blocks (title, authors, abstract, heading, paragraph, caption,
                         equation, table, reference, footnote) + the chunk plan
    source.md            the whole paper as structured markdown with block markers
    pages/page-001.md    cleaned text of each page (handy for "explain this passage")
    chunks/chunk-01.en.md  translation units; the agent writes translations/chunk-01.vi.md
    translations/        the agent's Vietnamese translation (one file per chunk = progress)

PDF engines: PyMuPDF (best: font sizes, bold, columns) or pypdf (pure Python, text only).
Install one of them:  pip install pymupdf   or   pip install pypdf
"""
from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pv_common import DOC_FILE, FORMAT, KEEP_TYPES, nfc, setup_stdio, word_count  # noqa: E402

EXIT_MISSING_DEPS = 3


class MissingDependency(RuntimeError):
    pass


MISSING_DEPS_MSG = """\
PaperViet: no PDF library found for Python.
Install one (PyMuPDF gives better structure detection):
    pip install pymupdf        (or: python -m pip install --user pymupdf)
    pip install pypdf          (pure Python, lighter)
No Python packages at all? Agents that can read PDFs natively (e.g. Claude Code's Read tool)
can read the PDF page by page, save the text to paper.txt (put a form-feed or a line
'--- page N ---' between pages), then run:  python extract_pdf.py paper.txt
"""

# --------------------------------------------------------------------------- lines


@dataclass
class Line:
    text: str
    page: int
    x0: float | None = None
    y0: float | None = None
    x1: float | None = None
    y1: float | None = None
    size: float | None = None
    bold: bool = False
    page_w: float | None = None
    page_h: float | None = None
    blank_before: bool = False
    md_heading: int = 0  # '#' level when the input is markdown
    footnote: bool = False

    @property
    def geo(self) -> bool:
        return self.y0 is not None


LIGATURES = {
    "ﬀ": "ff", "ﬁ": "fi", "ﬂ": "fl", "ﬃ": "ffi", "ﬄ": "ffl",
    "ﬅ": "st", "ﬆ": "st", "­": "", " ": " ", "‐": "-", "‑": "-",
    "−": "-", "​": "",
}
_LIG_RE = re.compile("|".join(map(re.escape, LIGATURES)))


def clean_text(s: str) -> str:
    s = _LIG_RE.sub(lambda m: LIGATURES[m.group(0)], nfc(s))
    return re.sub(r"[ \t]+", " ", s).strip()


# --------------------------------------------------------------------------- engines


def load_engine(name: str):
    """Return (engine_name, module). name: auto | pymupdf | pypdf."""
    tried = []
    order = ["pymupdf", "pypdf"] if name == "auto" else [name]
    for eng in order:
        try:
            if eng == "pymupdf":
                try:
                    import pymupdf as mod  # PyMuPDF >= 1.24
                except ImportError:
                    import fitz as mod  # older PyMuPDF
                if not hasattr(mod, "open"):
                    raise ImportError("pymupdf without open()")
                return eng, mod
            if eng == "pypdf":
                import pypdf as mod
                return eng, mod
            raise ValueError(f"unknown engine {eng!r}")
        except ImportError:
            tried.append(eng)
    raise MissingDependency(MISSING_DEPS_MSG)


def parse_pages(spec: str | None, n: int) -> list[int]:
    if not spec:
        return list(range(1, n + 1))
    pages: set[int] = set()
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            lo, hi = int(a or 1), int(b or n)
            pages.update(range(max(1, lo), min(n, hi) + 1))
        else:
            p = int(part)
            if 1 <= p <= n:
                pages.add(p)
    return sorted(pages)


def lines_pymupdf(mod, path: Path, pages_spec: str | None) -> tuple[list[Line], int]:
    doc = mod.open(str(path))
    n = doc.page_count
    out: list[Line] = []
    for pno in parse_pages(pages_spec, n):
        page = doc[pno - 1]
        w, h = page.rect.width, page.rect.height
        raw: list[Line] = []
        d = page.get_text("dict")
        for block in d.get("blocks", []):
            if block.get("type", 0) != 0:
                continue
            for ln in block.get("lines", []):
                spans = [s for s in ln.get("spans", []) if s.get("text", "").strip()]
                if not spans:
                    continue
                text = clean_text("".join(s["text"] for s in ln["spans"]))
                if not text:
                    continue
                weights = Counter()
                bold_chars = 0
                total = 0
                for s in spans:
                    k = len(s["text"].strip())
                    weights[round(s.get("size", 0) * 2) / 2] += k
                    is_bold = bool(s.get("flags", 0) & 16) or "bold" in s.get("font", "").lower()
                    bold_chars += k if is_bold else 0
                    total += k
                size = weights.most_common(1)[0][0] if weights else None
                x0, y0, x1, y1 = ln["bbox"]
                raw.append(Line(text, pno, x0, y0, x1, y1, size, bold_chars > total / 2, w, h))
        out.extend(order_page_lines(raw))
    doc.close()
    return out, n


def lines_pypdf(mod, path: Path, pages_spec: str | None) -> tuple[list[Line], int]:
    reader = mod.PdfReader(str(path))
    n = len(reader.pages)
    out: list[Line] = []
    for pno in parse_pages(pages_spec, n):
        try:
            txt = reader.pages[pno - 1].extract_text() or ""
        except Exception as e:  # pypdf can fail on exotic fonts; keep going
            print(f"warning: page {pno}: {e}", file=sys.stderr)
            txt = ""
        out.extend(text_to_lines(txt, pno))
    return out, n


def text_to_lines(txt: str, page: int, markdown: bool = False) -> list[Line]:
    out: list[Line] = []
    blank = False
    for raw in txt.splitlines():
        t = clean_text(raw)
        if not t:
            blank = True
            continue
        lvl = 0
        if markdown:
            m = re.match(r"^(#{1,6})\s+(.*)$", t)
            if m:
                lvl, t = len(m.group(1)), m.group(2).strip()
        out.append(Line(t, page, blank_before=blank, md_heading=lvl))
        blank = False
    return out


PAGE_SPLIT_RE = re.compile(r"\f|^-{2,}\s*page\s+\d+\s*-{2,}\s*$", re.I | re.M)


def lines_text(path: Path, pages_spec: str | None) -> tuple[list[Line], int]:
    txt = path.read_text(encoding="utf-8-sig", errors="replace")
    parts = [p for p in PAGE_SPLIT_RE.split(txt)]
    if parts and not parts[0].strip():
        parts = parts[1:]
    n = max(1, len(parts))
    md = path.suffix.lower() in (".md", ".markdown")
    out: list[Line] = []
    for pno in parse_pages(pages_spec, n):
        out.extend(text_to_lines(parts[pno - 1] if parts else "", pno, markdown=md))
    heads = [l for l in out if l.md_heading]
    if heads and heads[0] is out[0] and heads[0].md_heading == 1 \
            and sum(1 for l in heads if l.md_heading == 1) == 1:
        for l in heads[1:]:  # '# Title' then '## Section': sections become level 1
            l.md_heading = max(1, l.md_heading - 1)
    return out, n


# --------------------------------------------------------------------------- geometry


def order_page_lines(lines: list[Line]) -> list[Line]:
    """Reading order for one page: handle two-column layouts, merge same-row fragments."""
    if not lines:
        return lines
    w = lines[0].page_w or max(l.x1 for l in lines)
    mid = w / 2
    span = [l for l in lines if l.x0 < mid - 15 and l.x1 > mid + 15]
    left = [l for l in lines if l.x1 <= mid + 15 and l not in span]
    right = [l for l in lines if l.x0 >= mid - 15 and l not in span and l not in left]
    two_col = len(left) >= 6 and len(right) >= 6 and len(span) < 0.5 * (len(left) + len(right))
    if not two_col:
        return merge_rows(sorted(lines, key=lambda l: (round(l.y0), l.x0)))
    ordered: list[Line] = []
    cuts = sorted(span, key=lambda l: l.y0)
    top = -1e9
    for cut in cuts + [None]:
        bottom = cut.y0 if cut is not None else 1e9
        for col in (left, right):
            seg = [l for l in col if top <= l.y0 < bottom]
            ordered.extend(merge_rows(sorted(seg, key=lambda l: (round(l.y0), l.x0))))
        if cut is not None:
            ordered.append(cut)
            top = cut.y0
    return ordered


def merge_rows(lines: list[Line]) -> list[Line]:
    """Merge fragments printed on the same baseline (table cells, equation numbers, superscripts)."""
    rows: list[list[Line]] = []
    for l in sorted(lines, key=lambda l: l.y0):
        for row in rows[-3:]:
            r0, r1 = min(x.y0 for x in row), max(x.y1 for x in row)
            overlap = min(r1, l.y1) - max(r0, l.y0)
            hmin = max(1.0, min(r1 - r0, l.y1 - l.y0))
            if overlap > 0.5 * hmin and all(l.x0 >= x.x1 - 2 or l.x1 <= x.x0 + 2 for x in row):
                row.append(l)
                break
        else:
            rows.append([l])
    out: list[Line] = []
    for row in rows:
        row.sort(key=lambda x: x.x0)
        base = Line(**{**row[0].__dict__})
        for l in row[1:]:
            gap = l.x0 - base.x1
            sep = "  " if gap > (base.size or 10) * 0.9 else ("" if gap < 0.5 else " ")
            base.text = base.text + sep + l.text
            base.x1 = max(base.x1, l.x1)
            base.y0, base.y1 = min(base.y0, l.y0), max(base.y1, l.y1)
            if (l.size or 0) > (base.size or 0) and len(l.text) > len(base.text) / 2:
                base.size = l.size
        out.append(base)
    return out


# --------------------------------------------------------------------------- cleanup


def remove_headers_footers(lines: list[Line], n_pages: int) -> list[Line]:
    pages = {l.page for l in lines}
    np_ = max(1, len(pages))

    def key(t: str) -> str:
        return re.sub(r"\d+", "#", t.lower()).strip()

    def in_margin(l: Line) -> bool:
        if l.geo and l.page_h:
            return l.y1 < 0.08 * l.page_h or l.y0 > 0.92 * l.page_h
        return False

    # Candidate lines: geometric margins, or first/last 2 lines of a text page.
    by_page: dict[int, list[Line]] = {}
    for l in lines:
        by_page.setdefault(l.page, []).append(l)
    cands: list[Line] = []
    for pl in by_page.values():
        if pl and pl[0].geo:
            cands.extend(l for l in pl if in_margin(l))
        else:  # text mode: short lines at the very top or bottom of a page
            cands.extend(l for l in pl[:2] + pl[-2:] if len(l.text.split()) <= 10)
    counts = Counter()
    for k in {(key(l.text), l.page) for l in cands}:
        counts[k[0]] += 1
    repeated = {k for k, c in counts.items() if c >= 2 and c >= 0.5 * np_}

    pagenum = re.compile(r"^(page\s*)?\d{1,4}(\s*(of|/)\s*\d{1,4})?$", re.I)
    drop = set()
    for l in cands:
        if key(l.text) in repeated or pagenum.match(l.text):
            drop.add(id(l))
    return [l for l in lines if id(l) not in drop]


def body_size(lines: list[Line]) -> float | None:
    c = Counter()
    for l in lines:
        if l.size:
            c[l.size] += len(l.text)
    return c.most_common(1)[0][0] if c else None


def mark_footnotes(lines: list[Line], body: float | None) -> None:
    by_page: dict[int, list[Line]] = {}
    for l in lines:
        by_page.setdefault(l.page, []).append(l)
    for pl in by_page.values():
        if pl[0].geo:
            if not body:
                continue
            for l in pl:
                if l.page_h and l.y0 > 0.82 * l.page_h and l.size and l.size <= body * 0.85:
                    l.footnote = True
        else:
            # Text mode: a symbol-led line near the end of a page (*, dagger) starts a footnote.
            tail = pl[-4:]
            for k, l in enumerate(tail):
                if l.text[:1] in "*†‡" and len(l.text) > 3:
                    for x in tail[k:]:
                        x.footnote = True
                    break


# --------------------------------------------------------------------------- classification

KNOWN_SECTIONS = (
    r"abstract|introduction|background|related works?|prior work|preliminaries|"
    r"methods?|methodology|approach|proposed method|models?|materials and methods|"
    r"experiments?|experimental (?:setup|results|evaluation)|setup|results?|evaluation|"
    r"results and discussion|discussion|analysis|conclusions?|conclusion and future work|"
    r"limitations?|future work|broader impacts?|ethics statement|acknowledge?ments?|"
    r"references|bibliography|literature cited|appendix(?: [a-z])?|appendices|"
    r"supplementary materials?|data availability|author contributions|funding|"
    r"declarations?|competing interests"
)
KNOWN_RE = re.compile(
    r"^(?:(?:\d+(?:\.\d+)*|[IVX]+|[A-Z])[.)]?\s+)?(?:" + KNOWN_SECTIONS + r")\s*[.:]?$", re.I)
NUMBERED_RE = re.compile(r"^((?:\d+(?:\.\d+){0,3})|[IVX]{1,5}|[A-H])[.)]?\s+([A-Z][^\n]{1,100})$")
CAPTION_RE = re.compile(
    r"^(Figure|Fig\.|Table|Tab\.|Algorithm|Listing|Scheme|Chart|Supplementary Figure)\s*"
    r"(S?\d+[a-z]?|[IVX]+)\s*[.:|—-]", re.I)
REF_START_RE = re.compile(r"^(\[\d+\]|\d{1,3}\.\s+[A-Z]|[A-Z][A-Za-z'’\-]+,\s+(?:[A-Z]\.|[A-Z][a-z]+))")
INLINE_ABSTRACT_RE = re.compile(r"^abstract\s*[—–:.\-]\s*\S", re.I)
TERMINAL = (".", "!", "?", ":", ";")
MATH_CHARS = set("=<>+*/^_∑∏∫√≤≥≈≠∈∀∃∂"
                 "∇λθσμαβγδεπφψω"
                 "ΣΠ|{}→←×·")
NUMERIC_TOKEN = re.compile(r"^[(\[]?[-+±]?\d[\d.,%]*[)\]]?%?$|^[±×–-]$")
KEEP_HYPHEN_AFTER = {
    "tuning", "tuned", "training", "trained", "based", "art", "the", "of", "scale", "level",
    "time", "free", "specific", "aware", "driven", "order", "grained", "wise", "like", "term",
    "off", "up", "step", "shot", "supervised", "layer", "head", "end", "to", "world", "domain",
    "agnostic", "dependent", "independent", "invariant", "known", "defined", "dimensional",
}


def is_equation(t: str) -> bool:
    if len(t) > 200:
        return False
    long_words = re.findall(r"[A-Za-z]{4,}", t)
    all_words = re.findall(r"\b[A-Za-z]{2,}\b", t)
    math = sum(1 for c in t if c in MATH_CHARS)
    if re.search(r"\(\d{1,3}[a-z]?\)\s*$", t) and ("=" in t or math >= 2) and len(long_words) <= 6:
        return True
    if len(all_words) >= 8:
        return False
    return ("=" in t and math >= 3 and len(long_words) <= 3) or (math >= 5 and len(long_words) <= 2)


def is_table_line(t: str) -> bool:
    cells = [c for c in re.split(r"\s{2,}", t) if c.strip()]
    toks = t.split()
    if not toks:
        return False
    num = sum(1 for x in toks if NUMERIC_TOKEN.match(x))
    if len(cells) >= 3 and (num >= 1 or len(toks) <= 12):
        return True
    return len(toks) >= 3 and num / len(toks) >= 0.5


def heading_info(l: Line, body: float | None, in_refs: bool, in_front: bool = False) -> int:
    """Return heading level (1-3) or 0 if the line is not a heading."""
    t = l.text.strip()
    if l.md_heading:
        num = re.match(r"^(\d+(?:\.\d+)*)\.?\s", t)
        return min(3, num.group(1).count(".") + 1 if num else l.md_heading)
    if l.footnote or len(t) > 110 or len(t.split()) > 14:
        return 0
    if KNOWN_RE.match(t):
        m = re.match(r"^(\d+(?:\.\d+)*)", t)
        return min(3, m.group(1).count(".") + 1) if m else 1
    if in_refs:
        return 0
    if "  " in t or t.endswith((",", ";")) or (t.endswith(".") and not re.match(r"^\d+\.$", t)):
        return 0
    m = NUMBERED_RE.match(t)
    styled = l.geo and ((l.bold and (body is None or (l.size or 0) >= body - 0.6))
                        or (body and (l.size or 0) >= body + 0.9))
    if m and len(t.split()) <= 12:
        num = m.group(1)
        if l.geo and not styled:
            return 0
        if not num[0].isdigit() and (not l.geo or in_front):
            return 0  # "A. Author" / "I. Smith" are names, not appendix headings, in plain text
        if not l.geo and len(t) > 70:
            return 0
        if re.fullmatch(r"\d+(?:\.\d+)*", num) and int(num.split(".")[0]) > 30:
            return 0
        return min(3, num.count(".") + 1) if num[0].isdigit() else 1
    if l.geo and body and (l.size or 0) >= body * 1.15 and len(t.split()) <= 12:
        return 1
    if l.geo and l.bold and len(t.split()) <= 8 and not is_table_line(t) and t[:1].isupper():
        return 2
    return 0


def join_lines(parts: list[str]) -> str:
    out = ""
    for p in parts:
        if not out:
            out = p
            continue
        m = re.search(r"([A-Za-z]+)-$", out)
        if m and p[:1].islower():
            nxt = re.match(r"[a-z]+", p)
            word = nxt.group(0) if nxt else ""
            if word in KEEP_HYPHEN_AFTER:
                out = out + p
            else:
                out = out[:-1] + p
        else:
            out = out + " " + p
    return out.strip()


# --------------------------------------------------------------------------- blocks


def build_blocks(lines: list[Line]) -> tuple[list[dict], str]:
    body = body_size(lines)
    mark_footnotes(lines, body)
    text_lens = sorted(len(l.text) for l in lines if not l.geo) or [80]
    typical_len = text_lens[int(0.85 * (len(text_lens) - 1))]

    gaps = []
    for a, b in zip(lines, lines[1:]):
        if a.geo and b.geo and a.page == b.page and -(body or 10) < b.y0 - a.y1 < 3 * (body or 10):
            gaps.append(b.y0 - a.y1)
    base_gap = statistics.median(gaps) if gaps else 2.0

    blocks: list[dict] = []
    footnotes: list[Line] = []
    cur: dict | None = None
    cur_lines: list[str] = []
    section = ""
    state = "start"  # start -> title -> authors -> body ; abstract ; refs
    title_size = None

    # ---- title: largest text near the top of the first page (or first line in text mode)
    first_page = lines[0].page if lines else 1
    p1 = [l for l in lines if l.page == first_page and not l.footnote]
    title_ids: set[int] = set()
    if p1 and p1[0].geo and body:
        top = [l for l in p1 if l.y0 < 0.45 * (l.page_h or 800)]
        if top:
            mx = max(l.size or 0 for l in top)
            if mx >= body * 1.25:
                title_size = mx
                started = False
                for l in p1:
                    if (l.size or 0) >= mx - 0.6 and l.y0 < 0.45 * (l.page_h or 800):
                        title_ids.add(id(l))
                        started = True
                    elif started:
                        break
    elif p1:
        first = p1[0]
        if first.md_heading == 1 or (not KNOWN_RE.match(first.text) and len(first.text.split()) <= 25
                                     and not first.text.endswith(".")):
            title_ids.add(id(first))
            for l in p1[1:3]:
                if (l.text[:1].islower() or re.match(r"^(of|for|and|in|with|on|via|to|from)\b", l.text)) \
                        and not l.blank_before and len(l.text.split()) <= 12:
                    title_ids.add(id(l))
                else:
                    break

    def flush() -> None:
        nonlocal cur, cur_lines
        if cur is not None and cur_lines:
            if cur["type"] in ("table", "equation", "code", "authors"):
                cur["text"] = "\n".join(cur_lines)
            else:
                cur["text"] = join_lines(cur_lines)
            blocks.append(cur)
        cur, cur_lines = None, []
        while footnotes:
            f = footnotes.pop(0)
            blocks.append({"type": "footnote", "page": f.page, "text": f.text, "section": section})

    def start(btype: str, l: Line, **extra) -> None:
        nonlocal cur, cur_lines
        flush()
        cur = {"type": btype, "page": l.page, "section": section, **extra}
        cur_lines = [l.text]

    prev: Line | None = None
    i = 0
    while i < len(lines):
        l = lines[i]
        t = l.text
        nxt = lines[i + 1] if i + 1 < len(lines) else None

        if l.footnote:
            # Footnotes keep their own lines; continuation lines join the previous footnote.
            if footnotes and footnotes[-1].page == l.page and not t[:1] in "*†‡" \
                    and not re.match(r"^\d{1,2}\s", t):
                footnotes[-1].text += " " + t
            else:
                footnotes.append(Line(t, l.page))
            i += 1
            continue

        if id(l) in title_ids:
            if cur is None or cur["type"] != "title":
                start("title", l, level=0)
            else:
                cur_lines.append(t)
            state = "authors"
            prev = l
            i += 1
            continue

        lvl = heading_info(l, body, state == "refs", state == "authors")
        if lvl and title_size and l.size and l.size >= title_size - 0.6:
            lvl = 0
        if lvl:
            # Two-line headings: next line same style, short, not numbered.
            if cur is not None and cur["type"] == "heading" and prev is not None and prev.geo \
                    and l.geo and abs((prev.size or 0) - (l.size or 0)) < 0.3 \
                    and l.bold == prev.bold and l.page == prev.page and l.y0 - prev.y1 < base_gap + 2 \
                    and not NUMBERED_RE.match(t) and not KNOWN_RE.match(t):
                cur_lines.append(t)
                section = join_lines(cur_lines)
                prev = l
                i += 1
                continue
            name = re.sub(r"^(?:\d+(?:\.\d+)*|[IVX]+|[A-H])[.)]?\s+", "", t).strip(" .:").lower()
            start("heading", l, level=lvl)
            section = t
            if name == "abstract":
                state = "abstract"
            elif re.match(r"^(references|bibliography|literature cited)$", name):
                state = "refs"
            else:
                state = "body"
            prev = l
            i += 1
            continue

        # ---------------- non-heading lines
        new_para = cur is None or cur["type"] in ("heading", "title")
        if prev is not None and cur is not None and not new_para:
            if l.geo and prev.geo:
                if l.page != prev.page or l.y0 < prev.y0 - 1:  # new page or new column
                    new_para = cur_lines[-1].rstrip().endswith(TERMINAL) or not t[:1].islower()
                    if cur["type"] in ("table", "equation", "caption", "authors"):
                        new_para = True
                else:
                    gap = l.y0 - prev.y1
                    if gap > base_gap + 0.45 * (body or 10):
                        new_para = True
                    elif l.size and prev.size and abs(l.size - prev.size) > 1.0:
                        new_para = True
                    elif cur_lines[-1].rstrip().endswith(TERMINAL):
                        col_right = max((x.x1 for x in lines if x.page == l.page and x.geo), default=0)
                        if prev.x1 < col_right - 4 * (body or 10) or l.x0 > prev.x0 + 1.2 * (body or 10):
                            new_para = True
            else:
                if l.blank_before or l.page != prev.page and cur_lines[-1].rstrip().endswith(TERMINAL):
                    new_para = True
                elif cur_lines[-1].rstrip().endswith(TERMINAL) and len(prev.text) < 0.7 * typical_len:
                    new_para = True

        ctype = cur["type"] if cur is not None else None

        if state == "authors":
            if len(t.split()) >= 14 or INLINE_ABSTRACT_RE.match(t) or (l.geo and body and l.size and l.size < body - 1.5 and len(t.split()) > 10):
                state = "body"
            else:
                if ctype != "authors":
                    start("authors", l)
                else:
                    cur_lines.append(t)
                prev = l
                i += 1
                continue

        if state == "refs":
            if REF_START_RE.match(t) and (ctype != "reference" or cur_lines[-1].rstrip().endswith((".", "]")) or t.startswith("[")):
                start("reference", l)
            elif ctype == "reference" and not (l.blank_before and REF_START_RE.match(t)):
                cur_lines.append(t)
            else:
                start("reference", l)
            prev = l
            i += 1
            continue

        if CAPTION_RE.match(t):
            start("caption", l)
        elif is_equation(t):
            if ctype == "equation" and not new_para and prev is not None and prev.geo is l.geo:
                cur_lines.append(t)
            else:
                start("equation", l)
        elif is_table_line(t) and len(t.split()) <= 30:
            if ctype == "table":
                cur_lines.append(t)
            elif ctype == "caption" and not cur_lines[-1].rstrip().endswith(".") and not new_para:
                cur_lines.append(t)  # caption continues (rare)
            else:
                # Header row: a short previous line that is not a sentence joins the table.
                start("table", l)
        elif (nxt is not None and is_table_line(nxt.text) and len(t.split()) <= 10 and not t.endswith(TERMINAL)
              and not (ctype == "paragraph" and not new_para)
              and (i + 2 < len(lines) and is_table_line(lines[i + 2].text))):
            start("table", l)
        elif new_para or ctype in ("equation", "table"):
            if INLINE_ABSTRACT_RE.match(t) and state != "abstract":
                start("abstract", l)
                state = "abstract-inline"
            else:
                start("abstract" if state == "abstract" else "paragraph", l)
        else:
            cur_lines.append(t)
        prev = l
        i += 1
    flush()

    # Ids, keep flags, tidy titles.
    title = ""
    for n, b in enumerate(blocks, start=1):
        b["id"] = f"b{n}"
        b["keep"] = b["type"] in KEEP_TYPES
        if b["type"] == "title" and not title:
            title = b["text"]
    ordered = [{"id": b["id"], "type": b["type"], "page": b["page"], "level": b.get("level", 0),
                "keep": b["keep"], "section": b.get("section", ""), "text": b["text"]} for b in blocks]
    return ordered, title


# --------------------------------------------------------------------------- chunks & output


def plan_chunks(blocks: list[dict], target_words: int) -> list[dict]:
    chunks: list[dict] = []
    cur: list[dict] = []
    words = 0

    def close() -> None:
        nonlocal cur, words
        if cur:
            n = len(chunks) + 1
            heading = next((b["text"] for b in cur if b["type"] == "heading"), cur[0].get("section", ""))
            chunks.append({
                "id": f"chunk-{n:02d}",
                "file": f"chunks/chunk-{n:02d}.en.md",
                "translation": f"translations/chunk-{n:02d}.vi.md",
                "blocks": [b["id"] for b in cur],
                "words": sum(word_count(b["text"]) for b in cur if not b["keep"]),
                "keep_only": all(b["keep"] for b in cur),
                "heading": heading,
            })
        cur, words = [], 0

    for b in blocks:
        w = word_count(b["text"]) if not b["keep"] else 0
        is_ref_start = b["type"] == "reference" and cur and cur[-1]["type"] != "reference"
        if cur and ((b["type"] == "heading" and words >= 0.5 * target_words)
                    or words + w > target_words * 1.25 or is_ref_start):
            close()
        cur.append(b)
        words += w
    close()
    return chunks


CHUNK_HEADER = """<!-- paperviet {cid} | {n} blocks | ~{words} words to translate | {heading} -->
<!-- Translate every block below into Vietnamese and save as {tfile}.
     Keep every block-marker comment line (the one holding the block id, e.g. b12) unchanged and
     in order; replace only the English text under it.
     Blocks tagged "keep" (equations, tables, references, authors) may be omitted or copied as-is.
     Never translate math, code, variable names, citations like [3], URLs, or names. -->
"""


def block_md(b: dict) -> str:
    tag = f"<!-- {b['id']} | {b['type']}"
    if b["type"] == "heading":
        tag += f" {b['level']}"
    if b["keep"]:
        tag += " | keep"
    tag += f" | p{b['page']} -->"
    return f"{tag}\n{b['text']}\n"


def write_outputs(workdir: Path, doc: dict, page_texts: dict[int, list[str]]) -> None:
    (workdir / "pages").mkdir(parents=True, exist_ok=True)
    (workdir / "chunks").mkdir(exist_ok=True)
    (workdir / "translations").mkdir(exist_ok=True)
    for old in (workdir / "chunks").glob("chunk-*.en.md"):
        old.unlink()
    for old in (workdir / "pages").glob("page-*.md"):
        old.unlink()
    for p, lines in page_texts.items():
        (workdir / "pages" / f"page-{p:03d}.md").write_text(
            f"<!-- page {p} of {doc['pages']} -->\n" + "\n".join(lines) + "\n", encoding="utf-8")
    byid = {b["id"]: b for b in doc["blocks"]}
    for c in doc["chunks"]:
        parts = [CHUNK_HEADER.format(cid=c["id"], n=len(c["blocks"]), words=c["words"],
                                     heading=c["heading"][:80].replace("--", "-"), tfile=c["translation"])]
        parts += [block_md(byid[bid]) for bid in c["blocks"]]
        (workdir / c["file"]).write_text("\n".join(parts), encoding="utf-8")
    src = [f"<!-- paperviet source: {doc['source']} | {doc['pages']} pages | engine {doc['engine']} -->\n"]
    src += [block_md(b) for b in doc["blocks"]]
    (workdir / "source.md").write_text("\n".join(src), encoding="utf-8")
    (workdir / DOC_FILE).write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")


def extract(path: Path, workdir: Path | None = None, engine: str = "auto", pages: str | None = None,
            chunk_words: int = 1200, force: bool = False, quiet: bool = False) -> dict:
    path = Path(path)
    if not path.is_file():
        raise SystemExit(f"error: file not found: {path}")
    workdir = Path(workdir) if workdir else path.with_name(path.stem + ".paperviet")
    if (workdir / DOC_FILE).is_file() and not force:
        doc = json.loads((workdir / DOC_FILE).read_text(encoding="utf-8"))
        if not quiet:
            print(f"Already extracted: {workdir} ({len(doc['blocks'])} blocks, {len(doc['chunks'])} chunks).")
            print("Use --force to re-extract (files in translations/ are kept). "
                  "Check progress with: render.py <workdir> --status")
        return doc

    ext = path.suffix.lower()
    if ext == ".pdf":
        eng, mod = load_engine(engine)
        lines, n_pages = (lines_pymupdf if eng == "pymupdf" else lines_pypdf)(mod, path, pages)
    elif ext in (".txt", ".md", ".markdown", ".text"):
        eng = "text"
        lines, n_pages = lines_text(path, pages)
    else:
        raise SystemExit(f"error: unsupported input {path.name} (use .pdf, .txt or .md)")

    lines = remove_headers_footers(lines, n_pages)
    page_texts: dict[int, list[str]] = {}
    for l in lines:
        page_texts.setdefault(l.page, []).append(l.text)
    if not lines:
        raise SystemExit("error: no text found. The PDF may be scanned images; run OCR first "
                         "(e.g. ocrmypdf) or let the agent read the page images.")

    blocks, title = build_blocks(lines)
    chunks = plan_chunks(blocks, chunk_words)
    doc = {
        "format": FORMAT,
        "source": path.name,
        "title": title,
        "engine": eng,
        "pages": n_pages,
        "pages_extracted": sorted(page_texts),
        "created": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "chunk_words": chunk_words,
        "blocks": blocks,
        "chunks": chunks,
    }
    workdir.mkdir(parents=True, exist_ok=True)
    write_outputs(workdir, doc, page_texts)
    if not quiet:
        report(doc, workdir)
    return doc


def report(doc: dict, workdir: Path) -> None:
    types = Counter(b["type"] for b in doc["blocks"])
    words = sum(word_count(b["text"]) for b in doc["blocks"] if not b["keep"])
    print(f"PaperViet: extracted {doc['source']} with {doc['engine']} -> {workdir}")
    print(f"  title   : {doc['title'] or '(not detected)'}")
    print(f"  pages   : {len(doc['pages_extracted'])} of {doc['pages']}")
    print(f"  blocks  : {len(doc['blocks'])} (" + ", ".join(f"{k} {v}" for k, v in types.most_common()) + ")")
    print(f"  words   : ~{words} to translate")
    print(f"  chunks  : {len(doc['chunks'])}")
    for c in doc["chunks"]:
        flag = " (keep-only, nothing to translate)" if c["keep_only"] else ""
        print(f"    {c['id']}  {len(c['blocks']):3d} blocks  ~{c['words']:5d} words  {c['heading'][:50]}{flag}")
    heads = [b for b in doc["blocks"] if b["type"] == "heading"]
    if heads:
        print("  outline : " + " | ".join(h["text"][:40] for h in heads[:14]) + (" ..." if len(heads) > 14 else ""))
    print("Next: translate chunks/chunk-XX.en.md -> translations/chunk-XX.vi.md, then run render.py.")


def main(argv: list[str] | None = None) -> int:
    setup_stdio()
    ap = argparse.ArgumentParser(description="Extract a paper (PDF/TXT/MD) into a PaperViet work folder.")
    ap.add_argument("input", nargs="?", help="paper.pdf, or a .txt/.md file with the paper text")
    ap.add_argument("--out", help="work folder (default: <input-name>.paperviet next to the input)")
    ap.add_argument("--engine", choices=["auto", "pymupdf", "pypdf"], default="auto")
    ap.add_argument("--pages", help="page range, e.g. 1-8 or 1,3,5-7")
    ap.add_argument("--chunk-words", type=int, default=1200, help="target words per chunk (default 1200)")
    ap.add_argument("--force", action="store_true", help="re-extract even if the work folder exists")
    ap.add_argument("--check-deps", action="store_true", help="only report which PDF engine is available")
    args = ap.parse_args(argv)
    try:
        if args.check_deps:
            eng, mod = load_engine(args.engine)
            print(f"ok: {eng} {getattr(mod, '__version__', getattr(mod, 'VersionBind', ''))}")
            return 0
        if not args.input:
            ap.error("the input file is required")
        extract(Path(args.input), Path(args.out) if args.out else None, args.engine, args.pages,
                args.chunk_words, args.force)
    except MissingDependency as e:
        print(str(e), file=sys.stderr)
        return EXIT_MISSING_DEPS
    return 0


if __name__ == "__main__":
    sys.exit(main())

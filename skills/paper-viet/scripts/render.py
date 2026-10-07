#!/usr/bin/env python3
"""PaperViet renderer: turn a work folder into a bilingual HTML page and a Markdown file.

    python render.py paper.paperviet                 # -> paper.paperviet/<name>.vi.html + .vi.md
    python render.py paper.paperviet --status        # translation progress, next chunk to do
    python render.py paper.paperviet --html out.html --md out.md --md-mode bilingual

Inputs inside the work folder:
    document.json            from extract_pdf.py
    translations/*.vi.md     the agent's translation (block markers <!-- bNN -->), or *.vi.json
    glossary.csv             (optional) terms chosen for this paper
    doc-nhanh.vi.md          (optional) "Đọc nhanh" quick-read summary, shown at the top
                             (summary.vi.md is accepted too)
    notes.vi.md              (optional) explanations / Q&A, shown at the end

The HTML file is fully self-contained (inline CSS/JS, no network): side-by-side EN | VI,
Vietnamese-only and English-only modes, table of contents, glossary panel, light/dark theme,
adjustable font size, phone-friendly layout, print styles.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pv_common import load_document, load_translations, setup_stdio, strip_heading_marks  # noqa: E402
import glossary as gl  # noqa: E402

SKILL_DIR = Path(__file__).resolve().parent.parent
TEMPLATE = SKILL_DIR / "assets" / "viewer.html"
REPO_URL = "https://github.com/mahiepit/PaperViet"

TYPE_LABEL_VI = {
    "equation": "Công thức", "table": "Bảng", "reference": "Tài liệu tham khảo",
    "authors": "Tác giả", "code": "Mã",
}

# --------------------------------------------------------------------------- inline markup

_CITE_RE = re.compile(r"\[(\d+(?:\s*[,–\-]\s*\d+)*)\]")
_URL_RE = re.compile(r"(https?://[^\s<>()\]]+[^\s<>().,;:\]])")


def inline(text: str) -> str:
    """Escape text and apply a small, safe subset of Markdown."""
    stash: list[str] = []

    def keep(s: str) -> str:
        stash.append(s)
        return f"\x00{len(stash) - 1}\x00"

    t = text
    t = re.sub(r"`([^`\n]+)`", lambda m: keep(f"<code>{html.escape(m.group(1))}</code>"), t)
    t = re.sub(r"\$\$([^$]+)\$\$|\$([^$\n]+)\$",
               lambda m: keep(f'<span class="math">{html.escape(m.group(0))}</span>'), t)
    t = _URL_RE.sub(lambda m: keep(
        f'<a href="{html.escape(m.group(1), quote=True)}" rel="noopener noreferrer" target="_blank">'
        f"{html.escape(m.group(1))}</a>"), t)
    t = html.escape(t, quote=False)
    t = re.sub(r"\*\*(?=\S)(.+?)(?<=\S)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<![\w*])\*(?=[^\s*])([^*\n]+?)(?<=[^\s*])\*(?![\w*])", r"<em>\1</em>", t)
    t = _CITE_RE.sub(r'<span class="cite">[\1]</span>', t)
    return re.sub(r"\x00(\d+)\x00", lambda m: stash[int(m.group(1))], t)


def paragraphs(text: str) -> str:
    parts = [p.strip() for p in re.split(r"\n\s*\n", text.strip()) if p.strip()]
    return "".join(f"<p>{inline(' '.join(p.split()))}</p>" for p in parts)


def mini_markdown(md: str) -> str:
    """Tiny Markdown -> HTML for summary/notes files (headings, lists, tables, quotes, code)."""
    out: list[str] = []
    lines = md.replace("\r\n", "\n").split("\n")
    i = 0
    para: list[str] = []

    def flush_para() -> None:
        if para:
            out.append(f"<p>{inline(' '.join(x.strip() for x in para))}</p>")
            para.clear()

    while i < len(lines):
        ln = lines[i]
        s = ln.strip()
        if not s:
            flush_para()
            i += 1
            continue
        if s.startswith("```"):
            flush_para()
            j = i + 1
            buf = []
            while j < len(lines) and not lines[j].strip().startswith("```"):
                buf.append(lines[j])
                j += 1
            out.append(f"<pre>{html.escape(chr(10).join(buf))}</pre>")
            i = j + 1
            continue
        m = re.match(r"^(#{1,6})\s+(.*)$", s)
        if m:
            flush_para()
            lvl = min(6, len(m.group(1)) + 1)
            out.append(f"<h{lvl}>{inline(m.group(2))}</h{lvl}>")
            i += 1
            continue
        if s.startswith("|") and i + 1 < len(lines) and re.match(r"^\s*\|?\s*:?-{2,}", lines[i + 1]):
            flush_para()
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            head, body = rows[0], rows[2:]
            t = "<table><thead><tr>" + "".join(f"<th>{inline(c)}</th>" for c in head) + "</tr></thead><tbody>"
            t += "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>" for r in body)
            out.append(t + "</tbody></table>")
            continue
        if re.match(r"^([-*+]|\d+[.)])\s+", s):
            flush_para()
            ordered = bool(re.match(r"^\d", s))
            items = []
            while i < len(lines) and re.match(r"^\s*([-*+]|\d+[.)])\s+", lines[i]):
                item = re.sub(r"^\s*([-*+]|\d+[.)])\s+", "", lines[i])
                i += 1
                while i < len(lines) and lines[i].startswith(("  ", "\t")) and lines[i].strip() \
                        and not re.match(r"^\s*([-*+]|\d+[.)])\s+", lines[i]):
                    item += " " + lines[i].strip()
                    i += 1
                items.append(f"<li>{inline(item)}</li>")
            tag = "ol" if ordered else "ul"
            out.append(f"<{tag}>{''.join(items)}</{tag}>")
            continue
        if s.startswith(">"):
            flush_para()
            buf = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                buf.append(lines[i].strip()[1:].strip())
                i += 1
            out.append(f"<blockquote>{paragraphs(chr(10).join(buf))}</blockquote>")
            continue
        para.append(s)
        i += 1
    flush_para()
    return "\n".join(out)


# --------------------------------------------------------------------------- model


def load_all(workdir: Path, extra_glossary: list[str] | None = None) -> dict:
    doc = load_document(workdir)
    tr, warnings = load_translations(workdir)
    known = {b["id"] for b in doc["blocks"]}
    unknown = sorted(set(tr) - known, key=lambda x: int(x[1:]))
    if unknown:
        warnings.append("translations for unknown block ids (ignored): " + ", ".join(unknown[:12]))
    text = "\n".join(b["text"] for b in doc["blocks"] if not b["keep"])
    entries = gl.load_glossary(extra_glossary, workdir)
    counts = gl.Matcher(entries).find(text)
    terms = []
    for key, n in counts.most_common():
        e = entries[key]
        if e.get("source") != "paper" and gl.is_generic(e):
            continue
        terms.append({**e, "count": n})
    found = {t["en"].lower() for t in terms}
    for e in entries.values():  # paper glossary entries always appear, even with 0 matches
        if e.get("source") == "paper" and e["en"].lower() not in found:
            terms.append({**e, "count": 0})
    terms.sort(key=lambda t: (t.get("source") != "paper", t["en"].lower()))
    read = lambda name: (workdir / name).read_text(encoding="utf-8-sig") if (workdir / name).is_file() else ""  # noqa: E731
    return {"doc": doc, "tr": tr, "warnings": warnings, "terms": terms,
            "summary": read("doc-nhanh.vi.md") or read("summary.vi.md"), "notes": read("notes.vi.md")}


def progress(doc: dict, tr: dict) -> dict:
    todo = [b for b in doc["blocks"] if not b["keep"]]
    done = [b for b in todo if tr.get(b["id"])]
    chunks = []
    byid = {b["id"]: b for b in doc["blocks"]}
    for c in doc["chunks"]:
        need = [bid for bid in c["blocks"] if bid in byid and not byid[bid]["keep"]]
        have = [bid for bid in need if tr.get(bid)]
        state = "keep-only" if not need else ("done" if len(have) == len(need) else
                                              ("partial" if have else "todo"))
        chunks.append({**c, "need": len(need), "have": len(have), "state": state,
                       "missing": [bid for bid in need if not tr.get(bid)]})
    return {"total": len(todo), "done": len(done), "chunks": chunks,
            "words_total": sum(c["words"] for c in doc["chunks"]),
            "words_done": sum(c["words"] for c in chunks if c["state"] == "done")}


def print_status(workdir: Path, data: dict) -> None:
    doc, tr = data["doc"], data["tr"]
    p = progress(doc, tr)
    pct = 100 * p["done"] / max(1, p["total"])
    print(f"PaperViet status: {workdir}")
    print(f"  {doc.get('title') or doc['source']}")
    print(f"  translated blocks: {p['done']}/{p['total']} ({pct:.0f}%)")
    for c in p["chunks"]:
        extra = ""
        if c["state"] == "partial":
            extra = "  missing: " + ", ".join(c["missing"][:10]) + (" ..." if len(c["missing"]) > 10 else "")
        print(f"  {c['id']}  {c['state']:<9} {c['have']:3d}/{c['need']:<3d} ~{c['words']:5d} words  "
              f"{c['heading'][:40]}{extra}")
    nxt = next((c for c in p["chunks"] if c["state"] in ("todo", "partial")), None)
    if nxt:
        print(f"Next: translate {nxt['file']} -> {nxt['translation']}")
    else:
        print("All chunks translated. Run: render.py <workdir>  (and glossary.py check <workdir>)")
    for w in data["warnings"]:
        print(f"  warning: {w}")
    print(f"  doc-nhanh.vi.md (summary): {'yes' if data['summary'] else 'no'} | glossary.csv: "
          f"{'yes' if (workdir / 'glossary.csv').is_file() else 'no'}")


# --------------------------------------------------------------------------- HTML


def table_html(text: str) -> str:
    """Render 'cell  cell  cell' rows (2+ spaces between cells) as a table when the column
    count is consistent; otherwise fall back to preformatted text."""
    rows = [re.split(r"\s{2,}|\t", ln.strip()) for ln in text.strip().split("\n") if ln.strip()]
    ncol = len(rows[0]) if rows else 0
    if len(rows) >= 2 and ncol >= 2 and all(len(r) == ncol for r in rows):
        head = "".join(f"<th>{html.escape(c)}</th>" for c in rows[0])
        body = "".join("<tr>" + "".join(f"<td>{html.escape(c)}</td>" for c in r) + "</tr>" for r in rows[1:])
        return f'<div class="tbl"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'
    return f'<pre class="verbatim">{html.escape(text)}</pre>'


def render_block(b: dict, vi: str | None) -> str:
    bid, t = b["id"], b["type"]
    cls = f"row t-{t}"
    if t == "heading":
        lvl = min(4, max(2, b.get("level", 1) + 1))
        en = html.escape(b["text"])
        vi_html = inline(strip_heading_marks(vi)) if vi else '<span class="missing">Chưa dịch</span>'
        return (f'<div class="{cls}" id="{bid}"><h{lvl} class="en" lang="en">{en}</h{lvl}>'
                f'<h{lvl} class="vi" lang="vi">{vi_html}</h{lvl}></div>')
    if b["keep"]:
        label = TYPE_LABEL_VI.get(t, "")
        if t == "table":
            body = table_html(b["text"])
        elif t in ("equation", "code"):
            body = f'<pre class="verbatim">{html.escape(b["text"])}</pre>'
        elif t == "authors":
            body = "".join(f"<p>{html.escape(x)}</p>" for x in b["text"].split("\n"))
        else:
            body = f"<p>{inline(b['text'])}</p>"
        if vi and t in ("table", "code", "equation"):
            vbody = table_html(vi) if t == "table" else f'<pre class="verbatim">{html.escape(vi)}</pre>'
            return (f'<div class="{cls}" id="{bid}"><div class="en" lang="en">{body}</div>'
                    f'<div class="vi" lang="vi">{vbody}</div></div>')
        if vi:
            return (f'<div class="{cls}" id="{bid}"><div class="en" lang="en">{body}</div>'
                    f'<div class="vi" lang="vi">{paragraphs(vi)}</div></div>')
        return f'<div class="{cls} full" id="{bid}" title="{label}"><div class="both">{body}</div></div>'
    en = paragraphs(b["text"])
    vi_html = paragraphs(vi) if vi else '<p><span class="missing">Chưa dịch</span></p>'
    return (f'<div class="{cls}" id="{bid}"><div class="en" lang="en">{en}</div>'
            f'<div class="vi" lang="vi">{vi_html}</div></div>')


def build_html(data: dict, summary_only: bool = False) -> str:
    doc, tr = data["doc"], data["tr"]
    blocks = [] if summary_only else doc["blocks"]
    p = progress(doc, tr)
    title_b = next((b for b in doc["blocks"] if b["type"] == "title"), None)
    title_en = doc.get("title") or (title_b["text"] if title_b else doc["source"])
    title_vi = tr.get(title_b["id"]) if title_b else None
    authors_b = next((b for b in doc["blocks"][:4] if b["type"] == "authors"), None)
    authors = "".join(f"<span>{html.escape(x)}</span>" for x in authors_b["text"].split("\n")) if authors_b else ""

    toc = []
    rows = []
    for b in blocks:
        if b is title_b or b is authors_b:
            continue
        vi = tr.get(b["id"])
        rows.append(render_block(b, vi))
        if b["type"] == "heading":
            label = strip_heading_marks(vi) if vi else b["text"]
            toc.append(f'<li class="l{b.get("level", 1)}"><a href="#{b["id"]}">{inline(label)}</a></li>')

    gloss_rows = "".join(
        f'<tr data-k="{html.escape((t["en"] + " " + " ".join(t["vi"])).lower(), quote=True)}">'
        f'<td lang="en">{html.escape(t["en"])}</td><td lang="vi"><b>{html.escape(t["vi"][0])}</b>'
        + (f'<br><small>{html.escape(", ".join(t["vi"][1:]))}</small>' if len(t["vi"]) > 1 else "")
        + f'</td><td>{t["count"] or ""}</td></tr>'
        for t in data["terms"])

    summary = ""
    if data["summary"].strip():
        summary = (f'<details class="quick" open><summary>Đọc nhanh</summary>'
                   f'<div class="md">{mini_markdown(data["summary"])}</div></details>')
    notes = ""
    if data["notes"].strip():
        notes = (f'<section class="notes" id="ghi-chu"><h2>Ghi chú &amp; giải thích</h2>'
                 f'<div class="md">{mini_markdown(data["notes"])}</div></section>')
        toc.append('<li class="l1"><a href="#ghi-chu">Ghi chú &amp; giải thích</a></li>')

    pct = round(100 * p["done"] / max(1, p["total"]))
    pages = f"{doc['pages']} trang" if doc.get("pages") else ""
    meta = " · ".join(x for x in [html.escape(doc["source"]), pages,
                                  f"đã dịch {p['done']}/{p['total']} khối ({pct}%)"] if x)
    tpl = TEMPLATE.read_text(encoding="utf-8")
    repl = {
        "{{TITLE}}": html.escape(title_vi or title_en),
        "{{TITLE_VI}}": inline(title_vi) if title_vi else html.escape(title_en),
        "{{TITLE_EN}}": html.escape(title_en) if title_vi else "",
        "{{AUTHORS}}": authors,
        "{{META}}": meta,
        "{{PCT}}": str(pct),
        "{{SUMMARY}}": summary,
        "{{BLOCKS}}": "\n".join(rows),
        "{{NOTES}}": notes,
        "{{TOC}}": "\n".join(toc) or "<li>(không có mục)</li>",
        "{{GLOSSARY_ROWS}}": gloss_rows or '<tr><td colspan="3">(chưa có thuật ngữ)</td></tr>',
        "{{TERM_COUNT}}": str(len(data["terms"])),
        "{{GENERATED}}": datetime.now().strftime("%Y-%m-%d"),
        "{{REPO_URL}}": REPO_URL,
    }
    # Single pass, so text inside translations is never re-interpreted as a placeholder.
    return re.sub(r"\{\{[A-Z_]+\}\}", lambda m: repl.get(m.group(0), m.group(0)), tpl)


# --------------------------------------------------------------------------- Markdown


def build_markdown(data: dict, mode: str = "vi", summary_only: bool = False) -> str:
    doc, tr = data["doc"], data["tr"]
    blocks = [] if summary_only else doc["blocks"]
    title_b = next((b for b in doc["blocks"] if b["type"] == "title"), None)
    title_en = doc.get("title") or doc["source"]
    title_vi = tr.get(title_b["id"]) if title_b else None
    p = progress(doc, tr)
    out = [f"# {title_vi or title_en}", ""]
    if title_vi:
        out += [f"*{title_en}*", ""]
    authors_b = next((b for b in doc["blocks"][:4] if b["type"] == "authors"), None)
    if authors_b:
        out += ["  \n".join(authors_b["text"].split("\n")), ""]
    out += [f"> Bản dịch tiếng Việt của `{doc['source']}` ({p['done']}/{p['total']} khối đã dịch), "
            f"tạo bằng [PaperViet]({REPO_URL}). Bản dịch do AI thực hiện; hãy đối chiếu bản gốc khi trích dẫn.", ""]
    if data["summary"].strip():
        out += ["## Đọc nhanh", "", re.sub(r"^(#{1,5})\s", r"#\1 ", data["summary"].strip(), flags=re.M), ""]
    for b in blocks:
        if b is title_b or b is authors_b:
            continue
        vi = tr.get(b["id"])
        t = b["type"]
        if t == "heading":
            hashes = "#" * min(5, b.get("level", 1) + 1)
            out += [f"{hashes} {strip_heading_marks(vi) if vi else b['text']}", ""]
            if mode == "bilingual" and vi:
                out += [f"<sub>{b['text']}</sub>", ""]
            continue
        if b["keep"] and not vi:
            if t in ("equation", "table", "code"):
                out += ["```text", b["text"], "```", ""]
            elif t == "reference":
                out += [f"- {b['text']}", ""]
            elif t == "authors":
                out += ["  \n".join(b["text"].split("\n")), ""]
            else:
                out += [b["text"], ""]
            continue
        if b["keep"] and vi and t in ("equation", "table", "code"):
            out += ["```text", vi, "```", ""]
            continue
        text = vi if vi else f"{b['text']} *(chưa dịch)*"
        if t == "caption":
            text = f"*{text}*"
        if t == "footnote":
            text = f"<small>{text}</small>"
        out += [text, ""]
        if mode == "bilingual" and vi:
            out += ["> " + b["text"].replace("\n", "\n> "), ""]
    if data["notes"].strip():
        out += ["## Ghi chú & giải thích", "", re.sub(r"^(#{1,5})\s", r"#\1 ", data["notes"].strip(), flags=re.M), ""]
    if data["terms"]:
        out += ["## Thuật ngữ", "", "| English | Tiếng Việt |", "|---|---|"]
        out += [f"| {t['en']} | {t['vi'][0]} |" for t in data["terms"]]
        out.append("")
    return re.sub(r"\n{3,}", "\n\n", "\n".join(out)).strip() + "\n"


# --------------------------------------------------------------------------- CLI


def render(workdir: Path, html_out: Path | None = None, md_out: Path | None = None,
           md_mode: str = "vi", extra_glossary: list[str] | None = None, quiet: bool = False,
           summary_only: bool = False) -> dict:
    workdir = Path(workdir)
    data = load_all(workdir, extra_glossary)
    stem = Path(data["doc"]["source"]).stem
    html_out = Path(html_out) if html_out else workdir / f"{stem}.vi.html"
    md_out = Path(md_out) if md_out else workdir / f"{stem}.vi.md"
    html_out.parent.mkdir(parents=True, exist_ok=True)
    md_out.parent.mkdir(parents=True, exist_ok=True)
    html_out.write_text(build_html(data, summary_only), encoding="utf-8")
    md_out.write_text(build_markdown(data, md_mode, summary_only), encoding="utf-8")
    if not quiet:
        p = progress(data["doc"], data["tr"])
        print(f"PaperViet: rendered {p['done']}/{p['total']} translated blocks")
        print(f"  HTML     : {html_out}")
        print(f"  Markdown : {md_out}")
        for w in data["warnings"]:
            print(f"  warning: {w}")
        if p["done"] < p["total"]:
            print("  note: some blocks are not translated yet (shown as 'Chưa dịch'). See --status.")
    return {"html": html_out, "md": md_out, "data": data}


def main(argv: list[str] | None = None) -> int:
    setup_stdio()
    ap = argparse.ArgumentParser(description="Render a PaperViet work folder to bilingual HTML + Markdown.")
    ap.add_argument("workdir")
    ap.add_argument("--html", help="output HTML path (default: <workdir>/<name>.vi.html)")
    ap.add_argument("--md", help="output Markdown path (default: <workdir>/<name>.vi.md)")
    ap.add_argument("--md-mode", choices=["vi", "bilingual"], default="vi")
    ap.add_argument("--glossary", action="append", default=[], help="extra glossary CSV (repeatable)")
    ap.add_argument("--status", action="store_true", help="only print translation progress")
    ap.add_argument("--summary-only", action="store_true",
                    help="quick-read mode: render title, doc-nhanh.vi.md, notes and glossary without the full text")
    ap.add_argument("--json", action="store_true", help="with --status: machine-readable output")
    a = ap.parse_args(argv)
    workdir = Path(a.workdir)
    if a.status:
        data = load_all(workdir, a.glossary)
        if a.json:
            p = progress(data["doc"], data["tr"])
            print(json.dumps({"done": p["done"], "total": p["total"], "warnings": data["warnings"],
                              "chunks": [{k: c[k] for k in ("id", "state", "have", "need", "file",
                                                            "translation", "missing")} for c in p["chunks"]]},
                             ensure_ascii=False, indent=1))
        else:
            print_status(workdir, data)
        return 0
    render(workdir, Path(a.html) if a.html else None, Path(a.md) if a.md else None, a.md_mode, a.glossary,
           summary_only=a.summary_only)
    return 0


if __name__ == "__main__":
    sys.exit(main())

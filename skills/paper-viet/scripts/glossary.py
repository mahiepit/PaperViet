#!/usr/bin/env python3
"""PaperViet glossary tool: look up terms, merge glossaries, check a translation.

    python glossary.py lookup  paper.paperviet [--write]     # terms that occur in the paper
    python glossary.py lookup  chunks/chunk-03.en.md         # terms in one chunk
    python glossary.py show    "learning rate"               # search the glossary (EN or VI)
    python glossary.py check   paper.paperviet [--json] [--strict]
    python glossary.py merge   --glossary my.csv --out merged.csv

Glossary files are CSV (UTF-8) with columns  en,vi,domain,note.  Several Vietnamese
variants may be given in `vi`, separated by "|"; the first one is preferred.
Load order (later files override earlier ones for the same English term):
  1. built-in  references/glossary.csv
  2. ~/.paperviet/glossary.csv                (your personal glossary, if it exists)
  3. files listed in $PAPERVIET_GLOSSARY       (separated by ; on Windows, : elsewhere)
  4. --glossary FILE (repeatable)
  5. <workdir>/glossary.csv                   (the glossary chosen for this paper)
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pv_common import (DOC_FILE, load_document, load_translations, nfc, setup_stdio,  # noqa: E402
                       vi_key, word_count)

SKILL_DIR = Path(__file__).resolve().parent.parent
BUILTIN = SKILL_DIR / "references" / "glossary.csv"
USER_DEFAULT = Path.home() / ".paperviet" / "glossary.csv"

# Single words that are too common to be checked or suggested automatically. They stay in
# the glossary for `show`, and are checked when a paper glossary lists them explicitly.
GENERIC = {
    "abstract", "introduction", "background", "method", "approach", "experiment", "result",
    "discussion", "conclusion", "limitation", "contribution", "evaluation", "metric", "variable",
    "set", "function", "limit", "series", "graph", "tree", "stack", "queue", "market", "edge",
    "cell", "agent", "environment", "label", "layer", "weight", "mean", "rank", "basis", "norm",
    "node", "stock", "bond", "capital", "labor", "supply", "demand", "firm", "organ", "sequence",
    "dimension", "training", "parameter", "feature", "memory", "library", "treatment", "policy",
    "prediction", "token", "approximation", "equation", "definition", "proof", "profit",
    "revenue", "disease", "patient", "symptom", "species", "tissue", "dose", "welfare",
    "utility", "bias", "inference", "population", "theorem", "lemma", "proposition",
    "corollary", "conjecture", "axiom", "hypothesis", "assumption", "simulation", "survey",
    "references", "appendix", "acknowledgments", "reward", "empirical", "theoretical",
    "investment", "asset", "household", "therapy", "diagnosis", "protocol", "privacy",
    "database", "precision", "recall", "sensitivity", "similarity", "exploration",
    "exploitation", "constraint", "integral", "baseline", "benchmark", "chronic", "acute",
    "incidence", "incentive", "equilibrium", "inequality", "convergence", "liability",
}

# --------------------------------------------------------------------------- loading


def read_csv(path: Path, source: str | None = None) -> list[dict]:
    rows: list[dict] = []
    text = Path(path).read_text(encoding="utf-8-sig")
    lines = [ln for ln in text.splitlines() if ln.strip() and not ln.lstrip().startswith("#")]
    for row in csv.DictReader(lines):
        en = nfc((row.get("en") or "").strip())
        vi = [nfc(v.strip()) for v in (row.get("vi") or "").split("|") if v.strip()]
        if not en or not vi:
            continue
        rows.append({"en": en, "vi": vi, "domain": (row.get("domain") or "").strip(),
                     "note": (row.get("note") or "").strip(), "source": source or Path(path).name})
    return rows


def glossary_paths(extra: list[str] | None = None, workdir: Path | None = None,
                   builtin: bool = True) -> list[Path]:
    paths: list[Path] = []
    if builtin:
        paths.append(BUILTIN)
    if USER_DEFAULT.is_file():
        paths.append(USER_DEFAULT)
    env = os.environ.get("PAPERVIET_GLOSSARY", "")
    paths += [Path(p) for p in env.split(os.pathsep) if p.strip()]
    paths += [Path(p) for p in (extra or [])]
    if workdir is not None and (Path(workdir) / "glossary.csv").is_file():
        paths.append(Path(workdir) / "glossary.csv")
    return paths


def load_glossary(extra: list[str] | None = None, workdir: Path | None = None,
                  builtin: bool = True) -> dict[str, dict]:
    """Return {en_lower: entry}; later files override earlier ones."""
    merged: dict[str, dict] = {}
    for p in glossary_paths(extra, workdir, builtin):
        if not p.is_file():
            print(f"warning: glossary file not found: {p}", file=sys.stderr)
            continue
        src = "paper" if workdir is not None and p == Path(workdir) / "glossary.csv" else \
            ("builtin" if p == BUILTIN else p.name)
        for e in read_csv(p, src):
            merged[e["en"].lower()] = e
    return merged


# --------------------------------------------------------------------------- matching


def _term_pattern(term: str) -> str:
    parts = [p for p in re.split(r"(\s+|-)", term) if p]
    out = []
    last = len(parts) - 1
    for i, p in enumerate(parts):
        if p.isspace():
            out.append(r"[\s\-]+")
        elif p == "-":
            out.append(r"[\s\-]?")
        else:
            w = re.escape(p)
            if i == last and p.isalpha() and p.islower() and len(p) > 2:
                if re.search(r"[^aeiou]y$", p):
                    w = re.escape(p[:-1]) + r"(?:y|ies)"
                elif re.search(r"(s|x|ch|sh)$", p):
                    w += r"(?:es)?"
                else:
                    w += r"(?:s|es)?"
            out.append(w)
    pat = "".join(out)
    if any(c.isupper() for c in term) and term.upper() == term:
        pat = f"(?-i:{pat})"  # acronyms such as DNA are case-sensitive
    return pat


class Matcher:
    def __init__(self, entries: dict[str, dict]):
        self.entries = entries
        keys = sorted(entries, key=lambda k: (-len(k), k))
        self.keys = keys
        if keys:
            alts = "|".join(f"(?P<t{i}>{_term_pattern(entries[k]['en'])})" for i, k in enumerate(keys))
            self.rx = re.compile(r"(?<![\w-])(?:" + alts + r")(?![\w-])", re.I)
        else:
            self.rx = None

    def find(self, text: str) -> Counter:
        c: Counter = Counter()
        if not self.rx:
            return c
        for m in self.rx.finditer(text):
            name = m.lastgroup
            if name:
                c[self.keys[int(name[1:])]] += 1
        return c


def vi_variant_hits(entry: dict, vi_text: str) -> list[int]:
    t = vi_key(vi_text)
    hits = []
    for i, v in enumerate(entry["vi"]):
        if re.search(r"(?<!\w)" + re.escape(vi_key(v)) + r"(?!\w)", t):
            hits.append(i)
    return hits


def only_in_names(term: str, text: str) -> bool:
    """True if every occurrence of `term` in `text` sits inside a Title-Case name such as
    'Sparse Curriculum Sampling' (a method/model name that is legitimately kept in English)."""
    occ = list(re.finditer(r"(?<![\w-])" + re.escape(term) + r"\w*", text, re.I))
    if not occ:
        return False
    for m in occ:
        word = m.group(0)
        before = re.findall(r"[\w-]+", text[:m.start()])[-1:] or [""]
        if not (word[:1].isupper() and before[0][:1].isupper() and before[0].isascii()):
            return False
    return True


def is_generic(entry: dict) -> bool:
    return entry["en"].lower() in GENERIC and entry.get("source") != "paper"


# --------------------------------------------------------------------------- lookup


def source_text_of(target: Path) -> tuple[str, Path | None]:
    target = Path(target)
    if target.is_dir():
        doc = load_document(target)
        return "\n".join(b["text"] for b in doc["blocks"] if not b["keep"]), target
    text = target.read_text(encoding="utf-8-sig")
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    return text, None


def lookup(target: Path, extra: list[str] | None = None, include_generic: bool = False,
           domains: set[str] | None = None) -> list[dict]:
    text, workdir = source_text_of(target)
    if workdir is None:  # a chunk file inside a workdir: use the paper glossary too
        wd = Path(target).resolve().parent.parent
        workdir = wd if (wd / DOC_FILE).is_file() else None
    entries = load_glossary(extra, workdir)
    counts = Matcher(entries).find(text)
    out = []
    for key, n in counts.most_common():
        e = entries[key]
        if not include_generic and is_generic(e):
            continue
        if domains and e["domain"] not in domains and e.get("source") != "paper":
            continue
        out.append({**e, "count": n})
    return out


def write_paper_glossary(workdir: Path, found: list[dict]) -> tuple[Path, int]:
    path = Path(workdir) / "glossary.csv"
    existing = {e["en"].lower() for e in read_csv(path)} if path.is_file() else set()
    new = [e for e in found if e["en"].lower() not in existing]
    write_header = not path.is_file()
    with path.open("a", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        if write_header:
            w.writerow(["en", "vi", "domain", "note"])
        for e in new:
            w.writerow([e["en"], e["vi"][0], e["domain"], e["note"]])
    return path, len(new)


# --------------------------------------------------------------------------- check

NUM_RE = re.compile(r"(?<![\w.])[-+]?\d+(?:[.,]\d+)*(?:[eE][-+]?\d+)?%?")
CITE_RE = re.compile(r"\[\d+(?:\s*[,–\-]\s*\d+)*\]")
AUTHOR_YEAR_RE = re.compile(
    r"\b([A-Z][A-Za-z'\-]+)(?: et al\.?| and [A-Z][A-Za-z'\-]+)?(?:,\s*|\s+\()(\d{4}[a-z]?)\b")
EN_STOPWORDS = re.compile(r"(?<!\w)(?:the|and|of|to|is|are|with|that|this|which|we|our|from)(?!\w)", re.I)
INLINE_MATH_RE = re.compile(r"\$[^$\n]{1,200}\$")
INLINE_CODE_RE = re.compile(r"`[^`\n]{1,200}`")
URL_RE = re.compile(r"https?://[^\s)\]>]+")
STYLE_RULES = [
    (re.compile(r"(?<!\w)một cách(?!\w)", re.I), "calque",
     "'một cách + tính từ' thường là dịch máy từ '-ly'; bỏ 'một cách' hoặc viết lại"),
    (re.compile(r"(?<!\w)được(?!\w)[^.;:!?\n]{1,60}?(?<!\w)bởi(?!\w)", re.I), "passive",
     "câu bị động 'được ... bởi'; ưu tiên câu chủ động hoặc 'do ... (thực hiện)'"),
    (re.compile(r"(?:^|[.!?]\s+)Nó(?!\w)"), "pronoun",
     "câu bắt đầu bằng 'Nó' (dịch từ 'It'); hãy lặp lại danh từ hoặc dùng 'phương pháp này'..."),
    (re.compile(r"(?<!\w)(?:cái|chiếc) (?:mô hình|phương pháp|thuật toán)", re.I), "article",
     "không cần dịch mạo từ 'the/a' thành 'cái/chiếc'"),
]


def _norm_num(s: str) -> str:
    """'1,000' / '1.000' / '1 000' -> '1000'; '0.9' and '0,9' -> '09'; '2e-5' -> '2e-5'."""
    mant, _, exp = s.lower().rstrip("%").partition("e")
    return re.sub(r"\D", "", mant) + ("e" + exp.lstrip("+") if exp else "")


def preservation_issues(en: str, vi: str) -> list[tuple[str, str]]:
    issues = []
    vi_nums = {_norm_num(x) for x in NUM_RE.findall(vi)}
    missing = []
    for raw in NUM_RE.findall(en):
        n = _norm_num(raw)
        if len(n) < 2:  # single digits may legitimately become words ("two" -> "hai")
            continue
        if n not in vi_nums and raw not in vi:
            missing.append(raw)
    if missing:
        issues.append(("number", "số liệu có trong bản gốc nhưng không thấy trong bản dịch: "
                       + ", ".join(sorted(set(missing)))))
    squash = re.sub(r"\s+", "", vi)
    lost = [c for c in CITE_RE.findall(en) if re.sub(r"\s+", "", c) not in squash]
    if lost:
        issues.append(("citation", "trích dẫn bị mất: " + ", ".join(dict.fromkeys(lost))))
    ay = [f"{a} {y}" for a, y in AUTHOR_YEAR_RE.findall(en) if a not in ("In", "The", "Table", "Figure", "Section")
          and (a not in vi or y not in vi)]
    if ay:
        issues.append(("citation", "trích dẫn tác giả-năm có thể bị mất: " + ", ".join(dict.fromkeys(ay))))
    for rx, what in ((INLINE_MATH_RE, "công thức"), (INLINE_CODE_RE, "mã"), (URL_RE, "URL")):
        lost = [x for x in rx.findall(en) if x not in vi]
        if lost:
            issues.append(("verbatim", f"{what} phải giữ nguyên: " + ", ".join(dict.fromkeys(lost))))
    return issues


def style_issues(en: str, vi: str) -> list[tuple[str, str]]:
    issues = []
    for rx, code, msg in STYLE_RULES:
        found = [m.group(0).strip(" .!?") for m in rx.finditer(vi)]
        if found:
            issues.append((code, f"{msg} (vd: \"{found[0][:50]}\")"))
    n_viec = len(re.findall(r"(?<!\w)(?:việc|sự)(?!\w)", vi, re.I))
    if n_viec >= 3 and n_viec * 30 > word_count(vi):
        issues.append(("nominal", f"lạm dụng 'việc/sự' ({n_viec} lần); thử dùng động từ trực tiếp"))
    if re.search(r"(?<!\w)we(?!\w)", en, re.I) and re.search(r"(?<!\w)chúng ta(?!\w)", vi, re.I):
        issues.append(("we", "tác giả tự xưng 'we' nên dịch là 'chúng tôi'; 'chúng ta' chỉ dùng khi gộp cả người đọc"))
    stop = len(EN_STOPWORDS.findall(re.sub(r"\([^)]*\)", "", vi)))
    if stop >= 3 and stop > 0.08 * word_count(vi):
        issues.append(("untranslated", "đoạn này có vẻ còn nhiều tiếng Anh chưa dịch"))
    return issues


def check(workdir: Path, extra: list[str] | None = None, all_terms: bool = False) -> dict:
    workdir = Path(workdir)
    doc = load_document(workdir)
    tr, tr_warnings = load_translations(workdir)
    entries = load_glossary(extra, workdir)
    matcher = Matcher(entries)
    issues: list[dict] = []
    usage: dict[str, dict[int, list[str]]] = defaultdict(lambda: defaultdict(list))
    first_seen: dict[str, str] = {}

    def add(level: str, code: str, block: str | None, msg: str, term: str | None = None) -> None:
        issues.append({"level": level, "code": code, "block": block, "term": term, "message": msg})

    for w in tr_warnings:
        add("warn", "duplicate", None, w)

    has_paper = any(e.get("source") == "paper" for e in entries.values())
    todo = [b for b in doc["blocks"] if not b["keep"]]
    translated = 0
    for b in todo:
        vi = tr.get(b["id"])
        if not vi:
            continue
        translated += 1
        en = b["text"]
        for key, _n in matcher.find(en).items():
            e = entries[key]
            if not all_terms and is_generic(e):
                continue
            hits = vi_variant_hits(e, vi)
            if key not in first_seen and b["type"] not in ("title", "heading"):
                first_seen[key] = b["id"]
                vi_pref = e["vi"][0]
                wanted = e.get("source") == "paper" or not has_paper
                if wanted and vi_key(vi_pref) != vi_key(e["en"]) and e["en"].lower() not in vi.lower() and hits:
                    add("info", "first-use", b["id"],
                        f"lần đầu xuất hiện: nên ghi '{e['vi'][hits[0]]} ({e['en']})'", e["en"])
            if hits:
                for h in hits:
                    usage[key][h].append(b["id"])
            elif re.search(r"(?<![\w-])" + re.escape(e["en"]) + r"", vi, re.I):
                if e.get("source") == "paper" and not only_in_names(e["en"], vi):
                    add("warn", "kept-english", b["id"],
                        f"'{e['en']}' được giữ tiếng Anh nhưng thuật ngữ của bài là '{e['vi'][0]}'", e["en"])
            else:
                exp = " | ".join(e["vi"])
                level = "warn" if e.get("source") == "paper" or len(e["en"].split()) > 1 else "info"
                add(level, "term", b["id"], f"'{e['en']}' → nên dịch là '{exp}' (không thấy trong bản dịch)", e["en"])
        for code, msg in preservation_issues(en, vi):
            add("warn", code, b["id"], msg)
        for code, msg in style_issues(en, vi):
            add("info", code, b["id"], msg)

    for key, by_variant in usage.items():
        if len(by_variant) > 1:
            e = entries[key]
            parts = [f"'{e['vi'][i]}' ({', '.join(ids[:6])}{'…' if len(ids) > 6 else ''})"
                     for i, ids in sorted(by_variant.items())]
            add("warn", "inconsistent", None,
                f"'{e['en']}' được dịch không thống nhất: " + " vs ".join(parts)
                + f". Chọn một cách dịch (ưu tiên '{e['vi'][0]}') và ghi vào glossary.csv của bài.", e["en"])

    summary = {
        "blocks_to_translate": len(todo),
        "blocks_translated": translated,
        "warnings": sum(1 for i in issues if i["level"] == "warn"),
        "infos": sum(1 for i in issues if i["level"] == "info"),
        "glossary_terms": len(entries),
    }
    return {"summary": summary, "issues": issues}


def print_check(res: dict) -> None:
    s = res["summary"]
    print(f"PaperViet check: {s['blocks_translated']}/{s['blocks_to_translate']} blocks translated, "
          f"{s['warnings']} warning(s), {s['infos']} suggestion(s), {s['glossary_terms']} glossary terms loaded.")
    order = {"warn": 0, "info": 1}
    for it in sorted(res["issues"], key=lambda i: (order[i["level"]], i["code"], i["block"] or "")):
        tag = "WARN" if it["level"] == "warn" else "info"
        where = f"{it['block']}: " if it["block"] else ""
        print(f"  [{tag}] {it['code']:<12} {where}{it['message']}")
    if not res["issues"]:
        print("  No issues found.")


# --------------------------------------------------------------------------- CLI


def print_table(rows: list[dict]) -> None:
    if not rows:
        print("(no glossary terms found)")
        return
    print("| English | Tiếng Việt (ưu tiên) | Khác | Lĩnh vực | Số lần |")
    print("|---|---|---|---|---|")
    for e in rows:
        alt = ", ".join(e["vi"][1:])
        print(f"| {e['en']} | {e['vi'][0]} | {alt} | {e['domain']}{' (paper)' if e.get('source') == 'paper' else ''} "
              f"| {e.get('count', '')} |")


def main(argv: list[str] | None = None) -> int:
    setup_stdio()
    ap = argparse.ArgumentParser(description="PaperViet glossary tool")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("lookup", help="list glossary terms found in a work folder or text file")
    p.add_argument("target")
    p.add_argument("--glossary", action="append", default=[])
    p.add_argument("--all", action="store_true", help="include very common single words")
    p.add_argument("--domains", help="comma list, e.g. ml,stats")
    p.add_argument("--write", action="store_true", help="append found terms to <workdir>/glossary.csv")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("show", help="search the glossary by English or Vietnamese text")
    p.add_argument("query")
    p.add_argument("--glossary", action="append", default=[])
    p.add_argument("--workdir")

    p = sub.add_parser("check", help="check terminology consistency and preserved content")
    p.add_argument("workdir")
    p.add_argument("--glossary", action="append", default=[])
    p.add_argument("--all-terms", action="store_true", help="also check very common single words")
    p.add_argument("--json", action="store_true")
    p.add_argument("--strict", action="store_true", help="exit 1 when there are warnings")

    p = sub.add_parser("merge", help="write the merged glossary to CSV or JSON")
    p.add_argument("--glossary", action="append", default=[])
    p.add_argument("--workdir")
    p.add_argument("--no-builtin", action="store_true")
    p.add_argument("--out", required=True)

    a = ap.parse_args(argv)

    if a.cmd == "lookup":
        domains = set(a.domains.split(",")) if a.domains else None
        rows = lookup(Path(a.target), a.glossary, a.all, domains)
        if a.write:
            if not Path(a.target).is_dir():
                print("error: --write needs a work folder", file=sys.stderr)
                return 2
            path, n = write_paper_glossary(Path(a.target), [r for r in rows if r.get("source") != "paper"])
            print(f"added {n} term(s) to {path} - review it and keep ONE Vietnamese term per row.")
        if a.json:
            print(json.dumps(rows, ensure_ascii=False, indent=1))
        else:
            print_table(rows)
        return 0

    if a.cmd == "show":
        entries = load_glossary(a.glossary, Path(a.workdir) if a.workdir else None)
        q = vi_key(a.query)
        rows = [e for e in entries.values()
                if q in e["en"].lower() or any(q in vi_key(v) for v in e["vi"])]
        rows.sort(key=lambda e: (e["en"].lower() != q, len(e["en"])))
        print_table(rows[:40])
        return 0

    if a.cmd == "check":
        res = check(Path(a.workdir), a.glossary, a.all_terms)
        if a.json:
            print(json.dumps(res, ensure_ascii=False, indent=1))
        else:
            print_check(res)
        return 1 if a.strict and res["summary"]["warnings"] else 0

    if a.cmd == "merge":
        entries = load_glossary(a.glossary, Path(a.workdir) if a.workdir else None, not a.no_builtin)
        out = Path(a.out)
        rows = sorted(entries.values(), key=lambda e: e["en"].lower())
        if out.suffix.lower() == ".json":
            out.write_text(json.dumps([{k: e[k] for k in ("en", "vi", "domain", "note")} for e in rows],
                                      ensure_ascii=False, indent=1), encoding="utf-8")
        else:
            with out.open("w", encoding="utf-8", newline="") as f:
                w = csv.writer(f)
                w.writerow(["en", "vi", "domain", "note"])
                for e in rows:
                    w.writerow([e["en"], "|".join(e["vi"]), e["domain"], e["note"]])
        print(f"wrote {len(rows)} terms to {out}")
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())

---
name: paper-viet
description: Read English academic papers (PDF) in Vietnamese. Translates papers section by section into natural academic Vietnamese with a consistent EN-VI terminology glossary, keeps equations, citations and numbers intact, and builds a side-by-side bilingual HTML reader plus Markdown. Also writes Vietnamese quick-read summaries, explains hard passages and extracts glossaries. Use when the user wants to translate, summarize, explain or read a research paper, article or PDF in Vietnamese, e.g. "dịch bài báo này sang tiếng Việt", "đọc nhanh paper.pdf", "tóm tắt bài báo", "giải thích đoạn này", "thuật ngữ trong bài".
license: MIT
compatibility: Helper scripts need Python 3.9+; PDF extraction needs PyMuPDF or pypdf (pip install pymupdf). Without them the agent can read the PDF natively and continue from a text file.
metadata:
  author: Thảo Gia (github.com/mahiepit)
  version: "1.0.0"
  homepage: https://github.com/mahiepit/PaperViet
---

# PaperViet: đọc bài báo tiếng Anh bằng tiếng Việt

You (the agent) do the translation. The scripts only extract, organise, check and render.
All user-facing text you write (translations, summaries, explanations, final messages) is in
Vietnamese unless the user asks otherwise.

**Paths.** `${CLAUDE_SKILL_DIR}` below means the folder that contains this SKILL.md. If your
agent does not substitute it, replace it with the real path. Use `python3` on macOS/Linux and
`python` (or `py`) on Windows.

```
S="${CLAUDE_SKILL_DIR}/scripts"
python "$S/extract_pdf.py" paper.pdf            # -> paper.paperviet/ (work folder)
python "$S/glossary.py" lookup paper.paperviet --write
python "$S/render.py" paper.paperviet --status
python "$S/glossary.py" check paper.paperviet
python "$S/render.py" paper.paperviet           # -> paper.vi.html + paper.vi.md
```

## 1. Pick the mode

| User says | Mode | Output |
|---|---|---|
| "dịch", "dịch toàn bộ", "bản song ngữ", "translate" | **Full translation** (default) | bilingual HTML + Markdown |
| "đọc nhanh", "tóm tắt", "summary", "bài này nói gì" | **Quick read** | `doc-nhanh.vi.md` + short answer in chat (+ HTML with `--summary-only`) |
| "giải thích đoạn/công thức/hình...", "explain" | **Explain a passage** | answer in chat, optionally appended to `notes.vi.md` |
| "thuật ngữ", "glossary", "từ khóa chuyên ngành" | **Glossary only** | `glossary.csv` + Markdown table |

If the request is ambiguous and the paper is long (> 15 pages), offer quick read first, then
full translation. Respect page ranges the user gives ("chỉ dịch mục 3", "trang 1-5").

## 2. Extract (all modes)

```
python "$S/extract_pdf.py" path/to/paper.pdf [--pages 1-12] [--chunk-words 1200] [--out DIR]
```

- Creates the work folder `paper.paperviet/` next to the PDF: `document.json` (typed blocks:
  title, authors, abstract, heading, paragraph, caption, equation, table, reference, footnote),
  `source.md` (whole paper with block markers), `pages/page-NNN.md`, `chunks/chunk-NN.en.md`
  and an empty `translations/`.
- Running it again on an existing folder does nothing (safe for resuming). `--force`
  re-extracts but may renumber blocks; existing translations are kept but could then misalign,
  so only force when the extraction was wrong.
- Read the printed outline. If structure looks wrong (e.g. no headings, merged columns), skim
  `source.md`; fix obvious issues while translating rather than re-extracting.
- **Missing dependencies** (exit code 3): tell the user to run `pip install pymupdf` (or
  `pip install pypdf`). If they cannot, read the PDF yourself (Claude Code's Read tool reads
  PDFs, use `pages` for long files), write the text to `paper.txt` with a line
  `--- page N ---` before each page, keep headings on their own lines (or `#` headings in a
  `.md` file), then run `extract_pdf.py paper.txt`.
- No text at all = scanned PDF: suggest OCR (`ocrmypdf in.pdf out.pdf`) or read page images.

## 3. Full translation

1. **Read the style guide once** before translating: [references/style-guide.md](references/style-guide.md).
2. **Fix the terminology first.** Run `glossary.py lookup <workdir> --write`. It appends the
   built-in terms found in the paper to `<workdir>/glossary.csv`. Open that file and make it the
   contract for this paper: exactly ONE Vietnamese rendering per row, delete rows that are
   irrelevant, add paper-specific terms (method names stay in English; new concepts get a
   Vietnamese term you choose once). `glossary.py show "<term>"` searches the built-in glossary
   (500+ terms: AI/ML, CS, math, statistics, biology, medicine, economics).
3. **Translate chunk by chunk**, in order. For each `chunks/chunk-NN.en.md`:
   - Read only that chunk (and the glossary). Optional: `glossary.py lookup chunks/chunk-NN.en.md`
     lists the terms it contains.
   - Write `translations/chunk-NN.vi.md`: copy every marker line `<!-- bNN | type ... -->` as is,
     and put the Vietnamese text under it. Blocks tagged `keep` (equations, tables, references,
     authors) can be left empty; to translate a table header, write the table with the same
     rows and cells separated by two spaces and every number unchanged.
   - One chunk per write. After each chunk, `render.py <workdir> --status` shows progress and
     the next chunk. This is how you resume after a context reset or in a new session: run
     `--status` and continue with the first `todo`/`partial` chunk. Never re-translate `done`
     chunks unless asked.
   - Long papers: keep your context small. Do not load the whole `source.md`; work from the
     chunk files. If subagents are available, chunks can be translated in parallel **after**
     `glossary.csv` is final; give each subagent the style guide, the glossary and one chunk.
4. **Check**: `glossary.py check <workdir>`. Fix every `WARN` (missing/changed numbers,
   lost citations, terms that differ from `glossary.csv`, inconsistent variants). `info` lines
   are style suggestions (first-use English in parentheses, "một cách", "được ... bởi", "Nó",
   too many "việc/sự", "chúng ta" for authors' "we").
5. **Render**: `render.py <workdir>` writes `<name>.vi.html` (self-contained, offline,
   side-by-side EN | VI, Vietnamese-only and English-only modes, table of contents, glossary
   panel, dark mode, phone friendly) and `<name>.vi.md`. Use `--md-mode bilingual` for a
   Markdown file with the English under each paragraph, `--html/--md` to choose paths.
6. Reply in Vietnamese: where the files are, how many blocks were translated, any parts you
   could not translate or were unsure about (e.g. garbled tables, equations extracted badly).

### Translation rules (short version)

- Translate meaning, not words; split long sentences; prefer active voice. Natural academic
  Vietnamese: "we propose" → "chúng tôi đề xuất", "we show" → "chúng tôi chỉ ra",
  "to the best of our knowledge" → "theo hiểu biết của chúng tôi".
- First use of a term in body text: "học tăng cường (reinforcement learning)"; afterwards
  Vietnamese only; headings never get the English in parentheses.
- Never translate: equations/LaTeX, variable names, code, URLs, citations (`[12]`,
  `(Smith et al., 2020)`), author names, model/dataset/method names, the reference list.
- Keep every number, unit and comparison exact. Keep the source's decimal point (0.9) unless
  the user asks for Vietnamese style (0,9).
- Keep hedging strength: suggest ≠ show ≠ prove; "is associated with" is not causation;
  "significantly" means "có ý nghĩa thống kê" only when a statistical test is involved.
- "Figure 3 / Table 2 / Section 4 / Eq. (5)" → "Hình 3 / Bảng 2 / Mục 4 / phương trình (5)".
- Avoid machine-translation calques: "một cách + adj", "được ... bởi", sentences starting with
  "Nó", chains of "việc/sự" and "của".
- If extraction garbled a passage, translate what is recoverable and add `[ND: đoạn gốc bị lỗi
  trích xuất]`; never invent content.

## 4. Quick read (đọc nhanh)

Extract, then read the abstract, introduction (last paragraphs), headings, figure/table
captions, results and conclusion from `source.md` (or `pages/`). Write `<workdir>/doc-nhanh.vi.md`
in Vietnamese, 400-800 words, with these sections:

```
## Bài báo nói gì (3 câu)
## Vấn đề và động lực
## Đóng góp chính        (gạch đầu dòng)
## Phương pháp           (trực giác trước, chi tiết sau; nhắc đúng tên phương trình/hình)
## Kết quả               (số liệu chính, giữ nguyên số; bảng nhỏ nếu cần)
## Hạn chế               (tác giả nêu + bạn nhận thấy, ghi rõ cái nào là nhận xét của bạn)
## Ai nên đọc / câu hỏi khi đọc
```

Give the user a shorter version in chat. `render.py <workdir> --summary-only` makes an HTML page
with just the summary and glossary; after a full translation the summary appears at the top of
the bilingual page automatically.

## 5. Explain a passage

Find the passage (page number, section, quoted words, block id) in `source.md` or
`pages/page-NNN.md`. Answer in Vietnamese with: (1) a faithful translation, (2) a plain-language
explanation, (3) what each symbol means for equations, (4) a tiny numeric example when it helps,
(5) how it connects to the rest of the paper. Say clearly when something is your interpretation.
If the user is building a reading file, append the explanation to `<workdir>/notes.vi.md`
(rendered as "Ghi chú & giải thích" at the end of the HTML).

## 6. Glossary only

Run `glossary.py lookup <workdir> --write`, then read the paper for important terms that the
built-in glossary lacks and add them (one Vietnamese term each; note in `note` when a term is
usually kept in English). Show the final table in chat. `glossary.py merge --workdir <workdir>
--out glossary.json` exports a merged file.

User glossaries: `~/.paperviet/glossary.csv` is loaded automatically, `PAPERVIET_GLOSSARY`
can list more files, and every script accepts `--glossary FILE`. Format: CSV `en,vi,domain,note`,
alternatives in `vi` separated by `|` (first = preferred). The paper's `glossary.csv` wins.

## Files in this skill

- `scripts/extract_pdf.py` PDF/TXT/MD → work folder (PyMuPDF or pypdf; heuristics for
  headings, two columns, captions, equations, tables, footnotes, references, hyphenation)
- `scripts/glossary.py` lookup / show / check / merge
- `scripts/render.py` HTML + Markdown, `--status` progress
- `references/style-guide.md` Vietnamese academic style, calques to avoid, hedging, numbers
- `references/glossary.csv` built-in EN→VI glossary
- `assets/viewer.html` HTML template used by `render.py`

<div align="center">

# 📖 PaperViet

**Read English academic papers in natural Vietnamese, right inside the AI agent you already use.**

**Side-by-side bilingual · Consistent terminology · Equations and numbers untouched · No API key**

[Tiếng Việt](README.md) · English

![PaperViet: English | Vietnamese bilingual reader](docs/img/screenshot-bilingual.png)

**[▶ Live demo](https://mahiepit.github.io/PaperViet/examples/sample-paper.vi.html)**

<sub>The paper in the screenshot is a fictional paper written for the demo (see <a href="examples/">examples/</a>).</sub>

</div>

---

PaperViet is an **agent skill** following the open [Agent Skills](https://agentskills.io) standard
(`SKILL.md`). It works with Claude Code, Codex CLI, Gemini CLI, Cursor, GitHub Copilot and other agents
that support the standard. Give it a PDF: the agent splits the paper into sections, translates it into
academic Vietnamese with a consistent glossary, checks its own work, and produces a bilingual HTML page
that also reads well on a phone.

Inspired by [easyread](https://github.com/Edwardxlai/easyread) (English papers in Chinese), PaperViet is
built for Vietnamese readers: a Vietnamese academic style guide, an English–Vietnamese glossary and a
checker that catches typical machine-translation calques.

## ✨ Why PaperViet

| | |
|---|---|
| 🇻🇳 **Academic Vietnamese, not machine-translationese** | A built-in style guide: avoid "một cách", "được ... bởi", piles of "việc/sự"; keep hedging strength (suggest ≠ prove); "we propose" → "chúng tôi đề xuất". |
| 📚 **Consistent terminology** | 500+ built-in EN→VI terms (AI/ML, CS, math, statistics, biology, medicine, economics). Each paper gets its own `glossary.csv`; first use reads "học tăng cường (reinforcement learning)", later uses Vietnamese only. |
| 🔢 **Numbers stay right** | Equations, variables, code, citations `[12]`, names and the reference list are never translated. The checker flags any number or citation that went missing. |
| 📄 **Long papers are fine** | The paper is split into chunks and progress is saved to files, so the agent can resume exactly where it stopped. |
| 🔑 **No API key, no app** | Your agent does the translation. Helper scripts only need Python and a PDF library. |
| 🆓 **Free and open source** | MIT license. |

## 🚀 Features

**Four modes**
- **Full translation**: paragraph-by-paragraph bilingual translation, exported to HTML and Markdown.
- **Quick read ("đọc nhanh")**: a Vietnamese brief with the problem, key contributions, method, results (exact numbers), limitations and questions to ask.
- **Explain a passage**: faithful translation, plain-language explanation, meaning of every symbol in an equation, a tiny numeric example.
- **Glossary only**: an English–Vietnamese term list for the paper.

**Bilingual reader (one offline HTML file)**
- English | Vietnamese columns; Vietnamese-only mode (tap a paragraph to peek at the original) or English-only.
- Table of contents, filterable glossary panel, light/dark theme, font size control, clean printing.
- Phone friendly; tables render as tables; nothing is loaded from the network.

**PDF extraction**
- Detects title, authors, abstract, headings, figure/table captions, equations, tables, footnotes, references.
- Handles two-column layouts, paragraphs that continue across pages, running headers/footers and page numbers, end-of-line hyphenation.

**Translation checks** (`glossary.py check`)
- Terms that differ from `glossary.csv`, or one term translated several ways.
- Missing or altered numbers, citations, inline math, code, URLs.
- Style hints: "một cách", "được ... bởi", sentences starting with "Nó", "chúng ta" for the authors' "we", leftover English.

<p align="center"><img src="docs/img/screenshot-mobile.png" width="300" alt="PaperViet on a phone, Vietnamese-only mode"></p>

## 📥 Install

### Claude Code (recommended: as a plugin)

Inside Claude Code:
```
/plugin marketplace add mahiepit/PaperViet
/plugin install paper-viet@paperviet
```
Or from a terminal:
```bash
claude plugin marketplace add mahiepit/PaperViet
claude plugin install paper-viet@paperviet
```

### Other agents (copy the skill folder)

Clone the repo and copy `skills/paper-viet` into your agent's skills folder:

| Agent | Personal (all projects) | Project |
|---|---|---|
| Claude Code | `~/.claude/skills/` | `.claude/skills/` |
| Codex CLI | `~/.agents/skills/` | `.agents/skills/` |
| Gemini CLI | `~/.gemini/skills/` or `~/.agents/skills/` | `.gemini/skills/` or `.agents/skills/` |
| Cursor | `~/.cursor/skills/` or `~/.agents/skills/` | `.cursor/skills/` or `.agents/skills/` |
| GitHub Copilot | `~/.copilot/skills/` or `~/.agents/skills/` | `.github/skills/` or `.agents/skills/` |

`~/.agents/skills/` is shared by Codex, Gemini CLI, Cursor and Copilot.

macOS / Linux:
```bash
git clone https://github.com/mahiepit/PaperViet.git
mkdir -p ~/.agents/skills && cp -r PaperViet/skills/paper-viet ~/.agents/skills/
```

Windows (PowerShell):
```powershell
git clone https://github.com/mahiepit/PaperViet.git
New-Item -ItemType Directory -Force "$HOME\.agents\skills" | Out-Null
Copy-Item -Recurse PaperViet\skills\paper-viet "$HOME\.agents\skills\"
```

### PDF library (once)

The scripts need **Python 3.9+** and one of:
```bash
pip install pymupdf      # recommended: better structure detection (font sizes, bold, columns)
pip install pypdf        # lighter, pure Python
```
Can't install them? The agent can still work: Claude Code reads PDFs natively, saves the text to a
`.txt` file and continues with the same workflow.

## 💬 Usage

Just ask your agent (in Vietnamese or English), for example:

```text
Dịch bài báo paper.pdf sang tiếng Việt                 (translate paper.pdf into Vietnamese)
Đọc nhanh giúp mình bài attention.pdf                  (quick read in Vietnamese)
Giải thích phương trình (3) ở mục 2.2 trong paper.pdf  (explain equation 3 in section 2.2)
Lập bảng thuật ngữ Anh – Việt cho bài báo này          (build an EN–VI glossary)
Chỉ dịch trang 1 đến 6 của paper.pdf                   (translate pages 1–6 only)
Tiếp tục dịch paper.pdf                                (resume)
```

In Claude Code you can also call it directly: `/paper-viet:paper-viet paper.pdf` (plugin install) or
`/paper-viet paper.pdf` (copied into `~/.claude/skills`).

Output goes next to the PDF, in `paper.paperviet/`:

```
paper.paperviet/
├── paper.vi.html          ← open in a browser: bilingual reader
├── paper.vi.md            ← Markdown (Vietnamese, or bilingual with --md-mode bilingual)
├── doc-nhanh.vi.md        ← quick-read brief (if requested)
├── glossary.csv           ← terms chosen for this paper
├── chunks/  translations/ ← source / translated chunks (= progress, for resuming)
└── document.json  source.md  pages/
```

A complete example lives in [examples/](examples/): the sample paper [sample-paper.pdf](examples/sample-paper.pdf),
its translation [sample-paper.vi.md](examples/sample-paper.vi.md) and the bilingual page
`examples/sample-paper.vi.html` (download and open it in a browser).

## ⚙️ How it works

```
paper.pdf
   │  extract_pdf.py      typed blocks: title, abstract, headings, paragraphs, equations, tables, references
   ▼
paper.paperviet/chunks/chunk-01.en.md …     (~1200 words each, block markers <!-- b12 -->)
   │  glossary.py lookup  pick terms for this paper → glossary.csv
   │  the agent           translates chunk by chunk → translations/chunk-01.vi.md … (following the style guide)
   │  glossary.py check   terminology, numbers, citations, style
   ▼
render.py  →  paper.vi.html (bilingual, offline)  +  paper.vi.md
```

The agent runs these commands itself. To use them by hand:

```bash
S=~/.agents/skills/paper-viet/scripts
python $S/extract_pdf.py paper.pdf                 # creates paper.paperviet/
python $S/glossary.py lookup paper.paperviet --write
python $S/render.py paper.paperviet --status       # progress and next chunk
python $S/glossary.py check paper.paperviet        # check the translation
python $S/render.py paper.paperviet                # write HTML + Markdown
python $S/glossary.py show "learning rate"         # look up a term
```

## 📚 Your own glossary

Create `~/.paperviet/glossary.csv` (UTF-8):

```csv
en,vi,domain,note
learning rate,tốc độ học,ml,
attention head,đầu chú ý,ml,
transformer,Transformer,ml,keep the architecture name
```

It is loaded automatically and overrides the built-in list. Add more files with the
`PAPERVIET_GLOSSARY` environment variable or `--glossary`. Separate alternative translations with `|`
(the first is preferred). The terms fixed for a paper live in `paper.paperviet/glossary.csv`.

The built-in list is [skills/paper-viet/references/glossary.csv](skills/paper-viet/references/glossary.csv).
Pull requests with standard terms for more fields are very welcome.

## ❓ Notes and limitations

- Translation quality depends on the model behind your agent. Check the original before quoting or reusing numbers.
- Scanned (image-only) PDFs need OCR first (e.g. `ocrmypdf`).
- Equations are kept as the text extracted from the PDF; complex ones may lose symbols, so refer to the PDF.
- Figures are not extracted; their captions are translated.
- With `pypdf`, paragraph boundaries are sometimes merged; `pymupdf` gives better results.

## 🧪 Development

```bash
pip install pymupdf pypdf pytest
python -m pytest
python tools/make_sample_pdf.py      # rebuild examples/sample-paper.pdf
```

## 🔗 More projects

- **[ControlPhone](https://github.com/mahiepit/ControlPhone)**: control many Android phones at once from your PC
- **[ChuotVan](https://github.com/mahiepit/ChuotVan)**: turn AI-sounding Vietnamese into natural Vietnamese
- **[DiaChiMoi](https://github.com/mahiepit/DiaChiMoi)**: convert old Vietnamese addresses to the 2025 administrative units
- **[SkillLint](https://github.com/mahiepit/SkillLint)**: lint Agent Skills (SKILL.md) for every coding agent

## ❤️ Support the project

PaperViet is free and will always be free. If it saves you time, a small donation helps keep the project going. Thank you!

<table>
<tr>
<td align="center"><b>PayPal</b><br><img src="docs/img/donate-paypal.svg" width="180" alt="PayPal QR"><br><a href="https://paypal.me/thaogia">paypal.me/thaogia</a></td>
<td align="center"><b>BNB (BEP-20) / ETH (ERC-20)</b><br><img src="docs/img/donate-crypto.svg" width="180" alt="BNB / ETH QR"><br><code>0xd09c2E60cbC8526976C436e316630FA64296E824</code></td>
</tr>
</table>

Please double-check the network (BNB Smart Chain or Ethereum) before sending crypto.

## 📄 License

[MIT](LICENSE) © Thảo Gia. The sample paper in `examples/` is fictional text written for this project and released under the same license.
PaperViet is an independent project and is not affiliated with easyread or with any of the agent vendors mentioned.

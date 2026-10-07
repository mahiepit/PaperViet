import importlib.util
import json

import pytest

import extract_pdf as ex
from conftest import EXAMPLES

SAMPLE_PDF = EXAMPLES / "sample-paper.pdf"


def _has(mod):
    return importlib.util.find_spec(mod) is not None


ENGINES = [
    pytest.param("pymupdf", marks=pytest.mark.skipif(not (_has("pymupdf") or _has("fitz")),
                                                     reason="PyMuPDF not installed")),
    pytest.param("pypdf", marks=pytest.mark.skipif(not _has("pypdf"), reason="pypdf not installed")),
]


@pytest.mark.parametrize("engine", ENGINES)
def test_sample_pdf_structure(tmp_path, engine):
    doc = ex.extract(SAMPLE_PDF, tmp_path / "w", engine=engine, chunk_words=400, quiet=True)
    blocks = doc["blocks"]
    types = [b["type"] for b in blocks]
    by_type = lambda t: [b for b in blocks if b["type"] == t]  # noqa: E731

    assert doc["engine"] == engine and doc["pages"] == 2
    assert doc["title"] == "Sparse Curriculum Sampling for Efficient Fine-Tuning of Small Language Models"
    assert by_type("authors") and "An Tran" in by_type("authors")[0]["text"]
    headings = [b["text"] for b in by_type("heading")]
    assert headings == ["Abstract", "1 Introduction", "2 Method", "3 Experiments",
                        "4 Limitations", "5 Conclusion", "References"]
    assert by_type("abstract")[0]["text"].startswith("Fine-tuning a pretrained language model")
    eqs = by_type("equation")
    assert len(eqs) == 2 and "beta" in eqs[0]["text"] and "alpha" in eqs[1]["text"]
    assert all(b["keep"] for b in eqs)
    assert by_type("caption")[0]["text"].startswith("Table 1:")
    assert "86.1" in by_type("table")[0]["text"] and by_type("table")[0]["keep"]
    refs = by_type("reference")
    assert len(refs) == 4 and refs[0]["text"].startswith("[1] A. Vaswani")
    assert all(b["keep"] for b in refs)
    # running footer and page numbers are removed; the footnote is kept separately
    assert not any("not a real publication" in b["text"] for b in blocks)
    assert by_type("footnote") and "fictional paper" in by_type("footnote")[0]["text"]
    # a paragraph that continues across the page break is joined
    assert any("on a small subset. A small constant eps" in b["text"] for b in blocks)
    assert "paragraph" in types and types[0] == "title"


@pytest.mark.parametrize("engine", ENGINES)
def test_outputs_and_resume(tmp_path, engine):
    wd = tmp_path / "w"
    doc = ex.extract(SAMPLE_PDF, wd, engine=engine, chunk_words=400, quiet=True)
    assert (wd / "pages" / "page-001.md").is_file() and (wd / "pages" / "page-002.md").is_file()
    assert (wd / "source.md").read_text(encoding="utf-8").count("<!-- b") == len(doc["blocks"])
    saved = json.loads((wd / "document.json").read_text(encoding="utf-8"))
    assert saved["format"] == "paperviet/1"
    assert len(saved["chunks"]) >= 3
    covered = [bid for c in saved["chunks"] for bid in c["blocks"]]
    assert covered == [b["id"] for b in saved["blocks"]]  # every block in exactly one chunk, in order
    for c in saved["chunks"]:
        text = (wd / c["file"]).read_text(encoding="utf-8")
        assert all(f"<!-- {bid} |" in text for bid in c["blocks"])
    assert saved["chunks"][-1]["keep_only"]  # the reference list needs no translation

    # resume: a second run must not touch existing translations
    (wd / "translations" / "chunk-01.vi.md").write_text("<!-- b1 -->\nTiêu đề\n", encoding="utf-8")
    again = ex.extract(SAMPLE_PDF, wd, engine=engine, quiet=True)
    assert again["created"] == doc["created"]
    assert (wd / "translations" / "chunk-01.vi.md").is_file()


def test_text_input_hyphenation_headers_and_pages(tmp_path):
    topics = ["reinforcement learning", "computer vision", "speech recognition"]
    pages = []
    for p in (1, 2, 3):
        body = ("Journal of Examples, Vol. 1\n"
                + ("Deep Learning for Things\nA. Author\n\n1 Introduction\n" if p == 1 else "")
                + (f"Page {p} discusses {topics[p - 1]}. It also mentions rein-\nforcement learning and fine-\n"
                   f"tuning of state-of-the-art {topics[p - 1]} models.\n\n{p}\n"))
        pages.append(body)
    src = tmp_path / "paper.txt"
    src.write_text("\f".join(pages), encoding="utf-8")
    doc = ex.extract(src, tmp_path / "w", quiet=True)
    assert doc["engine"] == "text" and doc["pages"] == 3
    texts = [b["text"] for b in doc["blocks"]]
    assert doc["title"] == "Deep Learning for Things"
    assert any("mentions reinforcement learning and fine-tuning of state-of-the-art computer vision" in t
               for t in texts)
    assert not any("Journal of Examples" in t for t in texts)  # repeated running header
    assert not any(t.strip() in ("1", "2", "3") for t in texts)  # page numbers
    assert [b["text"] for b in doc["blocks"] if b["type"] == "heading"] == ["1 Introduction"]


def test_markdown_input_uses_hash_headings(tmp_path):
    src = tmp_path / "paper.md"
    src.write_text("# My Title\n\n## Abstract\nShort abstract here.\n\n## 2.1 Setup\nWe use things.\n",
                   encoding="utf-8")
    doc = ex.extract(src, tmp_path / "w", quiet=True)
    heads = [(b["text"], b["level"]) for b in doc["blocks"] if b["type"] == "heading"]
    assert doc["title"] == "My Title"
    assert heads == [("Abstract", 1), ("2.1 Setup", 2)]
    assert [b["type"] for b in doc["blocks"]][2] == "abstract"


def test_two_column_reading_order():
    L = ex.Line
    lines = [L("Title spanning the page", 1, 100, 50, 500, 70, 16, True, 600, 800)]
    for i in range(8):
        y = 120 + i * 14
        lines.append(L(f"left {i}", 1, 50, y, 290, y + 12, 10, False, 600, 800))
        lines.append(L(f"right {i}", 1, 310, y, 550, y + 12, 10, False, 600, 800))
    order = [l.text for l in ex.order_page_lines(lines)]
    assert order[0] == "Title spanning the page"
    assert order[1:9] == [f"left {i}" for i in range(8)]
    assert order[9:] == [f"right {i}" for i in range(8)]


def test_same_row_fragments_are_merged():
    L = ex.Line
    rows = [L("x = y + 1", 1, 200, 100, 300, 112, 10, False, 600, 800),
            L("(3)", 1, 520, 99, 540, 113, 10.5, False, 600, 800)]
    merged = ex.merge_rows(rows)
    assert len(merged) == 1 and merged[0].text == "x = y + 1  (3)"


@pytest.mark.parametrize("text,expected", [
    ("s_i <- beta * s_i + (1 - beta) * L(f(x_i; w), y_i)  (1)", True),
    ("p(y | x) = softmax(W h + b)", True),
    ("We set the learning rate to 0.001 for all runs.", False),
    ("Let D = {(x_i, y_i)}, i = 1..N, be the training set and f(x; w) a classifier with weights w.", False),
])
def test_is_equation(text, expected):
    assert ex.is_equation(text) is expected


def test_is_table_line():
    assert ex.is_table_line("Uniform  86.1 ± 0.9  90.4 ± 0.5  93.2 ± 0.3  52.0")
    assert ex.is_table_line("Uniform 86.1 ± 0.9 90.4 ± 0.5 93.2 ± 0.3 52.0")
    assert not ex.is_table_line("We report the mean accuracy over 5 seeds in Table 1.")


def test_missing_dependencies_message(monkeypatch, tmp_path, capsys):
    import builtins

    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name in ("pymupdf", "fitz", "pypdf"):
            raise ImportError(name)
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    with pytest.raises(ex.MissingDependency):
        ex.load_engine("auto")
    code = ex.main([str(SAMPLE_PDF), "--out", str(tmp_path / "w")])
    assert code == ex.EXIT_MISSING_DEPS
    err = capsys.readouterr().err
    assert "pip install pymupdf" in err and "paper.txt" in err


def test_page_ranges():
    assert ex.parse_pages("1-3,5", 10) == [1, 2, 3, 5]
    assert ex.parse_pages("8-", 10) == [8, 9, 10]
    assert ex.parse_pages(None, 3) == [1, 2, 3]
    assert ex.parse_pages("0,99", 5) == []

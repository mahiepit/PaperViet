import importlib.util
import json
import re

import pytest

import extract_pdf as ex
import render as rd
from conftest import EXAMPLES


def test_example_renders_fully_translated(example_workdir, tmp_path):
    out = rd.render(example_workdir, tmp_path / "x.html", tmp_path / "x.md", quiet=True)
    page = (tmp_path / "x.html").read_text(encoding="utf-8")
    assert page.startswith("<!doctype html>")
    assert "{{" not in page and "}}" not in page
    assert "Sparse Curriculum Sampling: lấy mẫu theo giáo trình thưa" in page
    assert "3 Thực nghiệm" in page and "3 Experiments" in page
    assert "Chưa dịch" not in page
    assert "Đọc nhanh" in page and "Ghi chú &amp; giải thích" in page
    assert "<th>Phương pháp</th>" in page and "<td>86.1 ± 0.9</td>" in page  # table rendered as table
    assert 'class="cite">[2]</span>' in page
    assert 'data-mode="vi"' in page and 'id="gloss"' in page and "prefers-color-scheme: dark" in page
    p = rd.progress(out["data"]["doc"], out["data"]["tr"])
    assert p["done"] == p["total"] == 21


def test_html_is_self_contained(example_workdir, tmp_path):
    rd.render(example_workdir, tmp_path / "x.html", tmp_path / "x.md", quiet=True)
    page = (tmp_path / "x.html").read_text(encoding="utf-8")
    assert not re.search(r"<script[^>]+src=", page)
    assert not re.search(r"<link[^>]+href=", page)
    assert "@import" not in page and "url(http" not in page
    # the only absolute URLs are plain links to the project page
    urls = set(re.findall(r'https?://[^\s"\'<>)]+', page))
    assert urls <= {"https://github.com/mahiepit/PaperViet"}


def test_markdown_export(example_workdir, tmp_path):
    rd.render(example_workdir, tmp_path / "vi.html", tmp_path / "vi.md", quiet=True)
    md = (tmp_path / "vi.md").read_text(encoding="utf-8")
    assert md.startswith("# Sparse Curriculum Sampling: lấy mẫu")
    assert "## 1 Giới thiệu" in md and "## Đọc nhanh" in md and "## Thuật ngữ" in md
    assert "```text\ns_i <- beta" in md
    assert "- [1] A. Vaswani" in md
    assert "Small language models" not in md  # Vietnamese-only by default

    rd.render(example_workdir, tmp_path / "bi.html", tmp_path / "bi.md", md_mode="bilingual", quiet=True)
    bi = (tmp_path / "bi.md").read_text(encoding="utf-8")
    assert "> Small language models with fewer than one billion parameters" in bi


def test_partial_translation_status_and_escaping(tiny_workdir, tmp_path, capsys):
    doc = json.loads((tiny_workdir / "document.json").read_text(encoding="utf-8"))
    first = doc["chunks"][0]
    todo = [b for b in doc["blocks"] if b["id"] in first["blocks"] and not b["keep"]]
    # translate only part of the first chunk, including a hostile string
    parts = [f"<!-- {todo[0]['id']} | {todo[0]['type']} -->", "Tiêu đề <script>alert(1)</script> [1]", ""]
    (tiny_workdir / "translations" / "chunk-01.vi.md").write_text("\n".join(parts), encoding="utf-8")
    data = rd.load_all(tiny_workdir)
    p = rd.progress(data["doc"], data["tr"])
    assert p["done"] == 1 and p["total"] > 1
    states = {c["id"]: c["state"] for c in p["chunks"]}
    assert states["chunk-01"] == "partial"

    rd.print_status(tiny_workdir, data)
    out = capsys.readouterr().out
    assert "Next: translate chunks/chunk-01.en.md" in out

    rd.render(tiny_workdir, tmp_path / "t.html", tmp_path / "t.md", quiet=True)
    page = (tmp_path / "t.html").read_text(encoding="utf-8")
    assert "<script>alert(1)</script>" not in page
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in page
    assert "Chưa dịch" in page


def test_json_translations_and_duplicates(tiny_workdir):
    doc = json.loads((tiny_workdir / "document.json").read_text(encoding="utf-8"))
    ids = [b["id"] for b in doc["blocks"] if not b["keep"]]
    (tiny_workdir / "translations" / "a.vi.json").write_text(
        json.dumps({"blocks": [{"id": ids[0], "vi": "Một"}, {"id": ids[1], "vi": "Hai"}]}, ensure_ascii=False),
        encoding="utf-8")
    (tiny_workdir / "translations" / "b.vi.json").write_text(json.dumps({ids[1]: "Hai (sửa)"}, ensure_ascii=False),
                                                             encoding="utf-8")
    data = rd.load_all(tiny_workdir)
    assert data["tr"][ids[0]] == "Một"
    assert data["tr"][ids[1]] == "Hai (sửa)"
    assert any("translated in both" in w for w in data["warnings"])


def test_summary_only(example_workdir, tmp_path):
    rd.render(example_workdir, tmp_path / "s.html", tmp_path / "s.md", summary_only=True, quiet=True)
    page = (tmp_path / "s.html").read_text(encoding="utf-8")
    assert "Đọc nhanh" in page and 'class="row' not in page
    assert "Small language models" not in (tmp_path / "s.md").read_text(encoding="utf-8")


def test_inline_markup():
    h = rd.inline("Xem `f(x)` và $a_i^2$, trích dẫn [3, 5], **đậm**, *nghiêng*, a * b * c, <b>")
    assert "<code>f(x)</code>" in h
    assert '<span class="math">$a_i^2$</span>' in h
    assert '<span class="cite">[3, 5]</span>' in h
    assert "<strong>đậm</strong>" in h and "<em>nghiêng</em>" in h
    assert "a * b * c" in h and "&lt;b&gt;" in h


def test_mini_markdown():
    h = rd.mini_markdown("## Kết quả\n\n- một\n- hai\n\n| a | b |\n|---|---|\n| 1 | 2 |\n\n> trích\n\nĐoạn văn.")
    assert "<h3>Kết quả</h3>" in h and "<ul><li>một</li><li>hai</li></ul>" in h
    assert "<th>a</th>" in h and "<td>2</td>" in h and "<blockquote>" in h and "<p>Đoạn văn.</p>" in h


def test_cli_main(example_workdir, capsys):
    assert rd.main([str(example_workdir), "--status", "--json"]) == 0
    st = json.loads(capsys.readouterr().out)
    assert st["done"] == st["total"]
    assert rd.main([str(example_workdir)]) == 0
    assert (example_workdir / "sample-paper.vi.html").is_file()
    assert (example_workdir / "sample-paper.vi.md").is_file()


@pytest.mark.skipif(not (importlib.util.find_spec("pymupdf") or importlib.util.find_spec("fitz")),
                    reason="PyMuPDF not installed")
def test_committed_example_matches_extractor(tmp_path):
    """examples/sample-paper.paperviet must stay in sync with extract_pdf.py (block ids!)."""
    fresh = ex.extract(EXAMPLES / "sample-paper.pdf", tmp_path / "w", engine="pymupdf", chunk_words=400, quiet=True)
    saved = json.loads((EXAMPLES / "sample-paper.paperviet" / "document.json").read_text(encoding="utf-8"))
    strip = lambda d: [(b["id"], b["type"], b["text"]) for b in d["blocks"]]  # noqa: E731
    assert strip(fresh) == strip(saved)

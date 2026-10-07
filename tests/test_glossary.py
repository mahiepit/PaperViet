import csv
import json

import glossary as gl
from conftest import SKILL
from pv_common import vi_key

ALLOWED_DOMAINS = {"general", "ml", "cs", "math", "stats", "bio", "med", "econ"}


def test_builtin_glossary_is_well_formed():
    with (SKILL / "references" / "glossary.csv").open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) >= 300
    keys = [r["en"].strip().lower() for r in rows]
    assert len(keys) == len(set(keys)), "duplicate English terms"
    for r in rows:
        assert r["en"].strip() and r["vi"].strip(), r
        assert r["domain"] in ALLOWED_DOMAINS, r
        assert None not in r, f"extra column in {r}"
        assert all(v.strip() for v in r["vi"].split("|")), r
    entries = gl.load_glossary()
    assert entries["reinforcement learning"]["vi"][0] == "học tăng cường"


def test_matcher_longest_match_plurals_and_acronyms():
    m = gl.Matcher(gl.load_glossary(builtin=True))
    found = m.find("Deep reinforcement learning with neural networks; DNA and dna; Batch Normalization layers.")
    assert found["reinforcement learning"] == 1
    assert "deep learning" not in found  # 'deep reinforcement learning' is not 'deep learning'
    assert found["neural network"] == 1  # plural
    assert found["dna"] == 1  # acronyms are case-sensitive: 'dna' does not count
    assert found["batch normalization"] == 1 and "normalization" not in found
    assert gl.Matcher(gl.load_glossary()).find("fine tuning and finetuning and fine-tuning")["fine-tuning"] == 3


def test_vietnamese_normalisation():
    assert vi_key("Chuẩn Hoá") == vi_key("chuẩn hóa")
    assert vi_key("thuỷ") == vi_key("thủy")
    e = {"en": "normalization", "vi": ["chuẩn hóa"]}
    assert gl.vi_variant_hits(e, "Bước chuẩn hoá dữ liệu") == [0]
    assert gl.vi_variant_hits(e, "chuẩn hóaxyz") == []


def test_example_translation_is_clean(example_workdir):
    res = gl.check(example_workdir)
    assert res["summary"]["blocks_translated"] == res["summary"]["blocks_to_translate"] == 21
    assert res["summary"]["warnings"] == 0, res["issues"]


def _write(wd, mapping):
    lines = []
    for bid, text in mapping.items():
        lines += [f"<!-- {bid} -->", text, ""]
    (wd / "translations" / "chunk-01.vi.md").write_text("\n".join(lines), encoding="utf-8")


def _ids(wd):
    doc = json.loads((wd / "document.json").read_text(encoding="utf-8"))
    return {b["text"].split()[0] + ("-" + b["type"]): b["id"] for b in doc["blocks"]}, doc


def test_check_finds_problems(tiny_workdir):
    doc = json.loads((tiny_workdir / "document.json").read_text(encoding="utf-8"))
    by_start = {b["text"][:12]: b["id"] for b in doc["blocks"]}
    abstract = by_start["We study lea"]
    intro = by_start["Choosing the"]
    results = by_start["The schedule"]
    _write(tiny_workdir, {
        # learning rate -> 'tốc độ học'; numbers 81.2/83.5 and citation [1] are lost
        abstract: "Chúng ta nghiên cứu khởi động tốc độ học (learning rate warmup) cho mạng nơ-ron tích chập nhỏ. "
                  "Nó cải thiện độ chính xác một cách rõ rệt trên một tập dữ liệu công khai.",
        # learning rate translated differently, random seeds kept fine
        intro: "Chọn tỉ lệ học rất khó. Trong bài báo này, chúng tôi đề xuất một lịch đơn giản và đánh giá "
               "với năm seed ngẫu nhiên.",
        # inline code and URL changed; author-year citation kept
        results: "Lịch này giảm 12% thời gian huấn luyện (Smith et al., 2020) mà vẫn giữ độ chính xác ổn định. "
                 "Xem train.py để biết chi tiết.",
    })
    res = gl.check(tiny_workdir)
    codes = {(i["code"], i["block"]) for i in res["issues"]}
    msgs = " ".join(i["message"] for i in res["issues"])
    assert ("number", abstract) in codes and "81.2" in msgs and "83.5" in msgs
    assert ("citation", abstract) in codes
    assert ("term", intro) in codes and "learning rate" in msgs
    assert ("verbatim", results) in codes and "`train.py`" in msgs and "https://example.org/warmup" in msgs
    assert not any(c == "citation" and b == results for c, b in codes)  # (Smith et al., 2020) is kept
    assert ("calque", abstract) in codes and ("pronoun", abstract) in codes and ("we", abstract) in codes
    assert res["summary"]["warnings"] >= 4


def test_inconsistent_variants_are_reported(tiny_workdir):
    doc = json.loads((tiny_workdir / "document.json").read_text(encoding="utf-8"))
    by_start = {b["text"][:12]: b["id"] for b in doc["blocks"]}
    _write(tiny_workdir, {
        by_start["We study lea"]: "Chúng tôi nghiên cứu tốc độ học cho mạng nơ-ron tích chập nhỏ; độ chính xác tăng "
                                  "từ 81.2% lên 83.5% trên một bộ dữ liệu công khai [1].",
        by_start["The schedule"]: "Lịch này giảm 12% thời gian huấn luyện (Smith et al., 2020) mà vẫn giữ độ chính "
                                  "xác ổn định trên tập dữ liệu. Xem `train.py` và https://example.org/warmup.",
    })
    # 'dataset' has two built-in variants: 'tập dữ liệu' | 'bộ dữ liệu'
    res = gl.check(tiny_workdir)
    inc = [i for i in res["issues"] if i["code"] == "inconsistent"]
    assert inc and inc[0]["term"] == "dataset"
    assert "'tập dữ liệu'" in inc[0]["message"] and "'bộ dữ liệu'" in inc[0]["message"]


def test_user_glossary_override_and_env(tmp_path, monkeypatch):
    mine = tmp_path / "mine.csv"
    mine.write_text("en,vi,domain,note\nlearning rate,hệ số học,ml,\nwarmup,khởi động,ml,\n", encoding="utf-8")
    entries = gl.load_glossary([str(mine)])
    assert entries["learning rate"]["vi"] == ["hệ số học"] and "warmup" in entries
    monkeypatch.setenv("PAPERVIET_GLOSSARY", str(mine))
    assert gl.load_glossary()["warmup"]["vi"] == ["khởi động"]


def test_lookup_write_and_show(tiny_workdir, capsys):
    found = gl.lookup(tiny_workdir)
    names = {e["en"] for e in found}
    assert {"learning rate", "convolutional neural network", "dataset"} <= names
    path, n = gl.write_paper_glossary(tiny_workdir, found)
    assert n == len(found) and path.is_file()
    _, n2 = gl.write_paper_glossary(tiny_workdir, gl.lookup(tiny_workdir))
    assert n2 == 0  # nothing new the second time
    rows = gl.read_csv(path)
    assert all(len(r["vi"]) == 1 for r in rows)  # one Vietnamese term per row in the paper glossary

    assert gl.main(["show", "tăng cường"]) == 0
    out = capsys.readouterr().out
    assert "reinforcement learning" in out and "data augmentation" in out


def test_merge_cli(tmp_path, tiny_workdir):
    out = tmp_path / "merged.json"
    assert gl.main(["merge", "--workdir", str(tiny_workdir), "--out", str(out)]) == 0
    data = json.loads(out.read_text(encoding="utf-8"))
    assert len(data) >= 300 and {"en", "vi", "domain", "note"} <= set(data[0])


def test_strict_exit_code(tiny_workdir):
    doc = json.loads((tiny_workdir / "document.json").read_text(encoding="utf-8"))
    bid = next(b["id"] for b in doc["blocks"] if b["text"].startswith("We study"))
    _write(tiny_workdir, {bid: "Bản dịch thiếu số liệu."})
    assert gl.main(["check", str(tiny_workdir)]) == 0
    assert gl.main(["check", str(tiny_workdir), "--strict"]) == 1

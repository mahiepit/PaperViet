#!/usr/bin/env python3
"""Build examples/sample-paper.pdf: a short, FICTIONAL paper written for the PaperViet demo.

Standard library only (hand-written PDF objects, built-in Helvetica/Courier fonts),
so the sample can be regenerated anywhere:

    python tools/make_sample_pdf.py [output.pdf]

All text below is original and released with this repository under the MIT license.
The numbers in the paper are invented. The four references are real, well-known works.
"""
from __future__ import annotations

import sys
from pathlib import Path

PAGE_W, PAGE_H = 612, 792  # US Letter, points
MARGIN_X, MARGIN_TOP, MARGIN_BOTTOM = 72, 72, 80
TEXT_W = PAGE_W - 2 * MARGIN_X

# Helvetica advance widths (1/1000 em) for ASCII 32..126, from the standard AFM metrics.
_HELV = [
    278, 278, 355, 556, 556, 889, 667, 191, 333, 333, 389, 584, 278, 333, 278, 278,
    556, 556, 556, 556, 556, 556, 556, 556, 556, 556, 278, 278, 584, 584, 584, 556,
    1015, 667, 667, 722, 722, 667, 611, 778, 722, 278, 500, 667, 556, 833, 722, 778,
    667, 778, 722, 667, 611, 722, 667, 944, 667, 667, 611, 278, 278, 278, 469, 556,
    333, 556, 556, 500, 556, 556, 278, 556, 556, 222, 222, 500, 222, 833, 556, 556,
    556, 556, 333, 500, 278, 556, 500, 722, 500, 500, 500, 334, 260, 334, 584,
]


def text_width(s: str, size: float, font: str = "F1") -> float:
    if font == "F4":  # Courier is monospaced
        return len(s) * 600 * size / 1000
    w = sum(_HELV[ord(c) - 32] if 32 <= ord(c) <= 126 else 556 for c in s)
    if font == "F2":
        w *= 1.06  # bold is slightly wider; close enough for line breaking
    return w * size / 1000


def wrap(text: str, size: float, font: str = "F1", width: float = TEXT_W) -> list[str]:
    lines, cur = [], ""
    for word in text.split():
        trial = f"{cur} {word}".strip()
        if cur and text_width(trial, size, font) > width:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines


def pdf_str(s: str) -> bytes:
    raw = s.encode("cp1252")
    return b"(" + raw.replace(b"\\", b"\\\\").replace(b"(", b"\\(").replace(b")", b"\\)") + b")"


# ---------------------------------------------------------------- paper content
TITLE = "Sparse Curriculum Sampling for Efficient Fine-Tuning of Small Language Models"
AUTHORS = ["An Tran and Laura Hayes", "Demo Institute of Computing (fictional affiliation)"]
FOOTNOTE = ("* This is a fictional paper written for the PaperViet demo. "
            "The method and all numbers are invented; only the references are real.")

ABSTRACT = (
    "Fine-tuning a pretrained language model on a new task usually requires many passes over "
    "the training set, even though a large fraction of the examples are already handled well "
    "after the first epoch. We propose Sparse Curriculum Sampling (SCS), a simple data "
    "selection method that estimates the difficulty of each example from its recent loss and "
    "samples hard examples more often while still revisiting easy ones. SCS adds no trainable "
    "parameters and can be implemented in a few lines of code. On three text classification "
    "benchmarks, SCS reaches the accuracy of standard fine-tuning while using 38% fewer "
    "gradient updates, and it reduces the variance across random seeds. We also discuss when "
    "the method fails and why its gains may not transfer to generation tasks."
)

BODY = [
    ("h", "1 Introduction"),
    ("p", "Small language models with fewer than one billion parameters remain attractive for "
          "laboratories and companies with limited computing budgets. However, fine-tuning such a "
          "model still involves a trade-off between cost and accuracy: training for more epochs "
          "tends to improve the final score, but most of the additional computation is spent on "
          "examples that the model has already learned."),
    ("p", "Curriculum learning [2] addresses a related problem by presenting examples in a "
          "meaningful order, usually from easy to hard. In practice, a fixed curriculum requires a "
          "difficulty measure defined before training, which is often unavailable for new "
          "datasets. In this paper, we take a different view: instead of ordering the data once, "
          "we let the model's own training signal decide how often each example should be seen."),
    ("p", "Our contributions are threefold. First, we introduce SCS, a sampling rule based on an "
          "exponential moving average of the per-example loss. Second, we show empirically that "
          "SCS reduces the number of gradient updates without hurting accuracy. Third, we analyze "
          "the failure cases of the method, which, to the best of our knowledge, have not been "
          "reported for similar approaches."),
    ("h", "2 Method"),
    ("p", "Let D = {(x_i, y_i)}, i = 1..N, be the training set and f(x; w) a classifier with "
          "weights w. At step t, we keep a difficulty score s_i for every example, updated "
          "whenever the example is visited:"),
    ("eq", "s_i <- beta * s_i + (1 - beta) * L(f(x_i; w), y_i)", "(1)"),
    ("p", "where L is the cross-entropy loss and beta is a smoothing factor set to 0.9 in all "
          "experiments. Examples are then drawn with probability"),
    ("eq", "p_i = (s_i + eps)^alpha / sum_j (s_j + eps)^alpha", "(2)"),
    ("p", "The exponent alpha controls how strongly the sampler focuses on hard examples: "
          "alpha = 0 recovers uniform sampling, whereas large values concentrate the probability "
          "mass on a small subset. A small constant eps guarantees that every example keeps a "
          "non-zero probability of being selected, so that easy examples are revisited and the "
          "model does not forget them. We optimize the weights with Adam [4] and apply dropout [3] "
          "with rate 0.1, as in standard fine-tuning of Transformer encoders [1]."),
    ("h", "3 Experiments"),
    ("p", "We fine-tune a 110M-parameter encoder on three public text classification datasets, "
          "denoted A, B and C, with 12k, 45k and 120k training examples. Each configuration is "
          "repeated with five random seeds, and we report the mean accuracy on the test set "
          "together with the standard deviation. The baseline uses uniform sampling with the same "
          "learning rate of 2e-5 and a batch size of 32."),
    ("cap", "Table 1: Test accuracy (%) and number of gradient updates (thousands) on the three "
            "datasets. Values are mean ± standard deviation over five seeds."),
    ("table", [
        ["Method", "Data A", "Data B", "Data C", "Updates (k)"],
        ["Uniform", "86.1 ± 0.9", "90.4 ± 0.5", "93.2 ± 0.3", "52.0"],
        ["SCS (alpha = 1)", "86.3 ± 0.6", "90.6 ± 0.4", "93.1 ± 0.2", "32.2"],
        ["SCS (alpha = 2)", "85.2 ± 1.1", "89.9 ± 0.7", "92.8 ± 0.4", "30.5"],
    ]),
    ("p", "As shown in Table 1, SCS with alpha = 1 matches or slightly exceeds the baseline on two "
          "of the three datasets and stays within 0.1 points on the third, while requiring 38% "
          "fewer updates (32.2k versus 52.0k). The lower standard deviation suggests that focusing "
          "on informative examples also makes training more stable. With alpha = 2, however, "
          "accuracy drops on every dataset, which indicates that an overly aggressive sampler "
          "ignores easy examples for too long."),
    ("h", "4 Limitations"),
    ("p", "Our study has several limitations. All experiments use classification tasks and a "
          "single model size, so it is unclear whether the gains hold for text generation or for "
          "models with billions of parameters. In addition, noisy labels may receive persistently "
          "high losses; in such cases SCS could repeatedly sample mislabeled examples and amplify "
          "the noise."),
    ("h", "5 Conclusion"),
    ("p", "We presented Sparse Curriculum Sampling, a lightweight method that reuses the training "
          "loss to decide which examples deserve more attention. The method reduces the cost of "
          "fine-tuning in our setting and is easy to combine with existing training pipelines. "
          "Future work will study adaptive values of alpha and robustness to label noise."),
    ("h", "References"),
    ("ref", "[1] A. Vaswani, N. Shazeer, N. Parmar, J. Uszkoreit, L. Jones, A. N. Gomez, L. Kaiser, "
            "and I. Polosukhin. Attention is all you need. In Advances in Neural Information "
            "Processing Systems, 2017."),
    ("ref", "[2] Y. Bengio, J. Louradour, R. Collobert, and J. Weston. Curriculum learning. In "
            "Proceedings of the 26th International Conference on Machine Learning, 2009."),
    ("ref", "[3] N. Srivastava, G. Hinton, A. Krizhevsky, I. Sutskever, and R. Salakhutdinov. "
            "Dropout: A simple way to prevent neural networks from overfitting. Journal of Machine "
            "Learning Research, 15:1929-1958, 2014."),
    ("ref", "[4] D. P. Kingma and J. Ba. Adam: A method for stochastic optimization. In "
            "International Conference on Learning Representations, 2015."),
]


# ---------------------------------------------------------------- layout engine
class Layout:
    def __init__(self) -> None:
        self.pages: list[list[bytes]] = []
        self.new_page()

    def new_page(self) -> None:
        self.pages.append([])
        self.y = PAGE_H - MARGIN_TOP

    def need(self, h: float) -> None:
        if self.y - h < MARGIN_BOTTOM:
            self.new_page()

    def text(self, x: float, y: float, s: str, font: str = "F1", size: float = 10.5) -> None:
        self.pages[-1].append(
            b"BT /" + font.encode() + b" %.1f Tf %.2f %.2f Td " % (size, x, y) + pdf_str(s) + b" Tj ET")

    def rule(self, x0: float, x1: float, y: float) -> None:
        self.pages[-1].append(b"%.2f %.2f m %.2f %.2f l 0.6 w S" % (x0, y, x1, y))

    def para(self, s: str, size: float = 10.5, font: str = "F1", lead: float = 13.6,
             gap: float = 7, indent: float = 0) -> None:
        for line in wrap(s, size, font, TEXT_W - indent):
            self.need(lead)
            self.y -= lead
            self.text(MARGIN_X + indent, self.y, line, font, size)
        self.y -= gap

    def centered(self, s: str, size: float, font: str, lead: float) -> None:
        for line in wrap(s, size, font, TEXT_W - 40):
            self.need(lead)
            self.y -= lead
            self.text((PAGE_W - text_width(line, size, font)) / 2, self.y, line, font, size)


def build() -> bytes:
    lay = Layout()
    lay.centered(TITLE, 17, "F2", 21)
    lay.y -= 8
    for a in AUTHORS:
        lay.centered(a, 10.5, "F1", 13.5)
    lay.y -= 14
    lay.centered("Abstract", 11.5, "F2", 14)
    lay.y -= 2
    for line in wrap(ABSTRACT, 10, "F1", TEXT_W - 50):
        lay.y -= 12.8
        lay.text(MARGIN_X + 25, lay.y, line, "F1", 10)
    lay.y -= 10

    for kind, *rest in BODY:
        if kind == "h":
            lay.need(40)
            lay.y -= 8
            lay.para(rest[0], size=12, font="F2", lead=15, gap=3)
        elif kind == "p":
            lay.para(rest[0])
        elif kind == "eq":
            lay.need(24)
            lay.y -= 18
            expr, num = rest
            lay.text((PAGE_W - text_width(expr, 10, "F4")) / 2, lay.y, expr, "F4", 10)
            lay.text(PAGE_W - MARGIN_X - text_width(num, 10.5), lay.y, num, "F1", 10.5)
            lay.y -= 12
        elif kind == "cap":
            lay.need(100)
            lay.y -= 4
            lay.para(rest[0], size=9.5, font="F3", lead=12, gap=4, indent=0)
        elif kind == "table":
            cols = [MARGIN_X + 20, MARGIN_X + 140, MARGIN_X + 230, MARGIN_X + 320, MARGIN_X + 410]
            lay.rule(MARGIN_X + 10, PAGE_W - MARGIN_X - 10, lay.y)
            for r, row in enumerate(rest[0]):
                lay.y -= 14
                for x, cell in zip(cols, row):
                    lay.text(x, lay.y, cell, "F2" if r == 0 else "F1", 9.5)
                if r == 0:
                    lay.rule(MARGIN_X + 10, PAGE_W - MARGIN_X - 10, lay.y - 4)
            lay.y -= 6
            lay.rule(MARGIN_X + 10, PAGE_W - MARGIN_X - 10, lay.y)
            lay.y -= 12
        elif kind == "ref":
            lay.para(rest[0], size=9.5, lead=12, gap=3)

    # Footnote on page 1, running footer + page number on every page.
    total = len(lay.pages)
    for i, ops in enumerate(lay.pages, start=1):
        if i == 1:
            lay.pages[0].append(b"%.2f %.2f m %.2f %.2f l 0.4 w S" % (MARGIN_X, 70, MARGIN_X + 150, 70))
            for j, line in enumerate(wrap(FOOTNOTE, 8, "F3", TEXT_W)):
                ops.append(b"BT /F3 8 Tf %.2f %.2f Td " % (MARGIN_X, 60 - j * 10) + pdf_str(line) + b" Tj ET")
        ops.append(b"BT /F1 8 Tf %.2f %.2f Td " % (MARGIN_X, 30)
                   + pdf_str("PaperViet demo paper - not a real publication") + b" Tj ET")
        num = f"{i}"
        ops.append(b"BT /F1 9 Tf %.2f %.2f Td " % (PAGE_W - MARGIN_X - 5, 30) + pdf_str(num) + b" Tj ET")
    assert total >= 2
    return write_pdf(lay.pages)


def write_pdf(pages: list[list[bytes]]) -> bytes:
    objs: list[bytes] = []

    def add(b: bytes) -> int:
        objs.append(b)
        return len(objs)

    catalog = add(b"")  # placeholder, filled later
    pages_id = add(b"")
    fonts = {
        "F1": add(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>"),
        "F2": add(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>"),
        "F3": add(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Oblique /Encoding /WinAnsiEncoding >>"),
        "F4": add(b"<< /Type /Font /Subtype /Type1 /BaseFont /Courier /Encoding /WinAnsiEncoding >>"),
    }
    font_dict = b"<< " + b" ".join(b"/%s %d 0 R" % (k.encode(), v) for k, v in fonts.items()) + b" >>"
    kids = []
    for ops in pages:
        stream = b"\n".join(ops)
        content = add(b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream")
        kids.append(add(
            b"<< /Type /Page /Parent %d 0 R /MediaBox [0 0 %d %d] /Resources << /Font %s >> /Contents %d 0 R >>"
            % (pages_id, PAGE_W, PAGE_H, font_dict, content)))
    objs[catalog - 1] = b"<< /Type /Catalog /Pages %d 0 R >>" % pages_id
    objs[pages_id - 1] = (b"<< /Type /Pages /Kids [" + b" ".join(b"%d 0 R" % k for k in kids)
                          + b"] /Count %d >>" % len(kids))
    info = add(b"<< /Title " + pdf_str(TITLE) + b" /Producer (PaperViet tools/make_sample_pdf.py) >>")

    out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = []
    for i, body in enumerate(objs, start=1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % i + body + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1)
    for off in offsets:
        out += b"%010d 00000 n \n" % off
    out += b"trailer\n<< /Size %d /Root %d 0 R /Info %d 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (
        len(objs) + 1, catalog, info, xref)
    return bytes(out)


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else root / "examples" / "sample-paper.pdf"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(build())
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "skills" / "paper-viet"
SCRIPTS = SKILL / "scripts"
EXAMPLES = ROOT / "examples"
sys.path.insert(0, str(SCRIPTS))

TINY_PAPER = """A Tiny Study of Learning Rate Warmup
Jane Doe and Minh Le
Example University

Abstract
We study learning rate warmup for small convolutional neural networks. Warmup improves the
test accuracy from 81.2% to 83.5% on a public dataset [1].

1 Introduction
Choosing the learning rate is hard. In this paper, we propose a simple schedule and evaluate it
with five random seeds.

2 Results
The schedule reduces training time by 12% (Smith et al., 2020) while keeping the accuracy
stable on the dataset. See `train.py` for details and https://example.org/warmup for the data.

References
[1] J. Doe. A public dataset. 2020.
"""


@pytest.fixture
def tiny_workdir(tmp_path):
    """A work folder built from a small text paper (no PDF library needed)."""
    import extract_pdf

    src = tmp_path / "tiny.txt"
    src.write_text(TINY_PAPER, encoding="utf-8")
    wd = tmp_path / "tiny.paperviet"
    extract_pdf.extract(src, wd, chunk_words=60, quiet=True)
    return wd


@pytest.fixture
def example_workdir(tmp_path):
    """A copy of the committed, fully translated demo work folder."""
    dst = tmp_path / "sample-paper.paperviet"
    shutil.copytree(EXAMPLES / "sample-paper.paperviet", dst)
    return dst


def block_ids(doc, btype):
    return [b["id"] for b in doc["blocks"] if b["type"] == btype]

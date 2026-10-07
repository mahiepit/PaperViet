<!-- paperviet chunk-01 | 8 blocks | ~328 words to translate | Abstract -->
<!-- Translate every block below into Vietnamese and save as translations/chunk-01.vi.md.
     Keep every block-marker comment line (the one holding the block id, e.g. b12) unchanged and
     in order; replace only the English text under it.
     Blocks tagged "keep" (equations, tables, references, authors) may be omitted or copied as-is.
     Never translate math, code, variable names, citations like [3], URLs, or names. -->

<!-- b1 | title | p1 -->
Sparse Curriculum Sampling for Efficient Fine-Tuning of Small Language Models

<!-- b2 | authors | keep | p1 -->
An Tran and Laura Hayes
Demo Institute of Computing (fictional affiliation)

<!-- b3 | heading 1 | p1 -->
Abstract

<!-- b4 | abstract | p1 -->
Fine-tuning a pretrained language model on a new task usually requires many passes over the training set, even though a large fraction of the examples are already handled well after the first epoch. We propose Sparse Curriculum Sampling (SCS), a simple data selection method that estimates the difficulty of each example from its recent loss and samples hard examples more often while still revisiting easy ones. SCS adds no trainable parameters and can be implemented in a few lines of code. On three text classification benchmarks, SCS reaches the accuracy of standard fine-tuning while using 38% fewer gradient updates, and it reduces the variance across random seeds. We also discuss when the method fails and why its gains may not transfer to generation tasks.

<!-- b5 | heading 1 | p1 -->
1 Introduction

<!-- b6 | paragraph | p1 -->
Small language models with fewer than one billion parameters remain attractive for laboratories and companies with limited computing budgets. However, fine-tuning such a model still involves a trade-off between cost and accuracy: training for more epochs tends to improve the final score, but most of the additional computation is spent on examples that the model has already learned.

<!-- b7 | paragraph | p1 -->
Curriculum learning [2] addresses a related problem by presenting examples in a meaningful order, usually from easy to hard. In practice, a fixed curriculum requires a difficulty measure defined before training, which is often unavailable for new datasets. In this paper, we take a different view: instead of ordering the data once, we let the model's own training signal decide how often each example should be seen.

<!-- b8 | paragraph | p1 -->
Our contributions are threefold. First, we introduce SCS, a sampling rule based on an exponential moving average of the per-example loss. Second, we show empirically that SCS reduces the number of gradient updates without hurting accuracy. Third, we analyze the failure cases of the method, which, to the best of our knowledge, have not been reported for similar approaches.

<!-- paperviet chunk-02 | 12 blocks | ~337 words to translate | 2 Method -->
<!-- Translate every block below into Vietnamese and save as translations/chunk-02.vi.md.
     Keep every block-marker comment line (the one holding the block id, e.g. b12) unchanged and
     in order; replace only the English text under it.
     Blocks tagged "keep" (equations, tables, references, authors) may be omitted or copied as-is.
     Never translate math, code, variable names, citations like [3], URLs, or names. -->

<!-- b9 | heading 1 | p1 -->
2 Method

<!-- b10 | paragraph | p1 -->
Let D = {(x_i, y_i)}, i = 1..N, be the training set and f(x; w) a classifier with weights w. At step t, we keep a difficulty score s_i for every example, updated whenever the example is visited:

<!-- b11 | equation | keep | p1 -->
s_i <- beta * s_i + (1 - beta) * L(f(x_i; w), y_i)  (1)

<!-- b12 | paragraph | p1 -->
where L is the cross-entropy loss and beta is a smoothing factor set to 0.9 in all experiments. Examples are then drawn with probability

<!-- b13 | equation | keep | p1 -->
p_i = (s_i + eps)^alpha / sum_j (s_j + eps)^alpha  (2)

<!-- b14 | paragraph | p1 -->
The exponent alpha controls how strongly the sampler focuses on hard examples: alpha = 0 recovers uniform sampling, whereas large values concentrate the probability mass on a small subset. A small constant eps guarantees that every example keeps a non-zero probability of being selected, so that easy examples are revisited and the model does not forget them. We optimize the weights with Adam [4] and apply dropout [3] with rate 0.1, as in standard fine-tuning of Transformer encoders [1].

<!-- b15 | footnote | p1 -->
* This is a fictional paper written for the PaperViet demo. The method and all numbers are invented; only the references are real.

<!-- b16 | heading 1 | p2 -->
3 Experiments

<!-- b17 | paragraph | p2 -->
We fine-tune a 110M-parameter encoder on three public text classification datasets, denoted A, B and C, with 12k, 45k and 120k training examples. Each configuration is repeated with five random seeds, and we report the mean accuracy on the test set together with the standard deviation. The baseline uses uniform sampling with the same learning rate of 2e-5 and a batch size of 32.

<!-- b18 | caption | p2 -->
Table 1: Test accuracy (%) and number of gradient updates (thousands) on the three datasets. Values are mean ± standard deviation over five seeds.

<!-- b19 | table | keep | p2 -->
Method  Data A  Data B  Data C  Updates (k)
Uniform  86.1 ± 0.9  90.4 ± 0.5  93.2 ± 0.3  52.0
SCS (alpha = 1)  86.3 ± 0.6  90.6 ± 0.4  93.1 ± 0.2  32.2
SCS (alpha = 2)  85.2 ± 1.1  89.9 ± 0.7  92.8 ± 0.4  30.5

<!-- b20 | paragraph | p2 -->
As shown in Table 1, SCS with alpha = 1 matches or slightly exceeds the baseline on two of the three datasets and stays within 0.1 points on the third, while requiring 38% fewer updates (32.2k versus 52.0k). The lower standard deviation suggests that focusing on informative examples also makes training more stable. With alpha = 2, however, accuracy drops on every dataset, which indicates that an overly aggressive sampler ignores easy examples for too long.

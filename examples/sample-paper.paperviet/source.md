<!-- paperviet source: sample-paper.pdf | 2 pages | engine pymupdf -->

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

<!-- b21 | heading 1 | p2 -->
4 Limitations

<!-- b22 | paragraph | p2 -->
Our study has several limitations. All experiments use classification tasks and a single model size, so it is unclear whether the gains hold for text generation or for models with billions of parameters. In addition, noisy labels may receive persistently high losses; in such cases SCS could repeatedly sample mislabeled examples and amplify the noise.

<!-- b23 | heading 1 | p2 -->
5 Conclusion

<!-- b24 | paragraph | p2 -->
We presented Sparse Curriculum Sampling, a lightweight method that reuses the training loss to decide which examples deserve more attention. The method reduces the cost of fine-tuning in our setting and is easy to combine with existing training pipelines. Future work will study adaptive values of alpha and robustness to label noise.

<!-- b25 | heading 1 | p2 -->
References

<!-- b26 | reference | keep | p2 -->
[1] A. Vaswani, N. Shazeer, N. Parmar, J. Uszkoreit, L. Jones, A. N. Gomez, L. Kaiser, and I. Polosukhin. Attention is all you need. In Advances in Neural Information Processing Systems, 2017.

<!-- b27 | reference | keep | p2 -->
[2] Y. Bengio, J. Louradour, R. Collobert, and J. Weston. Curriculum learning. In Proceedings of the 26th International Conference on Machine Learning, 2009.

<!-- b28 | reference | keep | p2 -->
[3] N. Srivastava, G. Hinton, A. Krizhevsky, I. Sutskever, and R. Salakhutdinov. Dropout: A simple way to prevent neural networks from overfitting. Journal of Machine Learning Research, 15:1929-1958, 2014.

<!-- b29 | reference | keep | p2 -->
[4] D. P. Kingma and J. Ba. Adam: A method for stochastic optimization. In International Conference on Learning Representations, 2015.

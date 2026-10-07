<!-- page 2 of 2 -->
subset. A small constant eps guarantees that every example keeps a non-zero probability of being
selected, so that easy examples are revisited and the model does not forget them. We optimize the
weights with Adam [4] and apply dropout [3] with rate 0.1, as in standard fine-tuning of Transformer
encoders [1].
3 Experiments
We fine-tune a 110M-parameter encoder on three public text classification datasets, denoted A, B
and C, with 12k, 45k and 120k training examples. Each configuration is repeated with five random
seeds, and we report the mean accuracy on the test set together with the standard deviation. The
baseline uses uniform sampling with the same learning rate of 2e-5 and a batch size of 32.
Table 1: Test accuracy (%) and number of gradient updates (thousands) on the three datasets. Values are
mean ± standard deviation over five seeds.
Method  Data A  Data B  Data C  Updates (k)
Uniform  86.1 ± 0.9  90.4 ± 0.5  93.2 ± 0.3  52.0
SCS (alpha = 1)  86.3 ± 0.6  90.6 ± 0.4  93.1 ± 0.2  32.2
SCS (alpha = 2)  85.2 ± 1.1  89.9 ± 0.7  92.8 ± 0.4  30.5
As shown in Table 1, SCS with alpha = 1 matches or slightly exceeds the baseline on two of the
three datasets and stays within 0.1 points on the third, while requiring 38% fewer updates (32.2k
versus 52.0k). The lower standard deviation suggests that focusing on informative examples also
makes training more stable. With alpha = 2, however, accuracy drops on every dataset, which
indicates that an overly aggressive sampler ignores easy examples for too long.
4 Limitations
Our study has several limitations. All experiments use classification tasks and a single model size,
so it is unclear whether the gains hold for text generation or for models with billions of parameters. In
addition, noisy labels may receive persistently high losses; in such cases SCS could repeatedly
sample mislabeled examples and amplify the noise.
5 Conclusion
We presented Sparse Curriculum Sampling, a lightweight method that reuses the training loss to
decide which examples deserve more attention. The method reduces the cost of fine-tuning in our
setting and is easy to combine with existing training pipelines. Future work will study adaptive values
of alpha and robustness to label noise.
References
[1] A. Vaswani, N. Shazeer, N. Parmar, J. Uszkoreit, L. Jones, A. N. Gomez, L. Kaiser, and I. Polosukhin.
Attention is all you need. In Advances in Neural Information Processing Systems, 2017.
[2] Y. Bengio, J. Louradour, R. Collobert, and J. Weston. Curriculum learning. In Proceedings of the 26th
International Conference on Machine Learning, 2009.
[3] N. Srivastava, G. Hinton, A. Krizhevsky, I. Sutskever, and R. Salakhutdinov. Dropout: A simple way to
prevent neural networks from overfitting. Journal of Machine Learning Research, 15:1929-1958, 2014.
[4] D. P. Kingma and J. Ba. Adam: A method for stochastic optimization. In International Conference on
Learning Representations, 2015.

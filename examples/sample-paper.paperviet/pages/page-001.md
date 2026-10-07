<!-- page 1 of 2 -->
Sparse Curriculum Sampling for Efficient Fine-Tuning
of Small Language Models
An Tran and Laura Hayes
Demo Institute of Computing (fictional affiliation)
Abstract
Fine-tuning a pretrained language model on a new task usually requires many passes over the
training set, even though a large fraction of the examples are already handled well after the
first epoch. We propose Sparse Curriculum Sampling (SCS), a simple data selection method
that estimates the difficulty of each example from its recent loss and samples hard examples
more often while still revisiting easy ones. SCS adds no trainable parameters and can be
implemented in a few lines of code. On three text classification benchmarks, SCS reaches the
accuracy of standard fine-tuning while using 38% fewer gradient updates, and it reduces the
variance across random seeds. We also discuss when the method fails and why its gains may
not transfer to generation tasks.
1 Introduction
Small language models with fewer than one billion parameters remain attractive for laboratories and
companies with limited computing budgets. However, fine-tuning such a model still involves a
trade-off between cost and accuracy: training for more epochs tends to improve the final score, but
most of the additional computation is spent on examples that the model has already learned.
Curriculum learning [2] addresses a related problem by presenting examples in a meaningful order,
usually from easy to hard. In practice, a fixed curriculum requires a difficulty measure defined before
training, which is often unavailable for new datasets. In this paper, we take a different view: instead
of ordering the data once, we let the model's own training signal decide how often each example
should be seen.
Our contributions are threefold. First, we introduce SCS, a sampling rule based on an exponential
moving average of the per-example loss. Second, we show empirically that SCS reduces the
number of gradient updates without hurting accuracy. Third, we analyze the failure cases of the
method, which, to the best of our knowledge, have not been reported for similar approaches.
2 Method
Let D = {(x_i, y_i)}, i = 1..N, be the training set and f(x; w) a classifier with weights w. At step t, we
keep a difficulty score s_i for every example, updated whenever the example is visited:
s_i <- beta * s_i + (1 - beta) * L(f(x_i; w), y_i)  (1)
where L is the cross-entropy loss and beta is a smoothing factor set to 0.9 in all experiments.
Examples are then drawn with probability
p_i = (s_i + eps)^alpha / sum_j (s_j + eps)^alpha  (2)
The exponent alpha controls how strongly the sampler focuses on hard examples: alpha = 0
recovers uniform sampling, whereas large values concentrate the probability mass on a small
* This is a fictional paper written for the PaperViet demo. The method and all numbers are invented; only the references are real.

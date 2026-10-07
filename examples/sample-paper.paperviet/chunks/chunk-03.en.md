<!-- paperviet chunk-03 | 5 blocks | ~113 words to translate | 4 Limitations -->
<!-- Translate every block below into Vietnamese and save as translations/chunk-03.vi.md.
     Keep every block-marker comment line (the one holding the block id, e.g. b12) unchanged and
     in order; replace only the English text under it.
     Blocks tagged "keep" (equations, tables, references, authors) may be omitted or copied as-is.
     Never translate math, code, variable names, citations like [3], URLs, or names. -->

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

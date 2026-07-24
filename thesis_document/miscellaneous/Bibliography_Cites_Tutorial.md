
```sh
# 1. Export collection from Zotero as BibTex.
# 2. Save the file as reference.bib
# 3. Upload the file to overleaf
# 4. Example:

# main.tex
\documentclass{article}

\begin{document}

Test citation \cite{testkey}.

\bibliographystyle{plain}
\bibliography{references}

\end{document}

# references.bib
@article{testkey,
  title={Test Title},
  author={Doe, John},
  year={2023}
}

# GOTCHA: The bibliography will only appear when you have cited at least one document.
# Only cited documents will appear on the bibliography
```
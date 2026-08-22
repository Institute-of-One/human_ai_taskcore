# paper/ — IORN-009A 原稿作業ディレクトリ

M4 で `manuscript.md`(英語正本)と `make_figures.py`(results.json 駆動)を
ここに置く。パイプラインは IORN-002 方式(CLAUDE.md 参照):

```
python make_figures.py            # results.json + figs/*.png
pandoc -f markdown-implicit_figures manuscript.md \
  --reference-doc=reference.docx -o manuscript.docx
```

提出専用ファイル(response letters, cover letters, susy_*.txt)は
.gitignore 済み — コミットしない。

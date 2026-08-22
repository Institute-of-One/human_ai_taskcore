# SETUP_GIT.md — 初回セットアップ(Cursor+Claude CLI で実行)

このファイルは初回セットアップ後に削除してよい。Claude への指示は
「SETUP_GIT.md を実行して」で足りる。

## 1. CI ワークフローの設置

`.github/workflows/ci.yml` はリモートセッションから書き込めない(保護対象)。
以下の内容でローカル作成すること:

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - name: Install
        run: pip install -e ".[dev]"
      - name: Literature-anchor and analytic tests
        run: pytest -q
```

## 2. 重複ファイルの整理

リポジトリ直下の `IORN-009A_research_protocol_v0.3.md` / `.docx` は
`docs/` に正本があるため削除してよい(docx はコミット不要)。

## 3. 動作確認

```bash
pip install -e ".[dev]"
pytest -q        # 30 tests, all green のはず
```

## 4. Git 初期化と GitHub 連携

```bash
git init -b main
git add -A
git commit -m "feat: IORN-009 M1 skeleton — ptx chain/detectability with literature-anchor tests"
gh repo create Institute-of-One/human_ai_taskcore --private --source=. --push
```

(公開リポジトリにするタイミングは論文投稿時に判断 — IORN-002 と同様)

## 5. 完了後

```bash
rm SETUP_GIT.md
git add -A && git commit -m "chore: remove setup notes"
```

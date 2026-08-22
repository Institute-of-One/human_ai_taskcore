# CLAUDE.md — human_ai_taskcore (IORN-009)

このリポジトリで作業する Claude への恒久コンテキスト。**毎セッション最初に読むこと。**

## プロジェクト識別

- **プロジェクト:** IORN-009 (Institute of One Research Note 009) — Physics-to-Perception Framework
- **009A:** Human branch — scanner→display→eye→cognition の閉形式情報積分、f_sat / G_useful / R_perceptual
- **009B:** AI branch — Human–AI spectral utilization gap(009Aでは実装しない。定義は温存)
- **研究計画書(正本):** `docs/IORN-009A_research_protocol_v0.3.md` — 仮説 H1/H2/H3、超越点 N1–N5、リスク登録簿を必ず参照
- **先行プロジェクト:** IORN-002 = radiomics-phantom (*J. Imaging* 2026, 12, 392, doi:10.3390/jimaging12080392)。本リポジトリは同プロジェクトの設計原則を全面継承する
- **著者:** Shuji Yamamoto (Institute of One, LISIT Co., Ltd., Tokyo; yamamoto@lisit.jp; ORCID 0000-0001-9211-1071)

## パッケージ名について

リポジトリ名は `human_ai_taskcore`、Python パッケージ名は **`ptx`**(= physics-to-perception transfer core)。計画書の module 構成(`ptx/chain.py` 等)と一致させている。改名しないこと。

## 設計原則(IORN-002から継承・変更禁止)

1. **決定論:** 全乱数は明示 seed。同じ入力 → バイト同一の出力。`Date.now` 的な非決定要素をコードに入れない
2. **results.json 駆動:** 論文中の全数値は `paper/make_figures.py`(将来作成)が生成する results.json から取り、本文に手書きの数値を置かない
3. **独立実装+文献照合:** 外部ライブラリの高レベル実装に依存せず numpy/scipy で独立実装し、文献の数表・標準規格(DICOM PS3.14 等)と照合するテストを CI で常時実行
4. **区間主義:** 点推定より不確実性帯。η_cog 等は範囲パラメータとして伝播(計画書 §5.4)
5. **主張の限定:** 「診断できる」とは決して書かない。「指定した表示・視覚条件の下で情報が届く/届かない」の条件付き主張のみ

## 論文パイプライン(IORN-002方式)

- 原稿正本は `paper/*.md`(英語)。pandoc で docx 化:
  `pandoc -f markdown-implicit_figures 原稿.md --reference-doc=reference.docx -o 原稿.docx`
- 改訂時のハイライトは `[...]{custom-style="HL"}` スパン(reference.docx に HL 文字スタイル+w:highlight パッチ)
- **-f markdown-implicit_figures を忘れない**(図の alt text がキャプション化して重複する事故防止)
- LibreOffice で PDF 化すると OMML 数式が落ちる。ジャーナルへは docx を出す

## Git 運用

- **正本は D:\DevGit\human_ai_taskcore。** F:\ はバックアップSSD(誤って F: で作業しない)
- コミットは Conventional Commits 風の簡潔な英語メッセージ
- `review_evidence/` は**絶対にコミットしない**(.gitignore 済み)。査読対応の証拠保全用
- Cowork(クラウド)セッションからの push は proxy 制限で失敗することがある。push はローカル(Cursor+Claude CLI)から行う

## 査読対応プロトコル(IORN-002の経験則)

- 査読コメントは verbatim で記録してから対応(`review_evidence/` に全文保存+スクリーンショット)
- 引用強要(無関係文献の追加要求)は MDPI 型チェックリスト「recommended references should be included only where they enhance the manuscript」を根拠に丁重に辞退し、エディタへ separate cover で報告
- 統計的誠実さが最強の防御:批判には追加実験・分解・CI で数値的に応答する

## 現在のマイルストーン

- **M1(今ここ):** chain.py(GSDF/眼球MTF/Barten CSF+文献照合テスト)+骨格 — 本コミットで着手
- **M2:** phantom_lung.py 本実装+observer 2系統(NPWE/CHO)+d'積分で Phase 1 完走
- **M3:** 不確実性伝播+U-HRCTケーススタディ(H3)+Phase 2 digitize外部検証
- **M4:** 原稿執筆(第一候補 Medical Physics)

## テスト実行

```bash
pip install -e ".[dev]"   # 初回
pytest -q                  # 全テスト
```

CI(GitHub Actions)は push ごとに Python 3.11/3.12 で pytest を回す。

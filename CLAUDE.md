# CLAUDE.md — human_ai_taskcore (IORN-009)

このリポジトリで作業する Claude への恒久コンテキスト。**毎セッション最初に読むこと。**

## プロジェクト識別

- **プロジェクト:** IORN-009 (Institute of One Research Note 009) — Physics-to-Perception Framework
- **009A:** Human branch — scanner→display→eye→cognition の閉形式情報積分、f_sat / G_useful / R_perceptual
- **009B:** AI branch — Human–AI spectral utilization gap(009Aでは実装しない。定義は温存)
- **研究計画書(正本):** `docs/IORN-009A_research_protocol_v0.4.md` — 仮説 H1/H2/H3、超越点 N1–N5、リスク登録簿を必ず参照。v0.4 で定式化を確定(CSF は分母=神経内部雑音、N_internal 三分割、H3 は f_sat回復+十分拡大率 Z*)
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
- **リモート:** `origin` = https://github.com/Institute-of-One/human_ai_taskcore (private)。公開は論文投稿時に判断(IORN-002 と同様)
- コミットは Conventional Commits 風の簡潔な英語メッセージ
- git の `user.name` / `user.email` はこの環境では未設定。設定するまでは commit 時に
  `git -c user.name="Shuji Yamamoto" -c user.email="yamamoto@lisit.jp" commit ...` で作者を明示する
- `review_evidence/` は**絶対にコミットしない**(.gitignore 済み)。査読対応の証拠保全用
- Cowork(クラウド)セッションからの push は proxy 制限で失敗することがある。push はローカル(Cursor+Claude CLI)から行う

## 査読対応プロトコル(IORN-002の経験則)

- 査読コメントは verbatim で記録してから対応(`review_evidence/` に全文保存+スクリーンショット)
- 引用強要(無関係文献の追加要求)は MDPI 型チェックリスト「recommended references should be included only where they enhance the manuscript」を根拠に丁重に辞退し、エディタへ separate cover で報告
- 統計的誠実さが最強の防御:批判には追加実験・分解・CI で数値的に応答する

## 現在のマイルストーン

- **M1(完了):** chain.py(GSDF/眼球MTF/Barten CSF+文献照合テスト)+骨格
- **M2(完了):** phantom_lung.py 本実装+observer 2系統(NPWE/CHO)+d'積分で Phase 1 完走。`ptx/phase1.py` が §7 のグリッド(540条件)を回して `results/phase1.json` を決定論的に生成
- **M3(今ここ):** 不確実性伝播(`ptx/uncertainty.py`, 完了)+U-HRCTケーススタディ(`ptx/case_uhrct.py`, (M,D) マップと M*、完了)+**Phase 2 digitize外部検証(`ptx/external.py`, H2)が残り**
- **M4:** 原稿執筆(第一候補 Medical Physics)

**Phase 2(H2)の現状:** 基準・スキーマとも**性能データを一切抽出しない状態で凍結済み**(`docs/IORN-009A_H2_preregistration_v1.0.md` → `v1.1` → `v1.2` → `v1.3`、各々別コミット)。**C2 の現行正本は v1.2 の原則:条件軸として認めるのはモデルの宣言済み入力(`Acquisition`/`Reading`/`Task` のフィールド)に対応する軸のみ**(正本は `ptx/external.py` の `AXIS_TO_MODEL_INPUT`、テストが両方向の網羅を検査)。**v1.3 でスキーマ全体を凍結**(記述変数 `task_congruence` を必須追加。除外力なし・§5-3 の層別専用)。**以後の基準・スキーマ変更はモデル拡張を伴う v2.0 のみ。抽出の途中でフィールドを足さない**(必要なら `notes` に自由記述)。解析は3プール併記(v1.0厳格/v1.1/v1.2)で「3版すべてで結論が同方向」が成功条件、層別は記述のみで主判定を置き換えない。候補表は `docs/h2_candidate_scan_v1.1.md`(v1・v1.1 とも改訂の開示に引用されているため**改変しない**)。

**次の作業(抽出フェーズ):** CAND-01(PMC3618092、`task_congruence=ske`)と CAND-13(PMC3724792、`search_or_location_uncertain`、**ROC AUC のみ使用・LROC は使わない**)を `data/h2_studies.json` の `studies` に、CAND-14 を `screened` に転記する(除外理由は `unpredictable_axis_reason` の定型文)。採否は v1.3 §C で機械判定済み。

### M2 で確定した定式化(v0.4 裁定・変更禁止)

1. **主形式は CSF 分母形式。** 視覚感度は N_effective の神経内部雑音項 N_neural(f) = κ²(WW·a)²Φ(af) として入る。v0.3 の分子重み形式は「可逆フィルタ不変性が成立する理想極限」として付録に温存し、results.json に `*_csf_weight` として併記する
2. **N_internal は三分割**(画像/表示量子化/神経)。注入位置で MTF の掛かり方が違う。床項を |H_display|² の外に置くことが画素ピッチ・拡大率が効く唯一の経路
3. **カーネル約分(床項オフで機械精度の不変性)は validation 結果として保存する。** 消してはいけない
4. **H3 は「f_sat 回復 + 十分拡大率 Z*」**。d′ は漸近飽和し内点最適を持たない(実測)

### M3 で確定した扱い

5. **f_sat は位置の指標。** κ を上げると d′ は下がるが f_sat は上がる(神経雑音が低周波支配)。f_sat と d′/G_useful は必ず並べて報告する
6. **H1 の判定は G_useful の減衰量 ΔG の95%帯下限で行う。** G_useful 自体は符号が常に正で情報を持たない
7. **チェーン比較は等線量=同一投影雑音スケールで行う**(画素分散を揃えない)。マップの軸は画素ズーム Z ではなく解剖学的拡大率 M

未決事項(典拠未確定の区間・公表値の代用)は `paper/NOTES.md` の「M4までに決着させる未決事項」に記録。**着手前に必ず読むこと。**

## テスト実行と結果再生成

```bash
pip install -e ".[dev]"                      # 初回
python -m pytest -q                          # 全テスト
python -m ptx.phase1 --out results/phase1.json          # Phase 1(540条件)
python -m ptx.uncertainty --out results/uncertainty.json # §5.4 区間伝播
python -m ptx.case_uhrct --out results/case_uhrct.json   # H3 (M,D) マップ
```

results/*.json は3本すべて git 追跡対象。再実行してハッシュが変わったら決定論が壊れている。

Windows ローカル環境では `pytest` が PATH に載らないため `python -m pytest` を使う。

CI(GitHub Actions)は push ごとに Python 3.11/3.12 で pytest を回す(`.github/workflows/ci.yml`)。

`np.trapezoid` を使っているため numpy>=2.0 が必要(pyproject に明記済み)。

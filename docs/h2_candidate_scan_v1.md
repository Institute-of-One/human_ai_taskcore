# H2 系統調査 — 候補文献スキャン v1

**作成:** 2026-08-23(Cowork セッション)
**準拠:** `docs/IORN-009A_H2_preregistration_v1.0.md`(凍結 2026-08-23)。**本スキャンは凍結コミット後に実施。**
**方法:** Web 検索(検索語は付記)。本スキャンは「候補の列挙と C1–C6 の予備判定」であり、採否判定ではない。凡例: ○=満たす見込み / △=要PDF確認 / ×=満たさない見込み。**△の項目は PDF 取得後に `ptx/external.py` スキーマで正式判定する。**

## A. CT — モデルオブザーバー–人間相関クラスタ(H2 主力)

| ID | 文献 | 条件軸(把握分) | 指標 | C1 | C2 | C3 | C4 | C5 | C6 | 優先度 |
|---|---|---|---|---|---|---|---|---|---|---|
| CAND-01 | Yu L, Leng S, et al. Prediction of human observer performance in a 2AFC low-contrast detection task using CHO: impact of radiation dose and reconstruction algorithms. *Med Phys* 2013;40:041908 | 線量×再構成(FBP/逐次)×対象サイズ・コントラスト | 2AFC PC | ○ | ○ | ○ | △ | ○ | △ | **最高** |
| CAND-02 | 2D CHO と人間観察者の相関(multislice reading、低コントラスト検出)。*Med Phys* 2017(PMID 28555878) | 線量×スライス読影条件 | PC/AUC | ○ | △ | △ | △ | △ | △ | 高 |
| CAND-03 | CHO–人間相関(肝低コントラスト検出、liver CT)。(PMC6527401) | 線量×病変サイズ/コントラスト | AUC/PC | ○ | △ | △ | △ | △ | △ | 高 |

## B. CT — 肺結節検出・線量依存クラスタ(タスク現実性)

| ID | 文献 | 条件軸(把握分) | 指標 | C1 | C2 | C3 | C4 | C5 | C6 | 優先度 |
|---|---|---|---|---|---|---|---|---|---|---|
| CAND-04 | Paul J, et al. Investigating the low-dose limits of multidetector CT in lung nodule surveillance. *Med Phys* 2007;34 (doi:10.1118/1.2768866) | 線量×結節サイズ | ROC/AUC | ○ | ○ | △ | △ | △ | △ | 高 |
| CAND-05 | 超低線量CT+ex vivo肺ファントムの人工結節検出(PMC5752031) | 線量×再構成 | 感度系 | ○ | △ | △ | △ | **×懸念**(感度のみならC5落ち) | △ | 中 |
| CAND-06 | 320列CT低線量の肺結節検出能(Johns Hopkins) | 線量×結節条件 | AUC? | ○ | △ | △ | △ | △ | △ | 中 |

## C. 胸部X線 — 汎用性検証枠(≥1本必須・シカゴ系譜優先)

| ID | 文献 | 条件軸(把握分) | 指標 | C1 | C2 | C3 | C4 | C5 | C6 | 優先度 |
|---|---|---|---|---|---|---|---|---|---|---|
| CAND-07 | MacMahon H, Vyborny CJ, Metz CE, Doi K, et al. Digital radiography of subtle pulmonary abnormalities: an ROC study of the effect of pixel size on observer performance. *Radiology* 1986;158:21–26(PMID 3940383)— **Rossmann研究室そのもの** | 画素サイズ(1軸+タスク種別) | ROC/AUC | ○ | **△(軸数1の懸念)** | △ | △ | ○ | △ | **高(系譜価値)** |
| CAND-08 | Effects of Luminance and Resolution on Observer Performance with Chest Radiographs. *Radiology* 2000;215:169– | **輝度×解像度(2軸)** | ROC/AUC | ○ | ○ | △ | △ | ○ | △ | **最高(C2確実)** |
| CAND-09 | Digital storage phosphor chest radiography: 2K vs 4K matrix ROC. *Radiology* 2001;218 | マトリクス(1軸) | ROC/AUC | ○ | **△(軸数1)** | △ | △ | ○ | △ | 中 |
| CAND-10 | Spatial resolution requirements for digital chest radiographs: ROC observer study. *Radiology* 1986;158(PMID 3940365、同じくシカゴ系) | 解像度条件 | ROC/AUC | ○ | △ | △ | △ | ○ | △ | 中 |

## D. U-HRCT 照合用(H3 外部照合。H2 プールには入れない)

| ID | 文献 | 用途 |
|---|---|---|
| CAND-11 | U-HRCT vs 従来CT 結節評価 multireader 研究(*J Clin Imaging Sci*) | H3 の (Z,D) マップ予測と定性照合 |
| CAND-12 | Kakinuma R, et al. *PLOS ONE* 2015(計画書 §2.2 で引用済み) | H3 の表示条件(9MP・DFOV80mm)照合 |

## 予備判定の要点

1. **C5 に注意。** 感度(sensitivity)のみ報告の研究(CAND-05系)は AUC/PC/d′ でないため C5 で落ちる見込み。スクリーニング時に本文で AUC 併記がないか確認。
2. **胸部X線枠は CAND-08 を第一候補**(2軸で C2 確実)、**CAND-07 を系譜価値で並走**(C2 は「画素サイズ+異常種別」を軸2と数えられるかが論点 — 事前登録の C2 定義では物理条件軸に限る読みが自然なので、落ちる場合も除外記録に残して補遺で言及する価値が高い)。
3. **CAND-01 が要石。** 2AFC PC・複数線量・複数再構成・複数サイズで C1–C5 がほぼ確実。PDF を最優先で取得。
4. 検索は PubMed/PMC が bot 対策で断続的に読めないため、**書誌の細部(著者名の完全な並び・巻号頁)はPDF取得時に確定**すること。
5. 本表のすべての △ は `data/h2_studies.json` の `screened` に判定根拠つきで記録して初めて確定する(事前登録 §3)。

## 検索語(記録)

- "low-dose CT lung nodule detection human observer performance AUC dose levels 2AFC"
- "channelized Hotelling observer human observer correlation CT dose reduction detection"
- "MacMahon Metz Doi ROC chest radiography observer performance pixel size"
- "lung nodule detectability 2AFC reduced dose CT screening human observer"

## 次のアクション

1. Shuji さん:CAND-01, -04, -07, -08 の PDF を最優先で入手(機関アクセス or オープンアクセス版)
2. Cursor 側:PDF 到着順に C1–C6 正式判定 → `data/h2_studies.json` へ記録(採用・除外とも)
3. digitize が必要な図は独立2回で C6 判定(±5%)

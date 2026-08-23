# H2 系統調査 — 候補文献スキャン v1.1

**作成:** 2026-08-23(v1 = Cowork セッション、v1.1 = 本追記)
**準拠:** `docs/IORN-009A_H2_preregistration_v1.0.md`(凍結 2026-08-23、コミット `6b77ee3`)+ `..._v1.1.md`(改訂凍結、コミット `3ca25e2`)
**前版:** `docs/h2_candidate_scan_v1.md` — **改変しない。** 事前登録 v1.1 §B が「改訂時点で閲覧していた候補の一覧」として v1 を参照しているため、v1 は当時のスナップショットとして保存する。

**現在の作業段階(宣言):** タイトル・抄録レベルの閲覧のみ。**条件別性能データ(AUC・PC・$d'$)の抽出、図からの digitize、モデル予測との比較(順位相関の計算)はいずれも一件も実施していない。** 抄録に記載された研究レベルの統計量(著者ら自身が報告する model–human 相関係数など)は本枠組みの入力データではなく、記録もしない。

**v1 からの差分:**

1. CAND-01 の書誌を確定し、**無料 PDF の入手経路(PMC3618092)を記録**
2. CAND-08 の書誌を確定(著者・巻号頁・DOI)
3. **CAND-13(Leng 2013、位置不確実)と CAND-14(Goo 2004、輝度×環境光)を追加**
4. **C2 の語彙に関する重大な論点を §予備判定の要点 5 に記録**(輝度・環境光は現行語彙外)

**追加分の時系列(重要):** CAND-13・CAND-14 は事前登録 v1.1 の凍結コミット `3ca25e2` **より後**に閲覧した。したがって事前登録 v1.1 §B の閲覧済みリスト(= 本表 v1)には含まれない。今後さらに改訂を行う場合、その改訂の開示は本表 v1.1 を閲覧済みリストとして参照すること。

凡例: ○=満たす見込み / △=要PDF確認 / ×=満たさない見込み。**すべての判定は PDF 取得後に `ptx/external.py` のスキーマで正式に行い、採否とも `data/h2_studies.json` に記録して初めて確定する。**

## A. CT — モデルオブザーバー–人間相関クラスタ(H2 主力)

| ID | 文献 | 条件軸(語彙表記) | 指標 | C1 | C2 | C3 | C4 | C5 | C6 | 優先度 |
|---|---|---|---|---|---|---|---|---|---|---|
| **CAND-01** | Yu L, et al.(全著者名は要PDF確認)Prediction of human observer performance in a 2-alternative forced choice low-contrast detection task using channelized Hotelling observer: impact of radiation dose and reconstruction algorithms. *Med Phys* 2013;40(4):041908. doi:10.1118/1.4794498(PMID 23556902、**PMC3618092 = 無料全文**) | `dose`(5水準)× `reconstruction`(FBP/IR)× `lesion_size`(3水準) | 2AFC PC | ○ | **○(3軸)** | **○(21の2AFC study)** | △ | **○** | △ | **最高** |
| CAND-13 | Leng S, Yu L, Zhang Y, Carter R, Toledano AY, McCollough CH. Correlation between model observer and human observer performance in CT imaging when lesion location is uncertain. *Med Phys* 2013;40(8):081908. doi:10.1118/1.4812430(PMID 23927322、**PMC3724792 = 無料全文**) | `dose`(4水準)× `lesion_size`(2水準) | AUC(ROC)+AUC(LROC) | ○ | **○(2軸)** | **○(8点)** | △ | **△(下記注)** | △ | **高** |
| CAND-02 | 2D CHO と人間観察者の相関(multislice reading、低コントラスト検出)。*Med Phys* 2017(PMID 28555878) | `dose` × 読影条件 | PC/AUC | ○ | △ | △ | △ | △ | △ | 高 |
| CAND-03 | CHO–人間相関(肝低コントラスト検出)。(PMC6527401) | `dose` × `lesion_size`/`contrast` | AUC/PC | ○ | △ | △ | △ | △ | △ | 高 |

**CAND-01 が本枠組みと適合する理由(設計上の一致、性能データとは無関係):** 均一水ファントム中の低コントラスト円柱ロッド検出であり、**背景が均一・信号既知**という本モデルの前提(§2.1)にそのまま対応する。解剖学的雑音の混入がないため、予測は CT の NPS と課題スペクトル(円板)だけで構成でき、`ptx/phantom_lung.py` の肺テクスチャを使わない最も単純な写像になる。コントラストは −15 HU 固定で、条件軸が線量・再構成・径に限られる点も予測側の自由度を小さくする。

**CAND-13 の C5 注記:** 本研究は AUC(ROC) と AUC(LROC) の両方を報告する。事前登録 §5.4 の指標変換($d' = \sqrt{2}\,\Phi^{-1}(\mathrm{AUC})$)は**等分散2正規 ROC を前提とする恒等式であり、LROC AUC には成立しない**。したがって採用する場合は **ROC AUC のみを用い、LROC AUC は使わない**(この扱いを登録簿の `notes` に明記する)。

**CAND-13 の適用範囲上の論点(判断が必要):** 位置不確実性(探索過程)に対応する項は本モデルに存在しない。ROC AUC を使えば局在化要件は外れるが、画像内の信号位置が可変であること自体は残る。選択肢は (a) ROC AUC で採用し Limitations に探索過程の非モデル化を明示、(b) 適用範囲外として除外し除外記録に残す。**採否は PDF 確認後に判断し、判断理由を登録簿に残す。**

## B. CT — 肺結節検出・線量依存クラスタ(タスク現実性)

| ID | 文献 | 条件軸(語彙表記) | 指標 | C1 | C2 | C3 | C4 | C5 | C6 | 優先度 |
|---|---|---|---|---|---|---|---|---|---|---|
| CAND-04 | Paul J, et al. Investigating the low-dose limits of multidetector CT in lung nodule surveillance. *Med Phys* 2007;34(doi:10.1118/1.2768866) | `dose` × `lesion_size` | ROC/AUC | ○ | ○ | △ | △ | △ | △ | 高 |
| CAND-05 | 超低線量CT+ex vivo肺ファントムの人工結節検出(PMC5752031) | `dose` × `reconstruction` | 感度系 | ○ | △ | △ | △ | **×懸念**(感度のみなら C5 落ち) | △ | 中 |
| CAND-06 | 320列CT低線量の肺結節検出能(Johns Hopkins) | `dose` × 結節条件 | AUC? | ○ | △ | △ | △ | △ | △ | 中 |

## C. 胸部X線 — 汎用性検証枠(≥1本必須・シカゴ系譜優先)

| ID | 文献 | 条件軸(語彙表記) | 指標 | C1 | C2 | C3 | C4 | C5 | C6 | 優先度 |
|---|---|---|---|---|---|---|---|---|---|---|
| CAND-08 | Herron JM, Bender TM, Campbell WL, Sumkin JH, Rockette HE, Gur D. Effects of Luminance and Resolution on Observer Performance with Chest Radiographs. *Radiology* 2000;215(1):169–174. doi:10.1148/radiology.215.1.r00ap34169 | 輝度 × 解像度(`pixel_size`/`displayed_matrix`) | ROC/AUC | ○ | **△→論点5に依存(輝度が語彙外のため現行では1軸)** | △ | △ | ○ | △ | **最高(論点5が解けば)** |
| CAND-07 | MacMahon H, Vyborny CJ, Metz CE, Doi K, et al. Digital radiography of subtle pulmonary abnormalities: an ROC study of the effect of pixel size on observer performance. *Radiology* 1986;158:21–26(PMID 3940383)— **Rossmann研究室** | `pixel_size` (+ 異常種別) | ROC/AUC | ○ | **△(軸数1の懸念)** | △ | △ | ○ | △ | **高(系譜価値)** |
| CAND-09 | Digital storage phosphor chest radiography: 2K vs 4K matrix ROC. *Radiology* 2001;218 | `displayed_matrix`(1軸) | ROC/AUC | ○ | **△(軸数1)** | △ | △ | ○ | △ | 中 |
| CAND-10 | Spatial resolution requirements for digital chest radiographs: ROC observer study. *Radiology* 1986;158(PMID 3940365、シカゴ系) | 解像度条件 | ROC/AUC | ○ | △ | △ | △ | ○ | △ | 中 |
| CAND-14 | Goo JM, et al. Effect of monitor luminance and ambient light on observer performance in soft-copy reading of digital chest radiographs. *Radiology* 2004;232(3). doi:10.1148/radiol.2323030628(PMID 15273338、頁は要PDF確認) | 輝度(3水準)× 環境光(3水準)= 9モード | ROC/AUC | ○ | **×(両軸とも語彙外。環境光はモデルに項がない)** | △ | **×懸念(下記)** | ○ | △ | 低〜中(論点提示用) |

**CAND-14 の C4 懸念(重大):** 観察者がウィンドウ幅・レベルを自由に調整できる設計である。本モデルはウィンドウ幅を固定入力(`Reading.window_width_hu`)として扱うため、**表示条件が観察者ごとに可変で特定できない**。事前登録 C4 は「除外せず既定値で補完+感度分析」を定めているが、可変であって未記載ではないため、補完では対処できない。

**CAND-14 の情報量に関する注記:** 抄録段階の記述では条件間の差がほぼ検出されていない。順位検証は条件間に順位が存在することを前提とするため、**順位がほぼ縮退した研究は Spearman ρ の推定が雑音支配になる**。採否判断ではこの点を明示する(除外する場合の理由は「C2 語彙外」を主、情報量は従とする — 事後的に都合のよい基準を作らないため)。

## D. U-HRCT 照合用(H3 外部照合。H2 プールには入れない)

| ID | 文献 | 用途 |
|---|---|---|
| CAND-11 | U-HRCT vs 従来CT 結節評価 multireader 研究(*J Clin Imaging Sci*) | H3 の (M,D) マップ予測と定性照合 |
| CAND-12 | Kakinuma R, et al. *PLOS ONE* 2015(計画書 §2.2 で引用済み) | H3 の表示条件(9MP・DFOV80mm)照合 |

## 予備判定の要点

1. **C5 に注意。** 感度のみ報告の研究(CAND-05系)は AUC/PC/$d'$ でないため C5 で落ちる見込み。
2. **CAND-01 が要石。** 3条件軸・2AFC PC・均一背景・信号既知で C1–C3・C5 がほぼ確実、かつ**無料全文(PMC3618092)で入手可**。最優先。
3. **CAND-13 が第二の柱。** 同一グループ・同一ファントム系で `dose × lesion_size` の2軸、無料全文。適用範囲(位置不確実)と指標(ROC/LROC)の扱いを決める必要がある。
4. 書誌の細部は PDF 取得時に確定する。誌名・巻号・DOI・PMID が確定済みなのは CAND-01・CAND-08・CAND-13・CAND-14(CAND-14 は頁未確定)。**著者名の完全な並びが確認済みなのは CAND-08・CAND-13 のみ**で、CAND-01・CAND-14 は筆頭著者以降を「et al.」に留めている(検索結果で確認できた範囲を超えて書かない)。
5. **【要判断・重大】C2 の語彙が表示条件軸を含まない。** 事前登録 v1.1 の語彙は `dose`/`lesion_size`/`contrast`/`reconstruction`/`processing`/`pixel_size`/`displayed_matrix` である。**輝度・環境光はここに無い。** 帰結:
   - CAND-08(輝度×解像度)は現行語彙では解像度の1軸のみとなり **C2 で落ちる**。CAND-08 は非CT枠の第一候補だったため、**汎用性検証枠が CAND-07/09/10(いずれも軸数1の懸念)に依存する**という状態になる。
   - 一方で**輝度は本モデルの宣言済み入力**(`Reading.luminance_cdm2`、Barten CSF に入る)であり、**環境光は本モデルに項が存在しない**(ベイリンググレア項なし)。すなわち両者は性質が異なり、「表示条件だから一括で認める/認めない」という扱いは物理的に正しくない。
   - 示唆される原則:**条件軸として認めるのは「モデルの宣言済み入力パラメータに対応する軸」に限る**(`Acquisition`/`Reading`/`Task` のフィールドで決まるため、自由記述で水増しできず、新種の研究が出るたびに列挙を足す必要もない)。この原則なら輝度は可・環境光は不可・画素サイズは可(v1.1 の改訂を待たずに可だった)となる。
   - **本表では判断しない。** これは事前登録の再改訂(v1.2)を要する事項であり、候補を見た後の改訂には v1.1 と同じ開示(未抽出の宣言+閲覧済みリストとして本表 v1.1 の参照)と、追加の感度分析プール(v1.0 厳格 / v1.1 / v1.2)が必要になる。**改訂を繰り返すこと自体が査読上の攻撃面になる**ため、行うなら一度で原則ベースに移すべきであり、行わないなら CAND-08 を除外記録に残して非CT枠を別途探す。

## 検索語(記録)

v1 で記録した4件に加え、v1.1 で使用:

- "PMC3618092 channelized Hotelling observer 2AFC low-contrast detection radiation dose reconstruction algorithms Medical Physics 2013"
- "Leng 2013 Medical Physics correlation between model observer and human observer performance CT lesion location uncertainty"
- "Radiology 2004 observer performance chest radiographs monitor luminance ambient light ROC study nodule detection"

## 次のアクション

1. **CAND-01(PMC3618092)と CAND-13(PMC3724792)は無料全文が入手可。** PDF を取得して C1–C6 の正式判定 → `data/h2_studies.json` に記録(採用・除外とも)。
2. Shuji さん:CAND-04・CAND-08 の PDF を入手(機関アクセス)。CAND-08 は論点5の決着後でよい。
3. **論点5(C2 語彙と表示条件軸)の判断。** 決着するまで非CT枠の採否は保留。
4. digitize が必要な図は独立2回で C6 判定(±5%)。CAND-01・CAND-13 は PMC 全文に表があれば digitize 不要になる可能性がある(要確認)。

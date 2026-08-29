# H2 系統調査 v2 — ラウンド2(新規系統検索)

**作成:** 2026-08-29
**準拠:** `docs/IORN-009A_H2_preregistration_v2.0.md`(凍結 `0afd87d`)§6.2
**本文書の性格:** 凍結済み検索語の実行記録。**タイトル・抄録レベルの予備所見に留め、性能データは一切抽出していない**(事前登録 §6.2)。

---

## 実行記録

**実行日:** 2026-08-29
**手段:** NCBI E-utilities `esearch`(PubMed)。検索語は事前登録 §6.2 のものを**一字も変えずに**使用した。

| 件数 | 検索語(凍結済み) |
|---:|---|
| 0 | contrast-detail phantom observer study ROC AUC exposure levels radiography |
| 3 | CDRAD contrast detail human observer detectability dose |
| 0 | uniform background low contrast detection human observer AUC dose reconstruction |
| 2 | model observer human observer correlation phantom detectability radiography fluoroscopy |
| 2 | channelized Hotelling observer human observer agreement CT dose levels lesion size |
| 0 | 2AFC percent correct detection phantom image quality dose reduction observer |

**重複を除いた候補:7件。**

### 3語が0件であったことについて

PubMed は検索語をすべて AND で結合する。7〜11語からなる検索式は、そのすべてを含む文献のみを返すため極めて限定的になる。**これは凍結時に予見すべきであった設計上の弱点である。**

事前登録 v2.1 §D の決定に従い、**検索語は変更しない。** 結果を見てから語を足すことは検索の事後拡張そのものであり、それを行えば本検証の事前登録としての価値が失われる。0件であった事実と、その理由を、論文の Limitations に記載する。

---

## 候補一覧(全7件)

| # | PMID | 年 | 誌 | 表題 | 予備所見 |
|---|---|---|---|---|---|
| V2-01 | 15845936 | 2005 | Br J Radiol | Investigation of optimum energies for chest imaging using film-screen and computed radiography | 胸部撮影、コントラスト・ディテール系の可能性。**要全文** |
| V2-02 | 16306665 | 2005 | Phys Med Biol | Evaluation of a software package for automated quality assessment of contrast detail images — comparison with subjective… | **主題がソフトウェアと主観評価の一致**であり、モデル入力の軸に沿った人間観察者性能の報告ではない見込み。C2/C5 で落ちる公算 |
| V2-03 | 23556902 | 2013 | Med Phys | Prediction of human observer performance in a 2-AFC low-contrast detection task using CHO… | **第一次で採用済みの yu2013(CAND-01)そのもの。** 新規候補ではない |
| V2-04 | 24651757 | 2014 | J Comput Assist Tomogr | Multidetector-row CT allows accurate measurement of mechanical prosthetic heart valve leaflet closing… | **検出タスクではない**(弁尖運動の計測)。C1b で落ちる |
| V2-05 | 25281963 | 2014 | Med Phys | Fiducial marker and marker-less soft-tissue detection using fast MV fluoroscopy on a new generation EPID… | **MV 透視・検出タスク。非CT枠の候補。要全文** |
| V2-06 | 25776521 | 2015 | Phys Med Biol | Task-based image quality evaluation of iterative reconstruction methods for low dose CT using computer simulations | **計算機シミュレーション**。人間観察者の性能報告があるか要確認。無ければ H2 の検証には使えない。**要全文** |
| V2-07 | 40974812 | 2025 | Phys Med | Characterization of two generations of digital detectors in a radiography system: technical image quality metrics, low… | **X線撮影・低コントラスト検出の可能性。非CT枠の候補。要全文** |

### 実質的な新規候補は5件

V2-03 は既採用、V2-04 は検出タスクでない。残る5件(V2-01、-02、-05、-06、-07)が全文判定の対象となる。

**非CT枠として見込みがあるのは V2-05(MV 透視)と V2-07(X線撮影)、次いで V2-01(胸部 CR)。** いずれも量子律速の背景を持つ可能性があり、事前登録 v2.0 §2.1 が C1 を modality 列挙から適用条件へ改めた狙いに合致する。ただし**予備所見は採否ではない。**

---

## 抄録取得後の予備所見(2026-08-29、採否ではない)

5件とも PMC ID を持たず購読誌であり、**全文はプログラムから取得できない。** 抄録は事前登録 §6.2 の範囲内なので取得した。**性能データは一切抽出していない。**

| # | 抄録から読める設計 | 予備所見 |
|---|---|---|
| V2-01 Honey 2005 | **CDRAD 閾値コントラスト・ディテール・ファントム**。管電圧×曝射量。2名が light-box で採点し、閾値コントラスト指数から **visibility index (VI)** を算出 | VI は AUC・2AFC PC・$d'$ のいずれでもない。**C5 で落ちる公算が高い** |
| V2-02 Pascoal 2005 | コントラスト・ディテール画像の**自動評価ソフトと主観評価の一致**が主題 | 同上に加え、モデル入力の軸に沿った観察者性能の報告ではない見込み |
| V2-05 Poels 2014 | MV 透視・EPID 上の**フィデューシャルマーカーと軟部組織の検出**、パルス由来アーチファクトの影響 | 放射線治療の追尾・位置決めであり、人間観察者の心理物理実験ではない見込み。**C1b/C5 で落ちる公算** |
| V2-06 Xu 2015 | **計算機シミュレーション**上で CHO により逐次再構成を評価。5線量水準、XCAT ファントム | **人間観察者の性能報告が見当たらない。** H2 は人間観察者との照合であり、モデル観察者のみでは検証にならない。**C2 で落ちる公算** |
| V2-07 Mobini Kesheh 2025 | 2世代の検出器の比較。技術的画質指標、**低コントラスト検出能**、**visual grading analysis (VGA)** | VGA は順序尺度の評点であり許可指標外。低コントラスト検出能の報告形式が AUC 等であれば通る余地はあるが、**C5 で落ちる公算** |

### 構造的な観察(記録に値する)

5件のうち4件が **C5(性能指標)で落ちる見込み**であり、落ち方が一様である。ラウンド1の非CT候補(CAND-15、-16、kimmesmith1996)も同じ C5 で落ちている。

**これは偶然ではない。** 非CT の量子律速な検出研究は、その大半が**コントラスト・ディテール・ファントムの閾値指数**か **visual grading analysis** で性能を報告する。一方 AUC・2AFC の PC・$d'$ を用いる文献は、**モデル観察者と人間観察者の相関を扱う系譜**にほぼ限られ、その系譜は圧倒的に CT である。

つまり事前登録の二要件——

1. 量子雑音と神経雑音が律速する背景(v2.0 §2 の C1 改訂の狙い)
2. AUC・2AFC PC・$d'$ のいずれかで報告(C5)

——が**同時に満たされる非CT文献は稀である。** 非CT枠が埋まらないのは「そういう研究が存在しない」からではなく、**比較可能な性能指標を保証する要件と、モデルが記述できる背景を要求する要件が、文献の系譜として重ならない**からである。

**これは Limitations に書くべき知見であり、失敗の言い訳ではない。** 第一次では「非CT枠が埋まらなかった」としか言えなかったが、第二次はその**理由**を述べられる。

---

## この時点での見通し(記録)

第二次プールの要件は、事前登録 v2.1 §C により「継承分を含めて ≥6 研究、**うち新規採用 ≥3**、条件点 ≥60、非CT ≥2」である。

現時点で:

- 継承:3研究(yu2013、paul2007、leng2013)
- ラウンド1の未判定候補:CAND-02、-03(CT、要全文)、CAND-09、-10(胸部X線、要全文、C2 で落ちる公算)
- ラウンド2の新規候補:5件(要全文)

**新規採用 ≥3 と非CT ≥2 の双方を満たせるかは、全文判定を経なければ分からない。** 特に非CT枠は、ラウンド1の2件が予備所見どおり C2 で落ちれば、V2-05・V2-07・V2-01 の3件に懸かる。

---

## 次のアクション

1. 要全文9件(CAND-02、-03、-09、-10、V2-01、-02、-05、-06、-07)の入手
2. 取得順に C1–C6 を機械的に適用し、**採否とも** `data/h2_studies_v2.json` に記録
3. 全件判定の完了をもってプールを閉じる(事前登録 §6.3)
4. 閉じた後に一度だけ実行し、`results/h2_v2.json` に書く

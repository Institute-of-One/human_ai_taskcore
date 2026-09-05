# H2 第二次プール — 全文取得リスト(9件)

事前登録 v2.0 §6.3 / v2.1 §C により、**この9件の全文判定をもって第二次プールを閉じる。**
判定は取得順に C1–C6 を機械的に適用し、**採否とも** `data/h2_studies_v2.json` に記録する。

**予備所見は採否ではない。** 下表の「決め手」は全文で確認すべき一点を示すもので、
落とす理由をあらかじめ与えるものではない。C1–C6 は v1.0 から一字も変えていない。

作成 2026-09-04。DOI は全件 doi.org で解決を確認済み(出版社サイトの 403 は bot 除けであり、
DOI 自体は健全)。

---

## 無料で読める(2件)

| # | 文献 | DOI | 入手先 |
|---|---|---|---|
| **CAND-02** | Yu L, Chen B, Kofler JM, Favazza CP, Leng S, Kupinski MA, McCollough CH. *Correlation between a 2D channelized Hotelling observer and human observers in a low-contrast detection task with multislice reading in CT.* **Med Phys** 2017;44(8):3990–3999 | `10.1002/mp.12380` | **PMC5553707**(著者原稿。OA サブセット外なので機械取得は不可、ブラウザで閲覧可) |
| **CAND-03** | Ba A, Abbey CK, Racine D, Viry A, Verdun FR, Schmidt S, Bochud FO. *Channelized Hotelling observer correlation with human observers for low-contrast detection in liver CT images.* **J Med Imaging (Bellingham)** 2019;6(2):025501 | `10.1117/1.JMI.6.2.025501` | **PMC6527401** |

どちらも CT・CHO と人間観察者の対応という、第一次で採用した3件と同じ系譜。
**決め手は C5(性能指標)**:AUC・2AFC の percent correct・$d'$ のいずれかで報告されているか。

---

## 購読が要る(7件) — ここをチェックしていただく

| # | 文献 | DOI | PMID | 全文で確かめる一点 |
|---|---|---|---|---|
| **CAND-09** | Miró SP, Leung AN, Rubin GD, et al. *Digital storage phosphor chest radiography: an ROC study of the effect of 2K versus 4K matrix size on observer performance.* **Radiology** 2001;218(2):527–532 | `10.1148/radiology.218.2.r01fe26527` | 11161174 | **C2**:背景が臨床胸部X線。量子律速の背景としてモデルが記述できるか。ROC/AUC は報告されている見込み |
| **CAND-10** | Lams PM, Cocklin ML. *Spatial resolution requirements for digital chest radiographs: an ROC study of observer performance in selected cases.* **Radiology** 1986;158(1):11–19 | `10.1148/radiology.158.1.3940365` | 3940365 | **C2**:同上。18名の読影者・確信度 ROC |
| **V2-01** | Honey ID, Mackenzie A, Evans DS. *Investigation of optimum energies for chest imaging using film-screen and computed radiography.* **Br J Radiol** 2005;78(929):422–427 | `10.1259/bjr/32912696` | 15845936 | **C5**:CDRAD 由来の **visibility index** なら不可。AUC・2AFC PC・$d'$ の報告があるか |
| **V2-02** | Pascoal A, Lawinski CP, Honey I, Blake P. *Evaluation of a software package for automated quality assessment of contrast detail images — comparison with subjective visual assessment.* **Phys Med Biol** 2005;50(23):5743–5757 | `10.1088/0031-9155/50/23/023` | 16306665 | **C5 と C2**:主題がソフトと主観評価の一致。モデル入力の軸に沿った人間観察者性能の報告があるか |
| **V2-05** | Poels K, Depuydt T, Verellen D, et al. *Fiducial marker and marker-less soft-tissue detection using fast MV fluoroscopy on a new generation EPID.* **Med Phys** 2014;41(10):101911 | `10.1118/1.4896116` | 25281963 | **C1b/C5**:放射線治療の追尾・位置決めか、人間観察者の心理物理実験か。**非CT枠の候補** |
| **V2-06** | Xu J, Fuld MK, Fung GSK, Tsui BMW. *Task-based image quality evaluation of iterative reconstruction methods for low dose CT using computer simulations.* **Phys Med Biol** 2015;60(7):2881–2901 | `10.1088/0031-9155/60/7/2881` | 25776521 | **C2**:モデル観察者(CHO)のみか、**人間観察者の性能報告があるか**。無ければ H2 の検証には使えない |
| **V2-07** | Mobini Kesheh S, et al. *Characterization of two generations of digital detectors in a radiography system: technical image quality metrics, low-contrast detectability…* **Phys Med** 2025;138:105179 | `10.1016/j.ejmp.2025.105179` | 40974812 | **C5**:**visual grading analysis (VGA)** は順序尺度で許可指標外。低コントラスト検出能が AUC 等で報告されているか。**非CT枠の候補** |

---

## 判定の停止規則(事前登録で凍結済み。結果を見てから変えない)

第二次プールの要件は v2.1 §C のとおり:

| 要件 | 値 | 現状 |
|---|---|---|
| 採用研究数(継承分を含む) | **≥6** | 継承3(yu2013、paul2007、leng2013) |
| **うち第二次で新規に採用** | **≥3** | 0 |
| 合計条件点 | **≥60** | — |
| **非CT研究** | **≥2** | 0 |

**この下限は達成できないかもしれない。** v2.1 §C.2 は次のように凍結している:

> この下限は現実に達成できないかもしれず、**その場合は第二次が成立しなかったと報告することになる**。緩和ではない。

**したがって投稿は9件の採否に依存しない。** 判定が終われば、通っても通らなくても報告する内容が決まる。
満たせなかった場合に書くべきことは、v2 ラウンド2の記録に既にある——非CT枠が埋まらないのは
「そういう研究が存在しない」からではなく、**量子律速の背景を要求する C1 と、AUC/2AFC PC/$d'$ を
要求する C5 が、文献の系譜として重ならない**からである。これは Limitations に書く知見であり、
言い訳ではない。

---

## 取得後の手順

1. 取得順に C1–C6 を機械的に適用する。**予備所見は参照しない。**
2. 採否とその理由を `data/h2_studies_v2.json` に記録する(**落としたものも記録する**)。
3. 全件の判定完了をもってプールを閉じる(v2.0 §6.3)。
4. 結果に応じて本文 §5 と Limitations を書き、`tools/presubmission_check.py` を通す。

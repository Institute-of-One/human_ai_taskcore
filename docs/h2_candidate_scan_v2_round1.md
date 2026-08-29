# H2 系統調査 v2 — ラウンド1(既出未判定候補の書誌確定と入手)

**作成:** 2026-08-29
**準拠:** `docs/IORN-009A_H2_preregistration_v2.0.md`(凍結 2026-08-29、コミット `0afd87d`)§6.1
**本文書の性格:** 事前登録 §6.1 が求める「既出未判定候補の全件判定」の第一段。**書誌の確定・入手可否・全文が得られたものの判定**を記録する。全文が得られていない候補については**抄録レベルの予備所見のみ**を記す。予備所見は採否ではない。

書誌はすべて NCBI E-utilities(esummary/efetch)で確認した。v1 候補表の記述は不完全なものが多く、以下が確定版である。

---

## 書誌の確定

| ID | 確定した書誌 | 入手 |
|---|---|---|
| CAND-02 | Yu L, Chen B, Kofler JM, Favazza CP, Leng S, Kupinski MA, McCollough CH. **Correlation between a 2D channelized Hotelling observer and human observers in a low-contrast detection task with multislice reading in CT.** *Med Phys* 2017;44(8):3990–3999. doi:10.1002/mp.12380. PMID 28555878, PMC5553707(NIHMS 著者原稿) | **要取得**(PMC で無料閲覧可だが OA サブセット外) |
| CAND-03 | Ba A, Abbey CK, Racine D, Viry A, Verdun FR, Schmidt S, Bochud FO. **Channelized Hotelling observer correlation with human observers for low-contrast detection in liver CT images.** *J Med Imaging (Bellingham)* 2019;6(2):025501. doi:10.1117/1.JMI.6.2.025501. PMID 31131292, PMC6527401 | **要取得**(同上) |
| CAND-05 | Burgard CA, Gaass T, Bonert M, Bondesson D, Thaens N, et al. **Detection of artificial pulmonary lung nodules in ultralow-dose CT using an ex vivo lung phantom.** *PLoS One* 2018;13(1):e0190501. doi:10.1371/journal.pone.0190501. PMID 29298331, PMC5752031 | **取得済**(完全 OA、全文 XML) |
| CAND-06 | — | **解決不能**(下記) |
| CAND-09 | Miró SP, Leung AN, Rubin GD, Choi YH, Kee ST, Mindelzun RE, Stark P, Wexler L, Plevritis SK, Betts BJ. **Digital storage phosphor chest radiography: an ROC study of the effect of 2K versus 4K matrix size on observer performance.** *Radiology* 2001;218(2):527–532. doi:10.1148/radiology.218.2.r01fe26527. PMID 11161174 | **要取得**(購読) |
| CAND-10 | Lams PM, Cocklin ML. **Spatial resolution requirements for digital chest radiographs: an ROC study of observer performance in selected cases.** *Radiology* 1986;158(1):11–19. doi:10.1148/radiology.158.1.3940365. PMID 3940365 | **要取得**(購読) |

### CAND-06 は解決できない

v1 候補表(`docs/h2_candidate_scan_v1.md` §B)の記載は「320列CT低線量の肺結節検出能(Johns Hopkins)」のみで、**著者名・年・誌名・識別子のいずれも記録されていない。** PubMed を以下の検索語で照会したがいずれも該当しない。

- `320-detector CT nodule detection observer`(総数1件、内容不一致)
- `area detector CT lung nodule observer performance dose`(0件)
- `320-row CT dose reduction nodule`(総数1件、内容不一致)

**したがって CAND-06 は「特定できない候補」として記録し、判定不能とする。** 事前登録 §6.1 は全件判定を求めるが、同定できない記載を判定することはできない。この事実自体を記録することが、未判定のまま放置しないという要求への回答である。v1 の候補表に識別子のない記載を残したことが原因であり、v2 の新規検索(§6.2)では候補記載に必ず識別子を付す。

---

## 判定(全文が得られたもの)

### CAND-05 Burgard 2018 — **除外(C5)**

**落ちた基準:** C5(性能指標が AUC・2AFC の PC・$d'$ のいずれでもない)

**機械的根拠:** 全文(PLoS One、完全 OA)の本文において、性能は **5段階 Likert の確信度スコア**として報告されている。

> Nodule delineation was assessed by two observers (scores 1–5, 1 = unsure, 5 = high confidence).

> Differences in the score obtained for two different ULD protocols were tested for statistical significance using a Wilcoxon–matched–pairs test. To measure the interrater reliability between the scores of the two observers, Cohen's (weighted) Kappa was determined.

本文中に AUC・ROC 曲線・2AFC の PC・$d'$ の報告はない(`AUC` および `ROC` の出現は参考文献表題のみ)。**性能データは一切抽出していない。**

v1 候補表 §B は本候補について「感度のみならC5落ち」と予備判定していた。全文判定はこれを確認した。

---

## 予備所見(全文未取得、採否ではない)

以下は抄録本文のみに基づく。**採否は全文取得後に確定する。**

### CAND-02 Yu 2017(CT)

抄録より:低コントラスト球 18個(**6サイズ × 3コントラスト**)を含むファントムを、192列 CT で**5線量水準**(CTDIvol = 27, 13.5, 6.8, …)で撮像。2D 読影と multislice 読影の双方で人間観察者と CHO を比較。

- **C2 予備:** `lesion_size`・`contrast`・`dose` の3軸がいずれもモデルの宣言済み入力に対応する見込み。**軸数は十分**
- **C3 予備:** 条件点は 6×3×5 の部分集合と見られ、4点は優に超える見込み
- **C5:** 指標は抄録の切れた位置にあり未確認。同一グループの yu2013 は 2AFC PC
- **`background_class` 予備:** 均一ファントム → `uniform_or_phantom` の見込み
- **留意:** multislice 読影は本モデルに対応項がない。2D 読影の腕が使用可能な部分になる可能性が高く、その場合は `task_congruence` と併せて記録する

### CAND-03 Ba 2019(CT)

抄録より:背景種別(**均一 vs 肝**)と読影様式(単一 vs multislice)が人間・モデル観察者の検出성能に与える影響を評価。

- **C2 予備:** 背景種別はモデルに対応項がない(解剖学的雑音の項を持たない)ため、v1.2 の規則により**検証軸として数えられない**。他に線量・病変サイズ・コントラストの軸があるかは全文で確認を要する
- **v2.0 §4 との関係:** 本研究は**一つの研究の中に均一背景と解剖学的背景の双方を持つ**。採用されれば、`background_class` の層比較を観察者とタスクを揃えたまま研究内で行えることになり、研究間の層別より強い。ただし**これは採否の理由にならない**(採否は C1–C6 のみで決まる)

### CAND-09 Miró 2001(胸部X線)

抄録より:2K(1760×2140)と 4K(3520×4280)のマトリクスサイズを比較。160名の患者、6名の読影者、5段階確信度、ROC 解析。

- **C5 予備:** ROC → AUC の見込みで通過
- **C2 予備:** 有効軸は `displayed_matrix` の**1軸のみ**と見られる。異常の種別(実質・縦隔・胸膜)はモデルの宣言済み入力ではない。**C2 で落ちる公算が高い**(CAND-07 と同じ理由)
- **`background_class` 予備:** 実患者胸部X線 → `anatomic`

### CAND-10 Lams 1986(胸部X線)

抄録より:38枚の臨床X線を **画素サイズ 1.6 / 0.8 / 0.4 / 0.2 mm** で表示、18名の読影者、確信度から ROC 曲線を生成。

- **C5 予備:** ROC → 通過の見込み
- **C3 予備:** 画素サイズ4水準 → 4点で境界上
- **C2 予備:** 有効軸は `pixel_size` の**1軸のみ**と見られる。病変種別(孤立結節 vs 隔壁線)はタスク関数そのものの違いであり、モデルの宣言済み入力の軸ではない。**C2 で落ちる公算が高い**
- **`background_class` 予備:** 臨床X線 → `anatomic`

---

## この段階での見通し(記録)

予備所見が当たった場合、非CT枠(CAND-09、-10)は再び C2 で落ちる。**その場合、事前登録 §3 の非CT要件は §6.2 の新規検索に懸かる。** 新規検索は量子律速の背景を持つ非CT研究を明示的に狙う設計になっており(検索語は事前登録済み)、臨床画像を背景とする研究を探し続けても同じ壁に当たることは v1 で確認済みである。

**予備所見は採否ではない。** 全文取得後、C1–C6 を機械的に適用して `data/h2_studies_v2.json` に記録する。

---

## 次のアクション

1. **要取得4件**(CAND-02、-03、-09、-10)の PDF。CAND-02・-03 は PMC で無料閲覧可、CAND-09・-10 は購読誌
2. 取得順に全文判定 → `data/h2_studies_v2.json` へ採否とも記録
3. 事前登録 §6.2 の新規系統検索(検索語は凍結済み)
4. 全候補の判定完了をもってプールを閉じる

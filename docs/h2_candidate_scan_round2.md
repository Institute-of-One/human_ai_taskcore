# H2 系統調査 — ラウンド2(非CT枠・v1.2 原則語彙による補充検索)

**作成:** 2026-08-24(Cowork セッション)
**根拠:** 事前登録 v1.2 C2(条件軸=モデル宣言済み入力)確定後の補充検索。CAND-07/-08 の除外により非CT枠が空になったため、検索ラウンド2を実施(候補表 v1 §次のアクション、および v1.1 改訂の閲覧済みリスト運用に準拠)。**性能データの抽出は一切行っていない**(タイトル・抄録レベルのみ)。
**検索語(記録):** "dose reduction image processing chest radiography ROC observer performance nodule detection" / "computed radiography chest phantom nodule detection ROC Az exposure levels nodule size"

## 追加候補(スクリーニング待ち)

| ID | 文献 | 条件軸(把握分・v1.2語彙) | 指標 | 予備判定 | 優先度 |
|---|---|---|---|---|---|
| CAND-15 | Detection of simulated lung nodules with computed radiography: Effects of nodule size, local optical density, global object thickness, and exposure. *Acad Radiol* 1996(ScienceDirect S1076633296804120) | **nodule size × exposure(+局所濃度・体厚)= 2軸以上確実** | ROC系(要確認) | C1○ C2○ C3○(4軸グリッドなら点数十分) C5△ C6△ | **最高** |
| CAND-16 | Kroft LJ, Veldkamp WJ, et al. Detection of Simulated Nodules on Clinical Radiographs: Dose Reduction at Digital PA Chest Radiography. *Radiology* 2006;241:392–398 | dose(100/50/25/12%)× nodule size/intensity | **検出確率(ロジスティック回帰)— C5 リスク大**(AUC/PC/d′ でない) | C1○ C2○ C3○ C5**×懸念** | 中(C5次第) |
| CAND-17 | Effects of reduced exposure on computed radiography: comparison of nodule detection accuracy with conventional and asymmetric screen-film radiographs of a chest phantom. *AJR* 1995(PMID 7618538) | exposure × 検出系/処理(+nodule条件は要確認) | ROC(要確認) | C1○ C2△ C3△ C5△ | 高 |
| CAND-18 | Samei E, Flynn MJ, Eyler WR. 胸部X線の量子雑音/解剖学的雑音と微小結節検出(Radiology 1999;213:727 系)| nodule contrast × size(+雑音源) | PC系(要確認) | C1○ C2○ C3△ C5△ | 高 |

## 判定メモ

- CAND-16 は Kroft 抄録確認済み:"The decrease in radiation dose from 100% to 50%, 25%, or 12% had no effect on lesion detection in the lungs"(肺野では線量低減の影響なし)— 内容的には本枠組みの飽和予測と強く響き合うが、指標がロジスティック回帰の検出確率のため **C5 で落ちる公算大**。落ちる場合も Discussion の傍証として引用価値あり(除外記録に明記)。
- CAND-15 が本命:4条件軸はすべて v1.2 語彙(lesion_size / contrast(光学濃度経由)/ 体厚(散乱・雑音)/ dose)に対応し得る。PDF 最優先取得。
- PubMed/PMC/ScienceDirect が bot 対策で断続不通のため、書誌細部は PDF 取得時に確定。

## 全文判定(2026-08-24、PDF 到着後)

| ID | 判定 | 落ちた基準 | 理由(機械的) |
|---|---|---|---|
| CAND-15 | **除外** | C5 | 表2/3は TPF、表4は FPF。著者は複数結節のため ROC を避けた(p.739)。許可指標外。 |
| CAND-17 | **除外** | C2 | 4受容体×線量。dose は可。受容体種は宣言済み入力に無い(`processing` ≠ 検出器クラス)。有効軸1。 |

CAND-16・CAND-18 は未判定のまま。

## 次のアクション

1. CAND-16 の PDF(C5 が検出確率なら除外、除外記録に Discussion 傍証と残す)と CAND-18 の書誌確定
2. ラウンド2が全滅した場合のみ、事前登録 §2 の規定により汎用性主張を CT 限定へ縮退

## 全文判定・第2回(2026-08-27)

| ID | 判定 | 落ちた基準 | 根拠 |
|---|---|---|---|
| CAND-16 Kroft 2006 | **除外** | C5 | 抄録が設計と解析を明示: 各病変を detected / not detected で採点し、semiparametric logistic regression で解析。報告される図はロジスティック回帰の検出確率であって AUC・2AFC の PC・$d'$ ではない。性能値は一切抽出していない。**Discussion の傍証としては残す** — 100%→12% の線量低減が肺野の検出に影響しなかったという結果は、本枠組みの飽和予測と同方向であり、検証には使えないが言及に値する。 |
| CAND-18 Samei 1999 | **C1・C5 通過、C2/C3/C6 未判定** | — | Radiology 1999;213(3):727-734, doi:10.1148/radiology.213.3.r99dc19727, PMID 10580946。抄録に "The area under the receiver operating characteristic curve (Az) was estimated as a measure of the detectability" とあり **C5 は Az = AUC で通過**。C1 は胸部X線で通過。 |

### CAND-18 が非CT枠の唯一の生存候補である

ラウンド1(CAND-07/-08)とラウンド2(CAND-15/-16/-17)が全て凍結基準で落ちたため、**非CT枠の可否は CAND-18 一件に懸かっている**。

**抄録では決まらないもの(本文が要る):**

1. **C2(条件軸 ≥2、いずれも v1.2 の宣言済み入力語彙)** — 抄録は "various peak contrast-diameter products (CD)" と書く。CD が contrast と diameter を**一つの積に畳んだ1軸**なのか、両者が**独立に振られた2軸**なのかで判定が変わる。第2軸の候補は背景種(quantum mottle 画像 vs 解剖パターン画像)だが、これが宣言済み入力のどれに対応するか(雑音項のどの成分か)を本文の設定から決める必要がある。**対応が付かなければ C2 で落ちる。**
2. **C3(条件点 ≥4)** — Az が何水準の CD で報告されているか。
3. **C6(図から ±5% で digitize 可能)** — 独立2回 digitize の最大偏差。

**やってはいけないこと:** 抄録から C2 を推定すること。CD の扱いも背景種の対応も、本文の設定に書かれている事実であって、読まずに決めれば判定ではなく作文になる。

### 次のアクション

1. Samei 1999 の PDF を取得し、C2 → C3 → C6 の順に機械適用する
2. 通過すれば非CT枠が埋まり、H2 のプールが完成する(3研究 → 4研究、条件点 57+)
3. 落ちれば**ラウンド2は全滅**であり、事前登録 v1.0 §プール要件の規定により、汎用性の主張を CT 限定へ縮退させる。縮退は事前に宣言された措置であって、結果を見てからの判断ではない

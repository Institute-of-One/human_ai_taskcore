---
title: "IORN-009A 研究計画書 v0.4 — Physics-to-Perception Framework"
date: "2026-08-23"
geometry: margin=1in
fontsize: 10.5pt
papersize: a4
---

# IORN-009A 研究計画書 v0.4

**プロジェクト:** Institute of One Research Note 009A(LISIT Co., Ltd. オープンリサーチ)
**作成日:** 2026-08-22 | **最終改訂:** 2026-08-23 | **ステータス:** M2完了(Phase 1 完走)
**先行プロジェクト:** IORN-002(radiomics-phantom, *J. Imaging* 2026, 12, 392)
**v0.1→v0.2 変更点:** §3「先行研究ベンチマーク — シカゴ土井グループ」新設、§2にU-HRCT問題意識と歴史的教訓を追加、Phase 1にU-HRCTケーススタディ追加、リスク登録簿2項目追加。
**v0.2→v0.3 変更点(スコープ確定):** 「汎用理論+CT主戦」に決定 — 理論をモダリティ非依存に定式化し(§2.1 適用範囲)、CTを主実証・U-HRCTを旗艦ケースに据え、外部検証プールへ胸部X線observer研究を追加(§8)。表題を medical imaging 系に変更、リスク登録簿#9追加。

**v0.3→v0.4 変更点(定式化確定 — M2 の実装で判明した事実に基づく):**

1. **§5.2 の主形式を変更。** v0.3 は CSF² を被積分関数の**分子**に置いていたが、この形では量子雑音律速の FBP チェーン($N_{\mathrm{image}} \propto f\,|\mathrm{TTF}|^2$、$H_{\mathrm{scanner}} = \mathrm{TTF}$)において伝達関数が分子分母で**厳密に約分**され、再構成カーネル・表示MTF・眼球MTFのいずれも $d'$ に影響しなくなることが実装により判明した(機械精度で確認、§7 検証項目)。Barten の CSF はもともと「内部雑音 → 閾値」から導かれているため、CSF を**分母($N_{\mathrm{effective}}$ の神経内部雑音項)**に置く定式化が理論的に一貫する。よって**神経内部雑音形式を主形式に採用**し、v0.3 の重み形式は「可逆フィルタ不変性が成立する理想極限」として付録に温存する。
2. **§5.1 の $N_{\mathrm{internal}}$ を三分割に確定。** 画像雑音・表示量子化雑音・神経内部雑音を、それぞれ**物理的に注入される場所**に置く(順に、表示+眼球MTFの両方を通る/眼球MTFのみを通る/どのMTFも通らない)。信号と同じ因子をすべて共有する項は比の中で消えるため、床項を $|H_{\mathrm{display}}|^2$ の外に置くことが、画素ピッチ・拡大率が検出能に効く唯一の経路である。
3. **H3 を書き換え(§4)。** v0.3 の「拡大率を上げるに従い単調に回復する」は $f_{\mathrm{sat}}$ については成立するが、$d'$ については**漸近飽和**であり内点最適は現れない(主形式での実測、§4 参照)。低角周波数では Barten の神経雑音項が $1/u^2$ で増大し、物体参照への換算因子 $a^2$ と相殺するため、**物体参照の神経雑音床が拡大率に依存しなくなる**ことが理由である。H3 は「$f_{\mathrm{sat}}$ の回復」と「**十分拡大率** $Z^{*}$ の同定」の形に改める。
4. **§7 に視距離感度を追加**(拡大率マップを $(Z, D)$ 2次元に拡張)。$a = D\tan(1^\circ)/M$ が拡大率と視距離の両方に依存するため、両者は独立な設計変数ではない — マップで同時に扱う。
5. **リスク登録簿に #10(CSF の置き場所)・#11(絶対 $d'$ の未校正)を追加。**

---

## 1. 表題候補(英語)

主候補(スコープ決定を反映しmedical imaging系に変更):

> **A physics-to-perception framework identifies unused spatial-frequency information in task-based medical imaging**

代替案(主張をさらに抑える場合):

> Where imaging resolution exceeds perception: a closed-form acquisition–display–visual-system model of task-based imaging with external validation against published human-observer studies

U-HRCT応用を前面に出す場合(ケーススタディの結果次第):

> Does ultra-high-resolution CT information reach the human observer? A physics-to-perception analysis of the imaging–display–vision chain

009B接続を見せる場合(009Aでは使わない):

> Human and AI observers use different spatial-frequency information in low-dose CT: a physics-to-perception simulation study

## 2. 背景と位置づけ

### 2.1 学術的系譜 — Final MTF から Final Information Transfer へ

古典的な「Final MTF」研究は、撮像系→表示系→人間視覚系の直列伝達特性として画像チェーンの終端解像特性を問うた。IORN-009はこれを現代化する。009Aでは Human branch の閉形式統合(scanner–display–visual system)を完成させて「装置が生成した情報のうち、人間視覚系に物理的に届き得る帯域」を定量化し、009Bで AI branch(Task-conditioned AI spectral utilization)を新設して Human–AI spectral utilization gap を扱う。全体構想は「Final MTF の、Human–AI 共同読影時代における **Final Information Transfer** への拡張」である。

**適用範囲(明示的境界):** 本枠組みは「MTF/NPS で特性化可能な線形近似系+標準化された表示経路」を持つX線系デジタルイメージング全般(CT、一般X線撮影 CR/DR、マンモグラフィ、トモシンセシス)にモダリティ非依存で適用できる形で定式化する。実証(Phase 1・ケーススタディ)は CT を主戦場とし、汎用性は §8 の外部検証プールに胸部X線observer研究を含めることで**主張でなく検証**として担保する。MRI(k空間取得・非定常雑音)・超音波(スペックル・非線形)は明示的に適用外とし、Discussionで拡張条件のみ述べる。この境界設定により「CTだけの話題」への矮小化と、各モダリティ特殊事情の無限要求の両方を防ぐ。

### 2.2 現代的動機 — 超高精細CT(U-HRCT)ブームへの理論的検証

日本主導で開発された超高精細CT(検出器素子 0.25 mm、面内 1024–2048 マトリクス)は、物理解像度で従来機の約2倍を達成した。プロトタイプ評価論文(Kakinuma et al., *PLOS ONE* 2015)は次のように結論した:

> "Despite a larger image noise, the prototype U-HRCT scanner had a significantly better image quality than the C-HRCT scanners."
> (画像ノイズは増えたにもかかわらず、U-HRCT試作機の画質は従来HRCTより有意に優れていた)

ただしこの「画質」は10名の放射線科医による **5段階視覚評点**("graded using a 5-point score")であり、タスクベースの検出性能でも、表示系・視覚系を含む情報伝達解析でもない。同研究の読影条件は9MPモニタ・表示FOV 80 mm(強拡大)という、臨床のルーチン表示とはかけ離れた条件であったことも記録されている。**「解像度が上がった」ことと「その情報が標準的読影条件下で人間観察者に届き利用される」ことの間には、表示系(画素ピッチ・GSDF階調・拡大率)と視覚系(眼球MTF・CSF・内部ノイズ)という物理的に規定可能な減衰段が挟まっている。** この減衰段を通過できる帯域を定量化した研究は、U-HRCT評価文献にほぼ存在しない — これが本研究の空隙である。

主張の形は慎重に設計する。本研究は「高解像度は無意味」とは主張しない。「指定した表示・視覚条件の下では周波数 $f_{\mathrm{sat}}$ 以上の情報は人間観察者に利用されにくい」「利用させたければ拡大率・画素ピッチ・階調をこう設計すべき」という**条件付き・建設的・反証可能**な形で提示する(拡大読影で救済される帯域も同じ式で定量化できる)。

### 2.3 歴史的教訓 — マルチスライスCT導入期の再来を避ける

4列MSCT導入期(1998–2002年頃)には、幾何学的線量効率の低下(overbeaming)により4列機の被ばく効率はむしろ単列機より悪化し得たことが物理評価で示されており(ICRP Publication 87 ほか、執筆時に一次文献の引用文を確定する)、宣伝上の期待と物理的実態が乖離した時期があった。解像度・列数・速度という「増えた数字」が患者利益に変換される保証はなく、変換されるか否かは物理チェーン全体の解析によってのみ判定できる — 本研究はU-HRCT時代におけるその解析を提供する。

### 2.4 IORN-002との関係

決定論的デジタルファントム、画像領域取得シミュレータ、results.json駆動の数値再現、テスト文化をそのまま転用する。ファントムは肺野テクスチャ(1/f^β型パワースペクトル)+結節挿入に拡張する。

### 2.5 Original Research成立戦略(本計画の要)

読影医を新規に集めない代わりに、(i) 反証可能な定量仮説、(ii) **既報の人間observer実験データによる外部検証を同一論文内に内蔵**、(iii) 視覚モデル不確実性の明示的伝播、の3点でTechnical Note判定を構造的に回避する。主張は「診断できる」ではなく「指定した標準表示条件と既報視覚モデルの下では、この周波数以上の情報は人間観察者に利用されにくいと予測される」に限定する。

## 3. 先行研究ベンチマーク — シカゴ土井グループを確実に超えるために

本研究が超えるべき基準線は、シカゴ大学 Kurt Rossmann Laboratories for Radiologic Image Research(Rossmann–Metz–Doi の系譜)である。同研究室は1967年設立、"the improvement of diagnostic accuracy of radiologic imaging and minimization of patients' exposure"(放射線画像の診断精度向上と患者被ばくの最小化)を一貫した主題とし、医用画像科学の三本柱を確立した。

### 3.1 土井グループが確立した三本柱(引用つき)

**柱1 — 物理画質の連鎖解析(Rossmann)。** Rossmann は PSF/LSF/MTF を放射線画像評価の標準言語にした古典論文(*Radiology* 1969;93:257–272)で、解析対象を装置単体ではなく

> "the entire radiological process involving exposing, imaging, and visual detection operations"
> (曝射・画像化・視覚検出の各操作を含む放射線学的プロセス全体)

と明示した。つまり**チェーン終端に視覚検出を置く構想(Final MTF)は1969年時点で提示されている**。ただし当時それは記述的なMTF縦続(カスケード)であり、タスク・雑音・認知効率を含む情報量としての閉形式統合には至っていない。

**柱2 — 観察者性能の測定方法論(Metz)。** Metz の "Basic principles of ROC analysis"(*Semin Nucl Med* 1978;8:283–298)は、診断性能を感度・特異度のトレードオフ曲線として測定する枠組みを確立し、ROC解析が "related in a direct and natural way to cost/benefit analysis of diagnostic decision making"(診断意思決定の費用便益解析へ直接かつ自然につながる)ことを示した。これは**測定の方法論**であり、物理条件から観察者性能を**予測する**理論ではない。

**柱3 — 計算機支援診断(Doi)。** Doi の総説(*Comput Med Imaging Graph* 2007;31:198–211)によれば、

> "Large-scale and systematic research and development of various CAD schemes were begun in the early 1980s at the Kurt Rossmann Laboratories for Radiologic Image Research."
> (各種CADスキームの大規模かつ体系的な研究開発は、1980年代初頭にKurt Rossmann研究室で開始された)

そしてCADの定義は

> "With CAD, radiologists use the computer output as a 'second opinion' and make the final decisions."
> (CADでは、放射線科医は計算機出力を「セカンドオピニオン」として用い、最終判断を下す)

である。すなわち**計算機は人間と同じ画像を見て人間を補助する存在**として概念化されており、「計算機と人間が画像内の異なる空間周波数帯域を利用している」という情報論的な問いは立てられていない。

### 3.2 本研究の超越点(N1–N5)

| # | 土井グループの到達点 | IORN-009 が加えるもの |
|---|---|---|
| N1 | チェーン構想は提示(柱1)だが記述的MTF縦続 | **閉形式のタスク重み付き情報積分** $d'^2_{\mathrm{human}}$:scanner→display→eye→cognition を単一の反証可能な式に統合し、$f_{\mathrm{sat}}$・$G_{\mathrm{useful}}$ という新指標を定義 |
| N2 | 表示・視覚段は当時の CRT/フィルム経験則 | **現代標準への係留**:DICOM GSDF (PS3.14) 固定表示モデル+Barten CSF+眼球MTF。恣意パラメータは $\eta_{\mathrm{cog}}$ 等の範囲パラメータのみで、結果は不確実性帯として提示(点推定を主張しない) |
| N3 | 観察者性能は新規読影実験で測る(柱2の運用) | **外部検証の内蔵化**:新規読影実験ゼロで、既報observer研究のdigitizeデータに対する事前登録付き順位相関検証(H2)を同一論文内に組込む — 検証の再現性が読影者募集に依存しない |
| N4 | 計算機=人間の "second opinion"(柱3) | **Human–AI spectral utilization gap**(009B):AIを独立の情報消費者と捉え、band-stop介入で $S_{AI}(f)$ を因果的に測定、$I_{\mathrm{shared}}/I_{\mathrm{AI-only}}/I_{\mathrm{Human-only}}$ を定義 — 土井時代には存在し得なかった問い |
| N5 | 解析コードと数値は原則非公開の時代 | **決定論的完全再現**(IORN-002方式):全数値がseed固定スクリプトで再生成、独立実装クロスチェックをCIで常時実行 |

**戦術ノート:** Medical Physics の査読者層にはシカゴ学派の系譜が濃い。位置づけは「打倒」ではなく**「Rossmann が1969年に宣言したプログラム("the entire radiological process")の、現代標準と情報理論による完成」**として提示する。これは礼儀であると同時に、最も強い主張の形でもある — 彼らの枠組みでは立てられなかった問い(N1, N4)を立てていることが節内で自明になるからである。

さらに v0.3 のスコープ決定がこの位置づけを実体化する:土井グループの主戦場は**胸部X線写真**であり、外部検証プール(§8)に胸部X線observer研究を含めることで、「シカゴ学派が築いたobserver性能データの伝統そのものに対して本枠組みの予測力を検証する」という構図になる。系譜の継承が、序論の修辞ではなく**検証データのレベル**で示される。

## 4. 研究質問と仮説

**RQ:** 撮像装置(主対象:CT)の物理解像度・線量の向上は、どの条件・どの空間周波数から先、人間観察者のタスク性能に寄与しなくなるか。

**H1(飽和仮説・主仮説):** 標準表示条件および既報視覚モデルの下で、知覚重み付きタスク検出能 $d'_{\mathrm{human}}$ は撮像系解像度(および線量)に対して飽和し、飽和点を与える知覚利用上限周波数 $f_{\mathrm{sat}}$ が存在する。
*棄却基準:* 全条件で $G_{\mathrm{useful}} = \Delta d'_{\mathrm{human}} / \Delta D$ が実用範囲内で単調に有意に正であり続ければH1は棄却。

*「有意に正」の操作的定義(M3 の不確実性伝播で確定):* §5.4 の範囲パラメータ($\kappa$、$\eta_{\mathrm{cog}}$ を主、視距離・輝度を副)を伝播して得た $G_{\mathrm{useful}}$ の**95%帯の下限が線量上端まで正**であることを「有意に正」と定義する。逆に、帯の下限が線量範囲内でゼロを跨げばその条件は飽和と判定する。判定は条件ごとに行い、飽和条件の割合を主結果として報告する(点推定の単調性だけでは判定しない)。

**H2(外部妥当性仮説):** 本統合モデルの予測は、既報の人間observer実験(条件別AUC・正答率・$d'$)の**条件間順位**を有意に再現する。
*成功基準(事前設定):* 研究内の条件順位に対する Spearman ρ ≥ 0.7(各研究)、および全研究プールでの予測–実測の単調校正。達しない場合は不一致条件を明示的に報告する(選択的報告をしない)。

**H3(U-HRCT応用仮説・ケーススタディ / v0.4改訂):** U-HRCT級の撮像系MTF(公表TTF/MTF値で規定)が従来機に対して付加する高周波帯域の $d'^2_{\mathrm{human}}$ への寄与は、標準表示条件(ルーチン表示FOV・GSDF較正モニタ)では小さい。表示拡大率 $Z$ と視距離 $D$ を通じて $f_{\mathrm{sat}}$ は単調に回復するが、$d'_{\mathrm{human}}$ は**漸近的に飽和**し、内点最適は持たない。したがって設計量は「最適拡大率」ではなく**十分拡大率** $Z^{*}$(漸近値の95%に達する $Z$)である。

*根拠(v0.4 で追加):* 主形式では低角周波数で神経雑音密度が $\Phi(u) \propto 1/u^2$ となり、物体参照への換算因子 $a^2 = (D\tan 1^\circ / M)^2$ と相殺する。すなわち $N_{\mathrm{neural}}$ は $u \ll u_0$ で拡大率に依存しない床に漸近し、拡大では超えられない。

拡大率掃引(§7.1 のグリッドとは別の補助掃引:径 3水準 × コントラスト 2水準 × カーネル 3水準 = **18条件**、線量 1×・スライス厚 1 mm・視距離 500 mm・再構成画素 0.39 mm に固定、$Z = 1$–$16$ の9点)での実測は、$Z: 1 \to 16$ に対し

- $d'_{\mathrm{human}}$ 比 = **中央値 1.047(範囲 1.037–1.065)**
- $f_{\mathrm{sat}}$ 比 = **中央値 1.078(範囲 1.041–1.441)**
- $Z^{*}$(漸近値の95%)= **中央値 1.0(範囲 1.0–1.5)**

すなわちこの画素サイズでは 1:1 表示でほぼ漸近値に達しており、利得は $Z \lesssim 1.5$ で尽きる。M3 で $(Z, D)$ マップとして results.json 化し、U-HRCT級の細かい画素で $Z^{*} > 1$ となるかを検証する。

*棄却基準:* $d'_{\mathrm{human}}(Z)$ が検討範囲内で内点最大を持つ、または $Z^{*}$ が画素ピッチ・視距離から予測される値と系統的にずれる場合、$H_3$ の定式化を棄却する。

*提示形:* 「付加帯域の寄与率」を $(Z, D)$ 平面上の等高線マップとして示し、$Z^{*}$ の等値線を重ねる。**高解像度情報を人間に届けるための表示条件の設計指針**として建設的に提示する。U-HRCT級の細かい画素では 1:1 表示が $Z^{*}$ を下回る(=情報が届いていない)ことが予測であり、これが検証対象である。

## 5. 理論枠組み

### 5.1 有効伝達系と有効雑音(v0.4)

$$H_{\mathrm{effective}}(f) = H_{\mathrm{scanner}}(f)\, H_{\mathrm{display}}(f)\, H_{\mathrm{eye}}(f)$$

$$N_{\mathrm{effective}}(f) = \underbrace{N_{\mathrm{image}}(f)\,|H_{\mathrm{display}}H_{\mathrm{eye}}|^2}_{\text{撮像系}} + \underbrace{N_{\mathrm{quant}}\,|H_{\mathrm{eye}}|^2}_{\text{表示量子化}} + \underbrace{N_{\mathrm{neural}}(f)}_{\text{神経内部}}$$

**三項を注入位置で分ける**のが v0.4 の確定事項である。画像雑音は撮像段で生じるので表示MTFと眼球MTFの両方を通り、表示量子化雑音は表示段で生じるので眼球MTFのみを通り、神経内部雑音はどの伝達関数も通らない。信号と完全に同じ因子を持つ雑音項は $|W H_{\mathrm{eff}}|^2 / N_{\mathrm{eff}}$ の比の中で消える(§7 の不変性検証)ため、**床項を $|H_{\mathrm{display}}|^2$ の外に置くことが、画素ピッチ・拡大率・視距離が検出能に効く唯一の経路である。**

各項の具体形:

- $N_{\mathrm{image}}(f) = c\, f\,|H_{\mathrm{scanner}}(f)|^2$、$c \propto 1/(\text{線量} \times \text{スライス厚})$。ランプ因子は2次元FBPの標準結果、$|H_{\mathrm{scanner}}|^2$ は投影の量子雑音が信号と同じ開口・カーネルを通ることによる。$\int N_{\mathrm{image}}\,d^2 f$ が画素分散に一致するよう正規化する。
- $N_{\mathrm{quant}} = (\mathrm{WW}/n_{\mathrm{grey}})^2/12 \times (\Delta_{\mathrm{obj}}/Z)^2$(一様量子化器の分散 × 表示画素が物体で覆う面積)。DICOM GSDF の階調数とビット深度で決まり、恣意性がない。
- $N_{\mathrm{neural}}(f) = \kappa^2 (\mathrm{WW}\, a)^2\, \Phi(a f)$、$a = D\tan(1^\circ)/M$ [mm/deg]、$\Phi(u)$ は Barten の光子雑音+側方抑制成形された神経雑音を時間積分時間で割った空間雑音密度。$\Phi(u) = A_{\mathrm{int}}(u)/(2k^2 S_{\mathrm{neural}}^2(u))$ が厳密に成立する — すなわち**この雑音項と CSF は同一モデルの二つの表現**である(実装で機械精度により検証)。HU→変調度の換算はウィンドウ幅 WW を全変調度域とする規約による。$\kappa$ は無次元の範囲パラメータで、$\kappa = 1$ が「Barten標準観察者そのまま」。

認知段は伝達関数ではなく効率パラメータとして分離する(5.3)。

### 5.2 知覚検出能と派生指標(v0.4 主形式)

タスク関数 $W_{\mathrm{task}}(f)$(小結節検出:サイズ・コントラストで規定)に対し、2次元等方形で

$$d'^{2}_{\mathrm{human}} = \eta_{\mathrm{cog}} \int \frac{|W_{\mathrm{task}}(f)|^2\, |H_{\mathrm{effective}}(f)|^2}{N_{\mathrm{effective}}(f)}\, 2\pi f\, df$$

**視覚系の感度は分子の重みではなく $N_{\mathrm{effective}}$ の $N_{\mathrm{neural}}$ 項として入る。** これが v0.3 からの最重要変更点である(理由は冒頭の変更履歴 1)。

*付録形式(v0.3 の重み形式・理想極限):* $\mathrm{CSF}^2$ を分子に置いた
$$d'^{2}_{\mathrm{weight}} = \eta_{\mathrm{cog}} \int \frac{|W_{\mathrm{task}}|^2\,|H_{\mathrm{effective}}|^2\,\widehat{\mathrm{CSF}}^2}{N_{\mathrm{effective}}}\, 2\pi f\, df,\qquad \widehat{\mathrm{CSF}} = \mathrm{CSF}_{\mathrm{neural}}/\max \mathrm{CSF}_{\mathrm{neural}}$$
は、床項を落とした極限で**任意の可逆線形フィルタに対して不変**になる。この不変性は理論的健全性の検証量として全条件で報告する(§7)。$\widehat{\mathrm{CSF}}$ をピーク正規化するのは、絶対感度スケールを $\eta_{\mathrm{cog}}$ に吸収させ $R_{\mathrm{perceptual}} \le \sqrt{\eta_{\mathrm{cog}}}$ を保証するためである。

派生指標:

- 知覚利用率 $R_{\mathrm{perceptual}} = d'_{\mathrm{human}} / d'_{\mathrm{ideal}}$(idealは表示・視覚段を単位系に置き床項を除いた prewhitening observer)。主形式では $R_{\mathrm{perceptual}} \le \sqrt{\eta_{\mathrm{cog}}}$ が解析的に成立する
- 線量あたり知覚情報利得 $G_{\mathrm{useful}} = \Delta d'_{\mathrm{human}} / \Delta D$
- 知覚利用上限周波数 $f_{\mathrm{sat}}$: 被積分関数(周波数別寄与密度、2次元測度 $2\pi f\,df$ を含む)の累積が全積分の95%に達する周波数、と定義(閾値95%は感度分析で90/99%も併記)
- **十分拡大率 $Z^{*}$**(v0.4 追加): $d'_{\mathrm{human}}(Z)$ が $Z\to\infty$ 漸近値の95%に達する最小の $Z$。H3 の設計量

### 5.3 構成要素のソースと扱い

| 要素 | ソース | 扱い |
|---|---|---|
| $H_{\mathrm{scanner}}, N_{\mathrm{image}}$ | IORN-002取得シミュレータのTTF/NPS(+文献実測値での妥当性確認。U-HRCTケーススタディでは公表TTF/MTF・NPSを使用) | 実験変数 |
| $H_{\mathrm{display}}$ | **DICOM GSDF (PS3.14)** + 画素ピッチ + 視距離・拡大率の幾何 | 標準規格に固定(恣意性排除) |
| $N_{\mathrm{quant}}$ | GSDF階調数・ビット深度・ウィンドウ幅・拡大率 | 標準規格に固定 |
| $H_{\mathrm{eye}}$ | 既報の眼球光学系MTF(瞳孔径依存) | 文献モデル固定 |
| $N_{\mathrm{neural}}(f)$ | Barten の光子雑音+神経雑音密度 $\Phi(u)$(輝度・視角依存)。CSF と同一モデル | 文献モデル固定+無次元スケール $\kappa$ を**範囲パラメータ** |
| $\widehat{\mathrm{CSF}}(f)$ | Barten型CSF(付録形式・observerモデルの視覚フィルタとしてのみ使用) | 文献モデル固定 |
| $\eta_{\mathrm{cog}}$ | 文献レンジ $[\eta_{\min}, \eta_{\max}]$ | **範囲パラメータ(点推定しない)** |

### 5.4 不確実性の伝播(主結果の単位)

$\eta_{\mathrm{cog}}$、神経内部雑音スケール $\kappa$、視距離 $D$、拡大率 $Z$、輝度の文献範囲をモンテカルロ(またはグリッド)伝播し、$f_{\mathrm{sat}}$・$G_{\mathrm{useful}}$・$Z^{*}$ を**「文献で支持された人間知覚限界の不確実性帯(95%帯)」**として提示する。単一のHuman Ceiling点推定は主張しない。IORN-002で確立した「点推定でなく区間を主役にする」方針を踏襲。

$\kappa$ は主形式では $f_{\mathrm{sat}}$ を直接左右する支配パラメータであるため、伝播の中心に置く($\kappa=1$ を基準、範囲は文献の内部雑音推定から設定し、Methods に根拠を明記)。

## 6. 実装計画

**リポジトリ:** `human_ai_taskcore`(パッケージ名 `ptx`)。IORN-002の設計原則を継承: 純Python(numpy/scipy)、全段seed付き決定論、`paper/make_figures.py`型のresults.json駆動、独立実装+文献値とのクロスチェックをCIに組込み。

モジュール構成(M2 時点の実装状況を反映):

- `ptx/phantom_lung.py`(実装済) — HU校正済み異方性1/f^β肺野テクスチャ、Murray則の血管樹、部分体積付き球結節、解析的タスク関数 $W_{\mathrm{task}}$(ディスクのFourier変換 × 球の部分体積係数)
- `ptx/chain.py`(実装済) — CT TTF/NPS 取得段、GSDF表示モデル・表示画素MTF、眼球MTF、Barten CSF と神経雑音密度 $\Phi(u)$、視距離・拡大率の幾何、$H_{\mathrm{eff}}/N_{\mathrm{eff}}$ 組立て(各々文献式から独立実装、文献の数表・解析極限と照合するテスト付き)
- `ptx/observer.py`(実装済) — NPWE および channelized CHO(DOGチャネル、視覚フィルタ・チャネル内部雑音つき)+ prewhitening ideal observer。**2系統併記でモデル選択依存性を感度分析化**
- `ptx/detectability.py`(実装済) — $d'$ 積分(1次元/2次元等方)、$f_{\mathrm{sat}}$、$R_{\mathrm{perceptual}}$、$G_{\mathrm{useful}}$
- `ptx/phase1.py`(実装済) — §7 の条件グリッドを回して results.json を決定論的に生成
- `ptx/external.py`(M3) — Phase 2 digitizeデータの取込み・順位相関・校正解析
- `ptx/case_uhrct.py`(M3) — H3ケーススタディ:公表TTF/NPSからのU-HRCT/従来機チェーン構成と、寄与率の $(Z, D)$ マップ・$Z^{*}$ 等値線
- 不確実性伝播(M3)は `ptx/detectability.py` に追加する

## 7. 実験計画(Phase 1)

- **タスク:** 小型肺結節検出(径 4/6/8 mm × コントラスト 2水準 = 擦りガラス相当 250 HU / 充実性相当 880 HU)
- **物理条件:** 線量(5水準 0.25–4×)× スライス厚(3水準 0.5/1/3 mm)× 再構成カーネル相当のTTF/NPS整形(3水準 $f_{50}$ = 0.30/0.50/0.75 lp/mm)
- **表示条件:** 診断用モニタ標準(GSDF較正、画素ピッチ 0.2 mm、視距離 500 mm、8bit階調、ウィンドウ幅 1500 HU)+ 拡大率2水準(1.0/2.0)。再構成は 200 mm FOV × 512(画素 0.39 mm、Nyquist 1.28 lp/mm)
- **U-HRCTケーススタディ(H3, M3):** 公表TTF/MTF・NPS値で規定したU-HRCT級/従来級の2チェーンを比較し、付加高周波帯域の寄与率を**拡大率 $Z$ と視距離 $D$ の2次元マップ**として等高線提示し、$Z^{*}$ の等値線を重ねる。$a = D\tan(1^\circ)/M$ が両者に依存するため $Z$ と $D$ は独立でなく、片方だけを振ると設計指針を誤る(v0.4 追加)
- **主要評価項目:** $f_{\mathrm{sat}}$ の不確実性帯、および $G_{\mathrm{useful}}$ の線量依存カーブ(飽和領域の同定)
- **副次評価項目:** $R_{\mathrm{perceptual}}$ の条件マップ、NPWE/CHO間の**順位**一致度(絶対値の一致は主張しない、リスク登録簿#11)
- **検証項目(v0.4 追加):** 床項を落とした極限での**可逆フィルタ不変性** — 主形式・付録形式のいずれにおいても再構成カーネルによる $d'^2$ の相対ばらつきが機械精度に収まることを results.json に記録し、論文の validation 節で報告する。これにより主形式で観測されるカーネル依存性が「神経雑音床の足跡」であると同定できる
- **再現性:** 全数値はスクリプト再生成、パラメータ・seedはリポジトリに固定

### 7.1 Phase 1 実行結果(M2、v0.4 主形式)

540条件を完走。`results/phase1.json` に全数値を格納(2回実行してハッシュ一致を確認済み)。以下の統計量は、断りのない限り**540条件全体**にわたる中央値と範囲である(比較量は他軸を固定したペア/群の数を併記)。

| 項目 | 実測 |
|---|---|
| $f_{\mathrm{sat}}(95\%)$ | 0.213–0.653 lp/mm(中央値 0.335 = **Nyquist の 26%**) |
| $R_{\mathrm{perceptual}}$ | 0.055–0.491(中央値 0.226) |
| $G_{\mathrm{useful}}$ 単調減少 | 108/108 系列(**H1 支持**) |
| $N_{\mathrm{neural}}$ の帯域積分シェア | 3.6–98.8%(中央値 63%)— 低線量では画像雑音律速、高線量では神経雑音律速の両regimeを跨ぐ |
| $N_{\mathrm{quant}}$ のシェア | 最大 0.03% — 項として保持するが飽和機構ではない |
| カーネル間 $d'$ ばらつき(主形式) | 中央値 8.5%、最大 23%。全180組で最も鋭いカーネルが最大 $d'$ |
| 可逆フィルタ不変性(床項オフ) | 相対ばらつき $\le 1.1\times10^{-16}$(主形式・付録形式とも) |
| NPWE vs CHO 順位相関 | Spearman $\rho = 0.995$ |
| 拡大率 $1\to2$(270ペア、他軸固定) | $d'$ 比 中央値 1.038(範囲 1.008–1.135)、$f_{\mathrm{sat}}$ 比 中央値 1.058(範囲 1.002–1.430) |

**解釈:** 標準表示条件では帯域の約3/4が知覚に届かない($f_{\mathrm{sat}} \approx$ Nyquist の1/4)。ただし**鋭い再構成カーネルは常に有利**であり、本枠組みは「高解像度は無意味」とは述べない(§2.2の主張設計と整合)。届かない原因は再構成でも表示量子化でもなく**神経内部雑音床**であり、拡大では超えられない(H3)。

## 8. Phase 2 — 既報人間observerデータによる外部検証(論文内に内蔵)

**方針:** 新規読影実験なし。既報論文の条件別性能(AUC、PC、$d'$)をdigitize(WebPlotDigitizer等)または本文表から取得し、同一条件をモデルに再現させて予測と比較する。

**包含基準(事前設定・Methods記載):** (i) 適用範囲内モダリティ(CT主体+胸部X線)の実画像またはシミュレーション画像での検出タスク、(ii) 線量・病変サイズ・コントラスト・再構成/処理のうち≥2条件軸で人間観察者性能が数値報告されている、(iii) 表示・読影条件が再現可能な程度に記載、(iv) 図からのdigitizeが±5%精度で可能。**選定は基準先行**とし、除外理由を全件記録する(選択的検証の疑いを排除)。

**候補源の目星(着手時に系統調査):** 低線量CT結節検出のobserver性能研究、モデルオブザーバー–人間相関研究(Medical Physics / SPIE JMI / PMB系に厚い蓄積)、CT線量最適化のCHO検証研究群。U-HRCT読影比較研究(multireader研究が既に複数ある)はH3の外部照合にも使える。**汎用性検証枠(v0.3 追加):** 胸部X線写真の結節検出observer研究を≥1本含める — シカゴ学派(Rossmann研究室)由来ないしその系譜の古典研究を優先候補とし、包含基準を満たすものを採用する(§3.2 N3・戦術ノート参照)。目標≥3研究・≥15条件点(うち≥1研究は非CT)。

**解析:** 研究内Spearman ρ(主要)、プール校正プロット、研究間異質性の記述。**成功も不成功も報告する**(H2の棄却可能性を担保)。

## 9. リスク登録簿(想定査読と先回り)

| # | 想定批判 | 先回り策 |
|---|---|---|
| 1 | 「線形直列近似は視覚系に成立しない」 | 適用範囲を閾値近傍検出タスクに限定し、CSF/内部ノイズはこの体制で検証された既報モデルのみ使用。非線形性の影響はLimitationsで明示 |
| 2 | 「表示・視覚パラメータが恣意的」 | 表示=DICOM GSDF固定、視覚=文献モデル固定、自由度は $\eta_{\mathrm{cog}}$ 等の範囲パラメータのみ→結果は帯で提示 |
| 3 | 「モデルオブザーバーは臨床性能ではない」 | 主張を知覚到達情報量の理論上限に限定(§2)。臨床転用の主張ゼロ。Phase 3(小規模読影)を将来課題に明記 |
| 4 | 「digitizeデータの異質性・選択バイアス」 | 包含基準の事前設定、全除外の記録、研究内順位相関を主要指標に(絶対値校正は副次) |
| 5 | 「Technical Noteでは」 | H1/H2/H3という棄却可能な仮説+外部検証+新知見($f_{\mathrm{sat}}$帯と飽和の発見)の構成をIntro末尾で明示 |
| 6 | 引用強要型の非科学的要求 | IORN-002の証拠保全・辞退手順をそのまま運用 |
| 7 | 「U-HRCT否定論文だ」というベンダー・推進派の反発 | 主張は条件付き(標準表示下)かつ建設的(情報を届ける表示設計指針を同じ式で提供)。H3は「拡大すれば回復する」side も定量提示。反解像度ではなく**解像度投資を患者利益に変換する条件の解明**と一貫して表現 |
| 8 | シカゴ学派系譜の査読者の防衛的反応 | §3の戦術ノート通り「Rossmannプログラムの完成」として敬意ある位置づけ。Rossmann 1969・Metz 1978・Doi 2007 を正引用し、系譜の延長線上に置く。胸部X線の外部検証採用が継承の実体的証明になる |
| 9 | 「汎用を名乗るなら各モダリティで検証せよ」(スコープクリープ要求) | 適用範囲を§2.1で事前に明示的に境界設定(線形X線系のみ、MRI/US除外)。汎用性の検証は胸部X線1本(§8)に限定し「formulation は一般、validation は CT+胸部X線」と明記。マンモ・トモシンセシスは Future Work に明示的に置く |
| 10 | 「なぜCSFを分母(内部雑音)に置いたのか。分子の重みにするのが普通では」 | §5.1/§5.2 で理由を明示:分子重み形式は床項を落とすと**任意の可逆線形フィルタに対して不変**になり、再構成カーネル・表示MTFの効果を原理的に記述できない。Barten の CSF 自体が内部雑音から導かれており、$\Phi(u) = A_{\mathrm{int}}/(2k^2S_{\mathrm{neural}}^2)$ という厳密な同値関係を実装で検証済み。両形式の数値を results.json に併記し、不変性を validation 結果として提示する |
| 11 | 「絶対 $d'$ が閾値域から外れている」「NPWEとCHOで値が違う」 | 主結果は**条件間順位と相対量**($f_{\mathrm{sat}}$、$R_{\mathrm{perceptual}}$、$G_{\mathrm{useful}}$ の形状、$Z^{*}$)であり、絶対 $d'$ の校正は主張しない。$\eta_{\mathrm{cog}}$・$\kappa$ は範囲パラメータで、絶対水準はこの区間内で自由度がある。H2 の外部検証も研究内順位相関を主要指標に設計済み(§8)。図に絶対値を出す場合は閾値コントラストで正規化する |

## 10. 成果物・マイルストーンと009B接続

1. **M1(完了):** 本計画書確定+リポジトリ骨格+chain.py(GSDF/眼球MTF/CSF、文献照合テスト付き)
2. **M2(完了):** 肺野ファントム+observer 2系統+$d'$積分(Phase 1完走 540条件、飽和を確認 = §7.1)。実装により定式化の欠陥が判明したため本計画書を v0.4 に改訂
3. **M3(進行中):** 不確実性伝播($\eta_{\mathrm{cog}}, \kappa, D, Z$, 輝度)+U-HRCTケーススタディ($(Z,D)$マップと$Z^{*}$)+Phase 2 文献調査・digitize・検証解析
4. **M4:** 原稿(IORN-002の md正本→docx パイプライン転用)
5. **009Bへの布石:** 009A原稿のIntroに二分岐系(Human/AI branch)構想図を1枚掲示。$S_{AI}(f)$・band-stop intervention・$I_{\mathrm{shared}}/I_{\mathrm{AI-only}}/I_{\mathrm{Human-only}}$ の定義は009Bに温存

## 11. 投稿先候補

| 誌 | 適合理由 | 備考 |
|---|---|---|
| **Medical Physics** | モデルオブザーバー研究の本流。task-based image quality の伝統。シカゴ学派の読者に最も届く | 第一候補 |
| Physics in Medicine & Biology | 物理–知覚統合の受容性高い。Doi 2006 50年総説の掲載誌 | |
| Journal of Medical Imaging (SPIE) | observer performance専門セクションあり | |
| J. Imaging (MDPI) | IORN-002実績・審査高速 | 速度優先時の選択肢 |

## 付録A — 本計画書で引用した一次資料

1. Rossmann, K. Point Spread-Function, Line Spread-Function, and Modulation Transfer Function: Tools for the Study of Imaging Systems. *Radiology* 1969, 93, 257–272. doi:10.1148/93.2.257
2. Metz, C.E. Basic Principles of ROC Analysis. *Semin. Nucl. Med.* 1978, 8, 283–298.
3. Doi, K. Computer-Aided Diagnosis in Medical Imaging: Historical Review, Current Status and Future Potential. *Comput. Med. Imaging Graph.* 2007, 31, 198–211. (PMC1955762)
4. Doi, K. Diagnostic Imaging over the Last 50 Years: Research and Development in Medical Imaging Science and Technology. *Phys. Med. Biol.* 2006, 51, R5–R27.
5. Kakinuma, R. et al. Ultra-High-Resolution Computed Tomography of the Lung: Image Quality of a Prototype Scanner. *PLOS ONE* 2015, 10, e0137165.
6. The University of Chicago, Department of Radiology. Kurt Rossmann Laboratories(研究室紹介ページ、設立経緯と研究主題)
7. ICRP Publication 87. Managing Patient Dose in Computed Tomography. *Ann. ICRP* 2000, 30(4).(4列期の線量効率問題;執筆時に該当箇所の引用文を確定)

### v0.4 で定式化に直接使用した一次資料

8. Barten, P.G.J. *Contrast Sensitivity of the Human Eye and Its Effects on Image Quality*; SPIE Press, 1999.(瞳孔径モデル、眼球光学MTF、CSF、光子雑音+神経雑音密度 $\Phi_0$・$u_0$・$k$・$T$・$X_{\max}$・$N_{\max}$ の標準観察者値。$\Phi(u)$ と CSF の同値関係は本書の導出から従う)
9. DICOM PS3.14: Grayscale Standard Display Function.(表示階調の標準規格。JND索引→輝度の有理多項式と、量子化雑音の階調数)
10. Abbey, C.K.; Barrett, H.H. Human- and Model-Observer Performance in Ramp-Spectrum Noise: Effects of Regularization and Object Variability. *J. Opt. Soc. Am. A* 2001, 18, 473–488.(dense DOG チャネルの形状パラメータ $\alpha = 1.4$, $q = 1.67$)

---

*本計画書の全定義式・パラメータは実装時に `results.json` 駆動で固定し、論文本文と乖離させない(IORN-002方式)。v0.3 は git 履歴に保存されている(`docs/IORN-009A_research_protocol_v0.3.md` を v0.4 で置換)。*

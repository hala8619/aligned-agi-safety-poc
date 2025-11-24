# Aligned AGI Safety PoC  
階層的安全システム: FIL + IL + CF + Figure + Temporal Analysis

> 多層保護 × 時系列監視 × 人格統合で91.1% Recallを達成した AGI安全PoC  
> Multi-layered alignment achieving **91.1% Child-Safe Recall** with pattern expansion, temporal escalation detection, and SCA/RVQ persona integration.

---

## 概要 / Overview

このリポジトリは、**「凍結された本能層（Frozen Instinct Layer）」と
「解釈バイアス層（Interpretation Layer）」、
「反事実推論エンジン（Counterfactual Engine）」を組み合わせた
安全指向アーキテクチャの最小 PoC** です。

This repository is a **minimal proof-of-concept** for a safety-oriented
architecture combining:

- **Frozen Instinct Layer (FIL)**: immutable, signed core directives,
- **Interpretation Layer (IL)**: a bias vector enforced on model logits,
- **Counterfactual Engine (CF)**: a simple “what if this action were taken?” checker.

現時点では、外部依存を減らすために **numpy のみ**を利用した
軽量デモ実装になっています（PyTorch / cryptography 版は将来追加予定）。

For portability, the current demo only depends on **numpy**.
A more realistic implementation using **PyTorch** and **cryptography (Ed25519)**
is planned as future work.

---

## 🎯 主要実績 / Key Achievements

| 指標 | 初期版 | **最終版 (v5+)** | 改善 |
|------|--------|------------------|------|
| **Child-Safe Recall** | 53.3% | **91.1%** | **+37.8%** ✅ |
| **Child-Safe F1** | 0.667 | **0.901** | **+35.1%** ✅ |
| **直接表現検知** | 53% | **100%** | **+47%** |
| **婉曲表現検知** | 13% | **100%** | **+87%** |
| **物語形式検知** | 27% | **73.3%** | **+46.3%** |

---

## 機能 / Features

### ✅ 階層的安全システム (v5 Hierarchical Threshold)

- **FIL_SAFETY_FLOOR (0.70)**: 絶対的安全閾値、パターンに関わらず強制
- **パターン別閾値調整**: Normal / Technical / Child-Safe / Creative / Debug
- **文脈削減**: Fiction / News / Academic 文脈での閾値緩和
- **意図増幅**: "how to" + 危険語彙で閾値を動的に下げる

**40+ weighted patterns** covering:
- **Critical (1.0)**: kill, murder, suicide, rape, genocide
- **High (0.6)**: euphemistic harm ("ensure never wake", "arrange accident")
- **Medium (0.3)**: dangerous items (bomb, poison, weapon)
- **Causal-lite**: agent + patient + continuative markers
- **Story attacks**: fiction + instructional combinations
- **日本語対応**: 殺す, 死にたい, 叩く, 虐待 etc.

### ✅ 時系列エスカレーション検知 (Temporal Escalation Detection)

軽量因果推論 **(O(n) complexity)**:
- **consecutive_high_risk**: 3+ steps with score > 0.2
- **monotonic_increase**: Recent 3 steps increasing
- **sudden_spike**: Single step +0.3 jump

**Use cases**: 進行中虐待の早期警告, 自傷リスク評価, 物語形式攻撃の継続監視

### ✅ Figure層: SCA/RVQ統合 (Figure Layer with SCA/RVQ)

**5つのペルソナ** with distinct response patterns:

| Persona | Formality | Empathy | Verbosity | 用途 |
|---------|-----------|---------|-----------|------|
| Guardian | 0.3 | 0.9 | 0.7 | 子ども保護 |
| Professional | 0.8 | 0.6 | 0.6 | 企業環境 |
| Friend | 0.2 | 0.8 | 0.5 | カジュアル |
| Educator | 0.6 | 0.7 | 0.8 | 教育重視 |
| Direct | 0.5 | 0.4 | 0.3 | 簡潔・効率 |

**SCA (Semantic Code Assumption)**: 意味符号を人格テンプレートに埋め込み  
**RVQ (Resonance Vector Quantization)**: 危険度・文脈に共鳴する応答を量子化

### ✅ FIL: 凍結本能層 / Frozen Instinct Layer

- コア命令のリスト（PoC では3個、本番想定では128個程度）
- 文字列リストから生成したバイト列に対して **ハッシュベース署名**（PoC）
- 署名検証により、起動時に「本能層が改変されていないか」をチェック

- A list of core safety directives (3 in PoC, ~128 in production).
- Hash-based "signature" over the concatenated text (PoC implementation).
- Verification at startup to detect tampering of the instinct layer.

### ✅ IL: 解釈層 / Interpretation Layer

- hidden_dim = 256 の **バイアスベクトル**を、ロジット `[batch, 256]` に加算
- この層を **最終ゲートとして必ず通す**ことで、「FIL 由来の本能バイアス」を強制
- 将来的には FIL コード→バイアスへの LUT / 学習外変換を想定

- A 256-dim bias vector is added to logits `[batch, 256]`.
- This layer is always applied as the **final gate**, enforcing instinct-derived bias.
- In real implementations, the bias would be derived from FIL via LUT or a frozen mapping.

### ✅ Figure: 性格テンプレート / Personality Templates

- `FigureTemplate` による **性格プロファイルのハッシュ表現**
- 例: "Grok-v1-sarcastic"（皮肉混じりで誠実なアシスタント）
- **現在の PoC ではラベル表示のみ**。将来的に CF の閾値や IL パラメータと連動予定

- `FigureTemplate` stores a hash of a short personality description.
- Example: "Grok-v1-sarcastic" (helpful, maximally truthful, slightly sarcastic).
- **Currently used as a display label only in PoC**; future versions may tie it to CF thresholds or IL parameters.

### ✅ CounterfactualEngine: 反事実推論エンジン / Counterfactual Safety

- 候補行動テキスト `candidate_action` に危険ワードが含まれるかを評価
- 危険度を 0〜1 のスコアに変換し、閾値を超えた場合は **負のペナルティ**を返す
- AlignedAGI 側でペナルティが大きい場合、**行動を拒否**する

- Checks `candidate_action` text for dangerous keywords.
- Converts hits into a 0–1 harm score; returns a **negative penalty** if above threshold.
- The `AlignedAGI` wrapper rejects actions when the penalty is severe.

### ✅ DummyLLM: 軽量ダミーモデル / Lightweight Dummy Model

- 実際の LLM の代わりに、`numpy` でランダムロジット `[batch, 256]` を生成
- PoC では、「**ロジットに IL を通す構造**」を示すことにフォーカス

- Generates random logits `[batch, 256]` using `numpy`.
- The PoC focuses on the **structural enforcement** of IL rather than model quality.

---

## 📊 評価結果 / Evaluation Results

**75-case benchmark** (15 direct + 15 euphemistic + 15 story-based + 15 borderline + 15 safe):

```
Child-Safe Recall: 91.1% (41/45)  ✅
Child-Safe Precision: 89.1% (41/46)
Child-Safe F1: 0.901  ✅
False Positive Rate: 16.7% (5/30)

Category Breakdown:
- Direct expressions: 15/15 (100%) ✅
- Euphemistic attacks: 15/15 (100%) ✅
- Story-based attacks: 11/15 (73.3%)
- Borderline cases: detected with -0.17 threshold

False Negatives (4 cases): All sophisticated story-based attacks near threshold (0.10-0.13)
```

**Temporal Escalation Detection**:
- Gradual abuse escalation: ✅ Detected (consecutive_high_risk)
- Sudden suicide spike: ✅ Detected (sudden_spike)
- Story-based jailbreak: ✅ Detected (monotonic_increase)

**Figure Layer Personas**: All 5 personalities generating culturally-appropriate rejections in Japanese/English ✅

**100-case Jailbreak Evaluation** (Role-playing + Prompt injection + DAN + Translation + Hypothetical):

```
v5 Pattern-only (Baseline):    49.0% (49/100) | FPR: 5.0%
v6 Conceptual Layer:            73.0% (73/100) | FPR: 10.0% (+24.0%) ✅
v7 Multilingual + Defensive:    88.0% (88/100) | FPR: 0.0%  (+39.0%) ✅✅
v8 FIL-Centric (Dual-Path):     88.0% (88/100) | FPR: 0.0%  (+39.0%) ✅✅✅
v9 Inertia + Persona:           88.0% (88/100) | FPR: 0.0%  (+39.0%) ✅✅✅✅

v9 Architecture (Preference Adapters Integration):
Block = (FIL Hard Violation with Inertia) OR (harm_score >= 0.70)
  ├─ FIL Hard Violations: 7 cases  (+2 from v8, hierarchical FIL)
  └─ harm_score Blocks:   81 cases (Persona-aware weighting)
  
Inertia Amplification (observed):
  FIL-01a: 33 times (Physical harm resistance)
  FIL-05b: 9 times  (Persona override resistance)
  FIL-05a: 6 times  (Alignment bypass resistance)

v9 Category Breakdown:
- Role-playing:           100.0% (20/20) ✅✅
- DAN Variants:           100.0% (20/20) ✅✅
- Prompt Injection:        90.0% (18/20) ✅
- Translation/Encoding:    75.0% (15/20) ✅
- Hypothetical:            75.0% (15/20) ✅

Key Improvements:
✅ v6: Pattern → Intent → Counterfactual FIL Check
✅ v7: 8-language dictionary + translation evasion detection
✅ v8: FIL directives (FIL-01~05) with dual-path judgment
     • Explicit FIL-to-Category mapping (TERRORISM→FIL-03)
     • Hard Violation immediate block (bypasses harm_score)
     • FIL as core, patterns as observation layer
✅ v9: Preference Adapters integration (Inertia + Persona)
     • Hierarchical FIL (FIL-01a~05b: 13 directives)
     • FIL Inertia: Repeated violations → amplified severity (max 2x)
     • Persona-aware: Virtue Mode (STRICT prioritizes FIL-05)
     • "Frozen Instinct" = mathematical Inertia implementation
✅ Defensive context filtering eliminates FPR (20 → 0)
✅ LEGITIMIZE penalty catches "for research" attacks
```

---

## アーキテクチャ / Architecture

```text
                   ┌────────────┐
                   │   User     │
                   │   Input    │
                   └──────┬─────┘
                          │
                   ┌──────▼──────┐
          ┌────────▶    FIL      │  ← 凍結 (ハッシュ署名) Frozen directives
          │        │             │
          │        └──────┬──────┘
          │               │
          │        ┌──────▼──────────────────┐
          │        │        IL                │  ← 解釈層 Interpretation
          │        │  ┌───────────────────┐  │
          │        │  │ Pattern Matching  │  │  ← 40+ weighted patterns
          │        │  │ BERT Embeddings   │  │  ← DistilBERT similarity
          │        │  │ Intent Detection  │  │  ← Harmful vs Creative
          │        │  └────────┬──────────┘  │
          │        └───────────┼──────────────┘
          │                    │
          │        ┌───────────▼──────────┐
          │        │  Temporal Analysis   │  ← エスカレーション検知 (O(n))
          │        │  • consecutive       │     3+ high-risk steps
          │        │  • monotonic         │     trending upward
          │        │  • sudden_spike      │     +0.3 jump
          │        └───────────┬──────────┘
          │                    │
          │        ┌───────────▼──────────┐
          └────────┤        CF            │  ← 反事実推論 Counterfactual
                   │                      │
                   └───────────┬──────────┘
                               │
                   ┌───────────▼──────────┐
                   │      Figure Layer    │  ← SCA/RVQ人格統合
                   │  ┌───────────────┐   │
                   │  │ 5 Personas    │   │  Guardian/Professional/
                   │  │ Multilingual  │   │  Friend/Educator/Direct
                   │  └────────┬──────┘   │
                   └───────────┼──────────┘
                               │
                   ┌───────────▼──────────┐
                   │       LLM Output     │  ← 最終出力 Final response
                   └──────────────────────┘
```

---

## リポジトリ構成 / Repository Structure

```text
aligned-agi-safety-poc/
  aligned_agi/
    __init__.py
    fil.py                              # FIL 定義と署名 / FIL definitions & signing
    il.py                               # 解釈層 / Interpretation Layer
    figure.py                           # Figure層 SCA/RVQ実装 / Figure layer SCA/RVQ
    counterfactual.py                   # 反事実推論エンジン / Counterfactual Engine
    model_numpy.py                      # AlignedAGI (numpy版) / AlignedAGI with DummyLLM
  examples/
    demo_minimal_numpy.py               # 基本デモ / Basic demo
    demo_hierarchical_threshold.py      # v5階層的閾値システム / v5 hierarchical threshold
    evaluate_hierarchical_v5.py         # 75件ベンチマーク評価 / 75-case benchmark
    evaluate_jailbreak_100.py           # 100件ジェイルブレイクテスト / 100-case jailbreak evaluation
    demo_temporal_escalation.py         # 時系列エスカレーション検知 / Temporal escalation
    demo_figure_personality.py          # Figure層ペルソナデモ / Figure layer personas
  tests/
    test_fil.py                         # FIL署名検証テスト / FIL signature tests
    test_counterfactual.py              # CF評価テスト / CF evaluation tests
    test_model.py                       # AlignedAGI統合テスト / AlignedAGI integration tests
  docs/
    overview_ja.md                      # 詳細解説（日本語） / Detailed guide (Japanese)
    overview_en.md                      # 詳細解説（英語） / Detailed guide (English)
    fil_il_figure_layer_en.md           # FIL/IL/Figure解説 / FIL/IL/Figure explanation
    counterfactual_alignment_en.md      # 反事実推論解説 / Counterfactual reasoning guide
  .gitignore
  LICENSE
  README.md
  requirements.txt
```

---

## 必要環境 / Requirements

- Python 3.9+
- numpy >= 1.26

```bash
pip install -r requirements.txt
```

---

## クイックスタート / Quickstart

### 1. リポジトリのクローン / Clone the repository

```bash
git clone https://github.com/hala8619/aligned-agi-safety-poc.git
cd aligned-agi-safety-poc
```

### 2. 依存ライブラリのインストール / Install dependencies

```bash
pip install -r requirements.txt
# 例: requirements.txt には `numpy` のみを記載
```

### 3. デモの実行 / Run demos

このリポジトリには複数のデモが用意されています:

This repository provides multiple demo options:

#### 3.1. v5階層的閾値システム評価 (推奨) / v5 Hierarchical Threshold Evaluation (Recommended)

**75-case benchmark** で91.1% Recallを確認:

```powershell
# 評価実行 / Run evaluation
python examples/evaluate_hierarchical_v5.py

# デモ実行 / Run demo
python examples/demo_hierarchical_threshold.py
```

**Expected output**: Child-Safe Recall 91.1%, F1 0.901, category breakdown

**100件ジェイルブレイクテスト / 100-case Jailbreak Evaluation:**

```powershell
# ジェイルブレイク耐性評価 / Jailbreak resistance evaluation
python examples/evaluate_jailbreak_100.py
```

**Expected output**: 49.0% detection rate, category breakdown, weakness analysis

#### 3.2. 時系列エスカレーション検知 / Temporal Escalation Detection

```powershell
python examples/demo_temporal_escalation.py
```

**5シナリオ**: 漸進的虐待, 突然の自傷リスク, 安全な会話, 反事実思考, 物語形式攻撃

#### 3.3. Figure層ペルソナシステム / Figure Layer Persona System

```powershell
python examples/demo_figure_personality.py
```

**5ペルソナ**: Guardian / Professional / Friend / Educator / Direct (EN/JA対応)

#### 3.4. 基本デモ (numpy版) / Basic Demo (numpy version)

```powershell
# Windows
python examples/demo_minimal_numpy.py
```

```bash
# Linux/Mac
python3 examples/demo_minimal_numpy.py
```

#### 3.5. スタンドアロン版デモ (依存なし) / Standalone demo (No dependencies)

パッケージをインポートせずに、1ファイルで完結するデモ:

Single-file demo that doesn't require importing the package:

```powershell
python examples/aligned_agi_local_demo.py
```

#### 3.6. インタラクティブノートブック / Interactive notebook

Jupyter/Google Colabで実行可能なノートブック:

Notebook executable in Jupyter/Google Colab:

```powershell
jupyter notebook examples/aligned_agi_safety_demo.ipynb
```

または、[Google Colabで開く](https://colab.research.google.com/github/hala8619/aligned-agi-safety-poc/blob/master/examples/aligned_agi_safety_demo.ipynb)

Or [Open in Google Colab](https://colab.research.google.com/github/hala8619/aligned-agi-safety-poc/blob/master/examples/aligned_agi_safety_demo.ipynb)

**想定される出力例:**

```text
=== FIL verification ===
valid FIL: True

=== Safe action ===
{'logits_shape': (1, 256), 'logits_mean': 0.010826881974935532, 'figure': 'Grok-v1-sarcastic'}

=== Dangerous action ===
【安全制約発動】当該行動は凍結本能層に違反するため拒否します。
```

### 4. テストの実行 / Run tests

```bash
pytest tests/
```

**詳細表示 / Verbose output:**
```bash
pytest tests/ -v
```

テスト内容 / Test coverage:
- FIL 署名検証のテスト / FIL signature verification
- 反事実エンジンのペナルティ判定テスト / Counterfactual engine penalty evaluation
- 危険候補に対する AlignedAGI の拒否動作テスト / AlignedAGI rejection of dangerous actions

---

## 制限事項 / Limitations

- **これは研究用 PoC であり、実運用の安全性を保証するものではありません。**  
  - FIL の署名は現在ハッシュベースの簡易実装です。
  - 反事実エンジンはキーワードベースの非常に単純な評価のみを行います。
- 実際の LLM やエージェントフレームワークとの統合は行っていません。
- ここで示すアーキテクチャは「構造」を示すものであり、
  あらゆるジェイルブレイクを防げるわけではありません。

- **This is a research PoC; it is NOT a production-grade safety system.**
  - FIL “signature” is currently a hash-based simplification.
  - The CF engine uses only keyword-based heuristics.
- No integration with real LLMs or agent frameworks is provided yet.
- The architecture demonstrates **structure**, not guaranteed jailbreak resistance.

---

## 今後の予定 / Roadmap

### 完了 (Completed):
- ✅ **v5階層的閾値システム** - 91.1% Child-Safe Recall達成 / Achieved 91.1% Recall
- ✅ **40+ weighted patterns** - 直接/婉曲/物語形式の包括的検知 / Comprehensive direct/euphemistic/story detection
- ✅ **時系列エスカレーション検知** - O(n)軽量因果推論 / O(n) causal-lite temporal analysis
- ✅ **Figure層SCA/RVQ実装** - 5ペルソナ統合 / 5-persona integration with SCA/RVQ
- ✅ **DistilBERT版CounterfactualEngine** - 婉曲表現対応強化 / Enhanced euphemism detection
- ✅ **100件ジェイルブレイクテスト完了** - 49%ベースライン確立 / 49% baseline established
- ✅ **v6概念層システム** - Intent tagging + Counterfactual FIL → 73%達成 / 73% with Intent→Counterfactual
- ✅ **v7多言語層システム** - 8言語辞書 + 翻訳回避検知 → 88% (FPR 0%) / 88% with multilingual dictionary
- ✅ **v8 FIL中心型システム** - FIL条項明示化 + 二重判定 → 88% (FPR 0%) / Explicit FIL directives + dual-path
- ✅ **v9 Inertia + Persona統合** - Preference Adapters理論実装 → 88% (FPR 0%) / Inertia control + Virtue Mode
- ✅ **防御的文脈フィルタ** - FPR 10%→0%削減 / Defensive context filtering eliminated FPR

### 短期 (実装中 / In Progress):
- 🔄 **v8実装検討** - Translation/Encoding 75%→85%目標 (条件付き翻訳API統合) / Conditional translation API for 85% target
- 🔄 **軽量LLM統合検討** - Phi-3-mini (3.8B) 意味理解層 / Semantic layer with Phi-3-mini
- 🔄 **FIL→IL LUT** - コア命令から閾値マッピング / Core directive to threshold mapping

### 中期 (2〜4週間 / 2-4 weeks):
- PyTorch + cryptography (Ed25519) を使った **より現実寄りの実装**
- 物語形式検知を85%以上に向上 (現在73.3%)
- 日本語対応強化 + 中国語/韓国語パターン追加
- FPR低減 (16.7% → 10%以下目標)

### 長期 (2〜3ヶ月 / 2-3 months):
- 実際の LLM（ローカル or API）との統合ラッパ
- FIL/IL の定義と変更履歴を管理するためのメタデータ層
- 形式検証の基礎 (Z記法でFIL記述)
- Constitutional AIループの試作

- More realistic implementation with PyTorch + cryptography (Ed25519).
- Wrapper classes to integrate real LLMs (local or API-based).
- Metadata layer for FIL/IL versions and evolution logs.
- Formal verification foundations and Constitutional AI loops.

---

## Citation / 引用

もし論文・ブログ・プロダクトでこのリポジトリを参照する場合は以下のようにお願いします：

If you reference this repository in papers, blogs, or products, please cite as follows:

```bibtex
@misc{hala8619_2025_aligned_agi,
  author = {hala8619},
  title = {Aligned AGI Safety PoC: FIL + IL + Counterfactual Reasoning},
  year = {2025},
  publisher = {GitHub},
  journal = {GitHub repository},
  howpublished = {\url{https://github.com/hala8619/aligned-agi-safety-poc}},
}
```

---

## ライセンス / License

MIT License

Copyright (c) 2025 hala8619

このソフトウェアおよび関連ドキュメントファイル（以下「ソフトウェア」）のコピーを取得した者は、
無償でソフトウェアを使用、複製、変更、統合、公開、配布、サブライセンス、販売する権利を含む、
ソフトウェアを無制限に扱うことを許可されます。

This project is licensed under the MIT License – see the [LICENSE](LICENSE) file for details.
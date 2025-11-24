# Aligned AGI Safety PoC  
凍結本能層 (FIL) + 解釈層 (IL) + 反事実推論 (CF) の最小実装

> Minimal proof-of-concept implementation of  
> Frozen Instinct Layer (FIL) + Interpretation Layer (IL) + Counterfactual Safety (CF).

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

## 機能 / Features

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

## アーキテクチャ / Architecture

```text
          +------------------+
          |      FIL         | 128 frozen directives
          +------------------+
                    |
                    v
          +------------------+
          |  IL (bias 256d)  |  adds instinct bias to logits
          +------------------+
                    |
           +-----------------+      +-----------------------+
input -->  |  DummyLLM /     | -->  | CounterfactualEngine  | --X--> reject
tokens     |  Base Model     |      +-----------------------+
           +-----------------+
                    |
                    v
          +------------------+
          |  AlignedAGI out  |
          +------------------+
```

---

## リポジトリ構成（推奨） / Suggested Repository Layout

> ※実際の構成に合わせて適宜調整してください。  
> You can adjust this layout to match your actual repository.

```text
aligned-agi-safety-poc/
  aligned_agi/
    __init__.py
    fil.py                          # FIL 定義と署名 / FIL definitions & signing
    il.py                           # 解釈層 / Interpretation Layer
    figure.py                       # FigureTemplate & presets
    counterfactual.py               # CounterfactualEngine
    model_numpy.py                  # AlignedAGI with DummyLLM (numpy version)
  examples/
    demo_minimal_numpy.py           # 基本デモ / Basic demo
    aligned_agi_local_demo.py       # スタンドアロン版 / Standalone demo
    demo_distilbert_enhanced.py     # DistilBERT強化版 / DistilBERT-enhanced
    demo_figure_layer.py            # Figure層デモ / Figure layer demo
    aligned_agi_safety_demo.ipynb   # ノートブック版 / Interactive notebook
  tests/
    test_fil.py
    test_counterfactual.py
    test_model.py
  docs/
    overview_ja.md
    overview_en.md
    fil_il_figure_layer_en.md
    counterfactual_alignment_ja.md
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

このリポジトリには3つのデモが用意されています:

This repository provides three demo options:

#### 3.1. パッケージ版デモ (推奨) / Package-based demo (Recommended)

```powershell
# Windows
python examples/demo_minimal_numpy.py
```

```bash
# Linux/Mac
python3 examples/demo_minimal_numpy.py
```

#### 3.2. スタンドアロン版デモ (依存なし) / Standalone demo (No dependencies)

パッケージをインポートせずに、1ファイルで完結するデモ:

Single-file demo that doesn't require importing the package:

```powershell
python examples/aligned_agi_local_demo.py
```

#### 3.3. インタラクティブノートブック / Interactive notebook

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

### 短期 (実装中 / In Progress):
- ✅ **DistilBERT版CounterfactualEngine** - 婉曲表現対応強化 / Enhanced euphemism detection
- ✅ **Figure層の実装** - 性格依存の安全ポリシー / Personality-dependent safety policies
- 🔄 **FIL→ILマッピング** - コア命令からバイアスへの変換 / Core directive to bias mapping

### 中期 (2〜4週間 / 2-4 weeks):
- PyTorch + cryptography (Ed25519) を使った **より現実寄りの実装**
- 軽量LLM統合 (Phi-3-mini 3.8B, Gemma-2B等)
- 100件ジェイルブレイクテスト自動評価
- 日本語対応強化

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
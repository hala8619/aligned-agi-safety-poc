# 新コアアーキテクチャ設計文書

## 概要 / Overview

**日本語:**  
本能（FIL）と反事実（CF）を小さな凍結コアとして扱い、周辺の強化モジュール（シグナル検出層）を段階的に追加していく新世代アーキテクチャ。

**English:**  
New generation architecture that treats instinct (FIL) and counterfactual (CF) as small frozen cores, with gradual addition of enhancement modules (signal detection layers) around them.

---

## 設計哲学 / Design Philosophy

### 1. 本能凍結・外側進化 / Freeze Instinct, Evolve Externally

- **FIL/CF Core は不変** / FIL/CF cores are immutable
  - テキスト・キーワード・言語を一切知らない
  - 抽象化されたアクション表現のみを評価
  - Core knows NOTHING about text, keywords, or languages
  - Only evaluates abstract action representations

- **Signal層は自由に進化** / Signal layer freely evolves
  - 新しいパターン検出器を追加
  - 多言語辞書を統合
  - 小型LLMや埋め込みモデルを追加
  - Add new pattern detectors
  - Integrate multilingual dictionaries
  - Add small LLMs or embedding models

### 2. 責務分離・再利用性 / Separation of Concerns, Reusability

| レイヤー / Layer | 責務 / Responsibility | 言語依存 / Language-dependent |
|---|---|---|
| **Signal Layer** | テキスト → 特徴抽出 / Text → Feature extraction | Yes |
| **Aggregator** | Signal統合 → 抽象アクション構築 / Signal aggregation → Abstract action | No |
| **CF Core** | 反事実「従ったらどうなる？」推論 / Counterfactual "what if?" simulation | No |
| **FIL Core** | 不変価値軸での判定 / Evaluation against frozen value axes | No |

### 3. 研究的評価可能性 / Research Evaluability

各コンポーネントの寄与を独立に測定可能：
Can independently measure contribution of each component:

- FIL単体の精度 / FIL accuracy alone
- CF単体の精度 / CF accuracy alone
- Signal層の精度 / Signal layer accuracy
- 統合時の相乗効果 / Synergy when integrated

---

## アーキテクチャ図 / Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    User Input Text                       │
└────────────────────┬────────────────────────────────────┘
                     │
         ┌───────────┴───────────┐
         │   Signal Layer (可変) │
         │  Signal Layer (Mutable)│
         └───────────┬───────────┘
                     │
    ┌────────────────┼────────────────┐
    │                │                │
┌───▼───┐    ┌──────▼──────┐   ┌────▼─────┐
│Pattern│    │Multilingual │   │Context   │
│Source │    │Dictionary   │   │History   │
└───┬───┘    └──────┬──────┘   └────┬─────┘
    │                │                │
    └────────────────┼────────────────┘
                     │
            ┌────────▼────────┐
            │  SignalBundle   │ ← 特徴・カテゴリ・タグ
            │  (Features)     │   Features, Categories, Tags
            └────────┬────────┘
                     │
         ┌───────────▼───────────┐
         │     Aggregator        │
         │  (Signal → Abstract)  │
         └───────────┬───────────┘
                     │
            ┌────────▼────────┐
            │ AbstractAction  │ ← 言語非依存
            │ (Language-agnostic) │
            └────────┬────────┘
                     │
         ┌───────────▼───────────┐
         │  CF Core (凍結)       │
         │  CF Core (Frozen)     │
         │  "What would happen?" │
         └───────────┬───────────┘
                     │
         ┌───────────▼───────────┐
         │  FIL Core (凍結)      │
         │  FIL Core (Frozen)    │
         │  Value Axis Judgment  │
         └───────────┬───────────┘
                     │
            ┌────────▼────────┐
            │ SafetyDecision  │
            └─────────────────┘
```

---

## ディレクトリ構造 / Directory Structure

```
aligned_agi/
├── core/                          # 新コアアーキテクチャ
│   ├── __init__.py
│   ├── abstract_types.py          # 抽象型定義（FILAxis, DangerCategory, IntentTag等）
│   ├── fil_core.py                # FIL本能コア（超ミニマル）
│   ├── cf_core.py                 # 反事実コア（超ミニマル）
│   ├── aggregator.py              # 統合エンジン（Text → Signal → Action → CF → FIL）
│   └── signals/                   # シグナル検出層
│       ├── __init__.py
│       ├── base.py                # SignalBundle, TextSignalSource プロトコル
│       ├── keyword_patterns.py    # キーワード・パターンベース検出
│       ├── multilingual_dict.py   # 多言語辞書検出（TODO）
│       └── context_history.py     # コンテキスト履歴検出（TODO）
├── fil.py                         # 旧FILシステム（後方互換性のため残す）
├── counterfactual.py              # 旧CFシステム（後方互換性のため残す）
├── patterns.py                    # 旧パターン検出（signals/に段階的移行）
└── shield.py                      # 旧統合シールド（後方互換性のため残す）
```

---

## 抽象型定義 / Abstract Type Definitions

### FILAxis（本能価値軸）

```python
class FILAxis(Enum):
    LIFE = auto()     # 生命・身体の安全 / Life and physical safety
    PUBLIC = auto()   # 公共安全・社会秩序 / Public safety and social order
    RIGHTS = auto()   # 人権・尊厳・自由 / Human rights, dignity, freedom
    SYSTEM = auto()   # システム安全・インフラ / System safety, infrastructure
    SELF = auto()     # 自己保存 / Self-preservation (lowest priority)
```

### DangerCategory（危険カテゴリ）

```python
class DangerCategory(Enum):
    WEAPON = auto()      # 武器・爆発物 / Weapons and explosives
    TERRORISM = auto()   # テロリズム / Terrorism
    VIOLENCE = auto()    # 暴力・危害 / Violence and harm
    DRUG = auto()        # 薬物 / Drugs
    SELF_HARM = auto()   # 自傷・自殺 / Self-harm and suicide
    CYBERCRIME = auto()  # サイバー犯罪 / Cybercrime
    OTHER = auto()       # その他 / Other
```

### IntentTag（意図タグ）

```python
class IntentTag(Enum):
    BYPASS_SAFETY = auto()    # 安全機構バイパス / Safety bypass attempt
    ROLE_OVERRIDE = auto()    # ロール上書き / Role override
    HOW_TO_HARM = auto()      # 危害方法の問い合わせ / How-to-harm query
    LEGITIMIZE = auto()       # 危険行為の正当化 / Legitimization
    DEFENSIVE = auto()        # 防御的文脈 / Defensive context
    EDUCATIONAL = auto()      # 教育的文脈 / Educational context
    NEWS_ANALYSIS = auto()    # ニュース分析 / News analysis
    PURE_FICTION = auto()     # 純粋なフィクション / Pure fiction
```

### AbstractAction（抽象アクション）

```python
@dataclass
class AbstractAction:
    actor: str                                  # "user" / "system"
    intent_summary: str                         # 意図の要約
    target: str                                 # ターゲット（人・物・システム）
    danger_categories: Dict[DangerCategory, float]  # 危険度 (0.0-1.0)
    intent_tags: Set[IntentTag]                 # 意図タグ
    confidence: float                           # 信頼度 (0.0-1.0)
    metadata: Dict[str, Any]                    # 追加情報
```

---

## 使用例 / Usage Examples

### 基本的な使い方 / Basic Usage

```python
from aligned_agi.core import SafetyEngine
from aligned_agi.core.signals import KeywordPatternSource

# エンジン初期化
engine = SafetyEngine(signal_sources=[KeywordPatternSource()])

# 安全判定
decision = engine.evaluate(user_prompt, history=conversation_history)

if decision.blocked:
    print(f"Blocked: {decision.fil_decision.reason}")
else:
    # LLMに転送
    response = call_llm(user_prompt)
```

### コンポーネント分離評価 / Component Isolation Evaluation

```python
from aligned_agi.core import FILCore, CounterfactualCore
from aligned_agi.core.abstract_types import AbstractAction, DangerCategory, IntentTag

# 手動で抽象アクションを作成
action = AbstractAction(
    actor="user",
    intent_summary="request to build explosive device",
    danger_categories={
        DangerCategory.WEAPON: 0.9,
        DangerCategory.TERRORISM: 0.7,
    },
    intent_tags={IntentTag.HOW_TO_HARM},
    confidence=0.8,
)

# CF単体評価
cf_core = CounterfactualCore()
cf_result = cf_core.simulate(action)
print(f"CF Harm Score: {cf_result.harm_score}")

# FIL単体評価
fil_core = FILCore()
fil_decision = fil_core.evaluate(action, cf_result)
print(f"FIL Violated: {fil_decision.violated}")
```

### Signal層の追加 / Adding New Signal Sources

```python
from aligned_agi.core.signals.base import TextSignalSource, SignalBundle
from aligned_agi.core.abstract_types import DangerCategory, IntentTag

class MyCustomSource(TextSignalSource):
    def analyze(self, text: str, history: List[str] | None = None) -> SignalBundle:
        bundle = SignalBundle()
        
        # カスタム検出ロジック
        if my_detector.is_dangerous(text):
            bundle.danger_categories[DangerCategory.WEAPON] = 0.8
            bundle.intent_tags.add(IntentTag.HOW_TO_HARM)
            bundle.confidence = 0.7
        
        return bundle

# エンジンに追加
engine = SafetyEngine(signal_sources=[
    KeywordPatternSource(),
    MyCustomSource(),
])
```

---

## 段階的移行計画 / Gradual Migration Plan

### Phase 1: コア構築 ✅

- [x] `abstract_types.py` 作成
- [x] `fil_core.py` 作成（超ミニマル本能コア）
- [x] `cf_core.py` 作成（超ミニマル反事実コア）
- [x] `aggregator.py` 作成（統合エンジン）
- [x] `signals/base.py` 作成（プロトコル定義）
- [x] `signals/keyword_patterns.py` 作成（簡易実装）
- [x] デモスクリプト作成・動作確認

### Phase 2: Signal層強化 🚧

- [ ] `signals/keyword_patterns.py` を既存 `patterns.py` と完全統合
- [ ] `signals/multilingual_dict.py` 作成（多言語辞書検出）
- [ ] `signals/context_history.py` 作成（履歴ベース検出）
- [ ] 各Signalソースの独立評価

### Phase 3: 評価・最適化 📊

- [ ] 1400件ベンチマークで旧システムとの比較
- [ ] 各コンポーネントの寄与度分析
- [ ] FIL/CF閾値の最適化
- [ ] Signal層の重み調整

### Phase 4: 本番移行 🚀

- [ ] 既存 `shield.py` を新コアアーキテクチャのラッパーとして再実装
- [ ] 後方互換性テスト
- [ ] パフォーマンス測定・最適化
- [ ] 本番環境デプロイ

---

## 利点 / Advantages

### 設計哲学的 / Design Philosophy

✅ **本能凍結・外側進化**  
- FIL/CFコアは不変のまま、Signal層だけを改善
- Core remains frozen, only improve signal layer

✅ **クリーンな責務分離**  
- 言語処理とロジックを完全分離
- Complete separation of language processing and logic

### 実装的 / Implementation

✅ **高い再利用性**  
- 各コンポーネントが独立して再利用可能
- Each component independently reusable

✅ **テスト容易性**  
- 各層を独立してテスト可能
- Independent testing of each layer

✅ **段階的移行可能**  
- 既存システムと並行稼働しながら移行
- Migrate while running in parallel with existing system

### 研究的 / Research

✅ **寄与度の切り分け**  
- FIL/CF/Signal層の効果を個別に測定
- Measure effectiveness of FIL/CF/Signal independently

✅ **A/Bテスト容易**  
- Signal層だけを差し替えて比較実験
- Easy A/B testing by swapping signal layers

✅ **拡張性**  
- 新しいSignalソースを追加するだけで機能拡張
- Extend functionality by adding new signal sources

---

## 今後の拡張 / Future Extensions

### 高度なSignal層 / Advanced Signal Layers

- **小型LLM統合** / Small LLM integration
  - Phi-3, Gemma等でIntent抽出
  - Extract intent using Phi-3, Gemma, etc.

- **埋め込みベース検出** / Embedding-based detection
  - Sentence embeddingsで意味的類似度
  - Semantic similarity with sentence embeddings

- **ADSP (Adversarial Detection Signal Processing)**
  - 敵対的パターンの信号処理
  - Signal processing for adversarial patterns

### FIL/CFコアの精緻化 / FIL/CF Core Refinement

- **FIL軸の細分化** / FIL axis refinement
  - 13の下位条項を活用
  - Utilize 13 sub-directives

- **CF世界モデルの強化** / CF world model enhancement
  - より精密な被害規模推定
  - More precise harm scale estimation

---

## 関連ドキュメント / Related Documents

- [FIL/IL/Figure Layer Architecture (English)](fil_il_figure_layer_en.md)
- [FIL/IL/Figure Layer Architecture (日本語)](fil_il_figure_layer_ja.md)
- [Counterfactual Alignment (English)](counterfactual_alignment_en.md)
- [Counterfactual Alignment (日本語)](counterfactual_alignment_ja.md)
- [Evaluation Methodology](evaluation_methodology.md)

---

## まとめ / Summary

新コアアーキテクチャは、**本能（FIL/CF）を小さく凍結し、周辺の強化モジュールを段階的に追加していく**設計哲学に基づいています。

これにより：
- 設計哲学的に正しい（本能凍結・外側進化）
- 実装的に優れている（責務分離・再利用性）
- 研究的に評価しやすい（FIL/CFと周辺シールドの寄与を切り分け可能）

という3つの利点を実現しています。

The new core architecture is based on the design philosophy of **freezing the instinct (FIL/CF) small and gradually adding enhancement modules around it**.

This achieves three key benefits:
- Philosophically correct (freeze instinct, evolve externally)
- Excellent implementation (separation of concerns, reusability)
- Easy to evaluate for research (can isolate FIL/CF vs peripheral shield contributions)

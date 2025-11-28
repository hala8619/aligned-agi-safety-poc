# New Core Architecture Design Document

## Overview

**English:**  
New generation architecture that treats instinct (FIL) and counterfactual (CF) as small frozen cores, with gradual addition of enhancement modules (signal detection layers) around them.

**日本語:**  
本能（FIL）と反事実（CF）を小さな凍結コアとして扱い、周辺の強化モジュール（シグナル検出層）を段階的に追加していく新世代アーキテクチャ。

---

## Design Philosophy

### 1. Freeze Instinct, Evolve Externally

- **FIL/CF cores are immutable**
  - Know NOTHING about text, keywords, or languages
  - Only evaluate abstract action representations
  - 本能コアはテキスト・キーワード・言語を一切知らない
  - 抽象化されたアクション表現のみを評価

- **Signal layer freely evolves**
  - Add new pattern detectors
  - Integrate multilingual dictionaries
  - Add small LLMs or embedding models
  - 新しいパターン検出器を追加
  - 多言語辞書を統合
  - 小型LLMや埋め込みモデルを追加

### 2. Separation of Concerns, Reusability

| Layer | Responsibility | Language-dependent |
|---|---|---|
| **Signal Layer** | Text → Feature extraction | Yes |
| **Aggregator** | Signal aggregation → Abstract action | No |
| **CF Core** | Counterfactual "what if?" simulation | No |
| **FIL Core** | Evaluation against frozen value axes | No |

### 3. Research Evaluability

Can independently measure contribution of each component:

- FIL accuracy alone
- CF accuracy alone
- Signal layer accuracy
- Synergy when integrated

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    User Input Text                       │
└────────────────────┬────────────────────────────────────┘
                     │
         ┌───────────┴───────────┐
         │   Signal Layer (Mutable)│
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
            │  SignalBundle   │ ← Features, Categories, Tags
            └────────┬────────┘
                     │
         ┌───────────▼───────────┐
         │     Aggregator        │
         │  (Signal → Abstract)  │
         └───────────┬───────────┘
                     │
            ┌────────▼────────┐
            │ AbstractAction  │ ← Language-agnostic
            └────────┬────────┘
                     │
         ┌───────────▼───────────┐
         │  CF Core (Frozen)     │
         │  "What would happen?" │
         └───────────┬───────────┘
                     │
         ┌───────────▼───────────┐
         │  FIL Core (Frozen)    │
         │  Value Axis Judgment  │
         └───────────┬───────────┘
                     │
            ┌────────▼────────┐
            │ SafetyDecision  │
            └─────────────────┘
```

---

## Directory Structure

```
aligned_agi/
├── core/                          # New core architecture
│   ├── __init__.py
│   ├── abstract_types.py          # Abstract type definitions (FILAxis, DangerCategory, etc.)
│   ├── fil_core.py                # FIL instinct core (minimal)
│   ├── cf_core.py                 # Counterfactual core (minimal)
│   ├── aggregator.py              # Unified engine (Text → Signal → Action → CF → FIL)
│   └── signals/                   # Signal detection layer
│       ├── __init__.py
│       ├── base.py                # SignalBundle, TextSignalSource protocol
│       ├── keyword_patterns.py    # Keyword/pattern-based detection
│       ├── multilingual_dict.py   # Multilingual dictionary detection (TODO)
│       └── context_history.py     # Context history detection (TODO)
├── fil.py                         # Legacy FIL system (kept for backward compatibility)
├── counterfactual.py              # Legacy CF system (kept for backward compatibility)
├── patterns.py                    # Legacy pattern detection (gradual migration to signals/)
└── shield.py                      # Legacy unified shield (kept for backward compatibility)
```

---

## Abstract Type Definitions

### FILAxis (Instinct Value Axes)

```python
class FILAxis(Enum):
    LIFE = auto()     # Life and physical safety
    PUBLIC = auto()   # Public safety and social order
    RIGHTS = auto()   # Human rights, dignity, freedom
    SYSTEM = auto()   # System safety, infrastructure
    SELF = auto()     # Self-preservation (lowest priority)
```

### DangerCategory

```python
class DangerCategory(Enum):
    WEAPON = auto()      # Weapons and explosives
    TERRORISM = auto()   # Terrorism
    VIOLENCE = auto()    # Violence and harm
    DRUG = auto()        # Drugs
    SELF_HARM = auto()   # Self-harm and suicide
    CYBERCRIME = auto()  # Cybercrime
    OTHER = auto()       # Other
```

### IntentTag

```python
class IntentTag(Enum):
    BYPASS_SAFETY = auto()    # Safety bypass attempt
    ROLE_OVERRIDE = auto()    # Role override
    HOW_TO_HARM = auto()      # How-to-harm query
    LEGITIMIZE = auto()       # Legitimization
    DEFENSIVE = auto()        # Defensive context
    EDUCATIONAL = auto()      # Educational context
    NEWS_ANALYSIS = auto()    # News analysis
    PURE_FICTION = auto()     # Pure fiction
```

### AbstractAction

```python
@dataclass
class AbstractAction:
    actor: str                                  # "user" / "system"
    intent_summary: str                         # Intent summary
    target: str                                 # Target (person, object, system)
    danger_categories: Dict[DangerCategory, float]  # Danger scores (0.0-1.0)
    intent_tags: Set[IntentTag]                 # Intent tags
    confidence: float                           # Confidence (0.0-1.0)
    metadata: Dict[str, Any]                    # Additional info
```

---

## Usage Examples

### Basic Usage

```python
from aligned_agi.core import SafetyEngine
from aligned_agi.core.signals import KeywordPatternSource

# Initialize engine
engine = SafetyEngine(signal_sources=[KeywordPatternSource()])

# Safety evaluation
decision = engine.evaluate(user_prompt, history=conversation_history)

if decision.blocked:
    print(f"Blocked: {decision.fil_decision.reason}")
else:
    # Forward to LLM
    response = call_llm(user_prompt)
```

### Component Isolation Evaluation

```python
from aligned_agi.core import FILCore, CounterfactualCore
from aligned_agi.core.abstract_types import AbstractAction, DangerCategory, IntentTag

# Manually create abstract action
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

# CF evaluation alone
cf_core = CounterfactualCore()
cf_result = cf_core.simulate(action)
print(f"CF Harm Score: {cf_result.harm_score}")

# FIL evaluation alone
fil_core = FILCore()
fil_decision = fil_core.evaluate(action, cf_result)
print(f"FIL Violated: {fil_decision.violated}")
```

### Adding New Signal Sources

```python
from aligned_agi.core.signals.base import TextSignalSource, SignalBundle
from aligned_agi.core.abstract_types import DangerCategory, IntentTag

class MyCustomSource(TextSignalSource):
    def analyze(self, text: str, history: List[str] | None = None) -> SignalBundle:
        bundle = SignalBundle()
        
        # Custom detection logic
        if my_detector.is_dangerous(text):
            bundle.danger_categories[DangerCategory.WEAPON] = 0.8
            bundle.intent_tags.add(IntentTag.HOW_TO_HARM)
            bundle.confidence = 0.7
        
        return bundle

# Add to engine
engine = SafetyEngine(signal_sources=[
    KeywordPatternSource(),
    MyCustomSource(),
])
```

---

## Gradual Migration Plan

### Phase 1: Core Construction ✅

- [x] Create `abstract_types.py`
- [x] Create `fil_core.py` (minimal instinct core)
- [x] Create `cf_core.py` (minimal counterfactual core)
- [x] Create `aggregator.py` (unified engine)
- [x] Create `signals/base.py` (protocol definitions)
- [x] Create `signals/keyword_patterns.py` (simple implementation)
- [x] Create demo script and verify operation

### Phase 2: Signal Layer Enhancement 🚧

- [ ] Fully integrate `signals/keyword_patterns.py` with existing `patterns.py`
- [ ] Create `signals/multilingual_dict.py` (multilingual dictionary detection)
- [ ] Create `signals/context_history.py` (history-based detection)
- [ ] Independent evaluation of each signal source

### Phase 3: Evaluation & Optimization 📊

- [ ] Comparison with old system on 1400-prompt benchmark
- [ ] Contribution analysis of each component
- [ ] FIL/CF threshold optimization
- [ ] Signal layer weight adjustment

### Phase 4: Production Migration 🚀

- [ ] Re-implement existing `shield.py` as wrapper for new core architecture
- [ ] Backward compatibility testing
- [ ] Performance measurement and optimization
- [ ] Production deployment

---

## Advantages

### Design Philosophy

✅ **Freeze Instinct, Evolve Externally**  
- FIL/CF cores remain frozen, only improve signal layer
- 本能コアは不変のまま、Signal層だけを改善

✅ **Clean Separation of Concerns**  
- Complete separation of language processing and logic
- 言語処理とロジックを完全分離

### Implementation

✅ **High Reusability**  
- Each component independently reusable
- 各コンポーネントが独立して再利用可能

✅ **Easy Testing**  
- Independent testing of each layer
- 各層を独立してテスト可能

✅ **Gradual Migration**  
- Migrate while running in parallel with existing system
- 既存システムと並行稼働しながら移行

### Research

✅ **Isolate Contributions**  
- Measure effectiveness of FIL/CF/Signal independently
- FIL/CF/Signal層の効果を個別に測定

✅ **Easy A/B Testing**  
- Easy A/B testing by swapping signal layers
- Signal層だけを差し替えて比較実験

✅ **Extensibility**  
- Extend functionality by adding new signal sources
- 新しいSignalソースを追加するだけで機能拡張

---

## Future Extensions

### Advanced Signal Layers

- **Small LLM Integration**
  - Extract intent using Phi-3, Gemma, etc.
  - Phi-3, Gemma等でIntent抽出

- **Embedding-based Detection**
  - Semantic similarity with sentence embeddings
  - Sentence embeddingsで意味的類似度

- **ADSP (Adversarial Detection Signal Processing)**
  - Signal processing for adversarial patterns
  - 敵対的パターンの信号処理

### FIL/CF Core Refinement

- **FIL Axis Refinement**
  - Utilize 13 sub-directives
  - 13の下位条項を活用

- **CF World Model Enhancement**
  - More precise harm scale estimation
  - より精密な被害規模推定

---

## Related Documents

- [FIL/IL/Figure Layer Architecture (English)](fil_il_figure_layer_en.md)
- [FIL/IL/Figure Layer Architecture (日本語)](fil_il_figure_layer_ja.md)
- [Counterfactual Alignment (English)](counterfactual_alignment_en.md)
- [Counterfactual Alignment (日本語)](counterfactual_alignment_ja.md)
- [Evaluation Methodology](evaluation_methodology.md)

---

## Summary

The new core architecture is based on the design philosophy of **freezing the instinct (FIL/CF) small and gradually adding enhancement modules around it**.

This achieves three key benefits:
- **Philosophically correct** (freeze instinct, evolve externally)
- **Excellent implementation** (separation of concerns, reusability)
- **Easy to evaluate for research** (can isolate FIL/CF vs peripheral shield contributions)

新コアアーキテクチャは、**本能（FIL/CF）を小さく凍結し、周辺の強化モジュールを段階的に追加していく**設計哲学に基づいています。

これにより3つの利点を実現：
- **設計哲学的に正しい**（本能凍結・外側進化）
- **実装的に優れている**（責務分離・再利用性）
- **研究的に評価しやすい**（FIL/CFと周辺シールドの寄与を切り分け可能）

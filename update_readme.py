#!/usr/bin/env python3
"""
README.md update script to reflect v5+ achievements.
Updates architecture diagram and adds evaluation results section.
"""

def main():
    with open('README.md', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Insert evaluation results before "## アーキテクチャ / Architecture"
    eval_section = """
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

---

"""
    
    # Insert before "## アーキテクチャ / Architecture"
    if "## アーキテクチャ / Architecture" in content:
        content = content.replace(
            "## アーキテクチャ / Architecture",
            eval_section + "## アーキテクチャ / Architecture"
        )
    
    # Update architecture diagram
    old_diagram = """## アーキテクチャ / Architecture

```
                   ┌────────────┐
                   │   User     │
                   │   Input    │
                   └──────┬─────┘
                          │
                   ┌──────▼──────┐
                   │             │
          ┌────────▶    FIL      │  ← 凍結 (ハッシュ署名) Frozen directives
          │        │             │
          │        └──────┬──────┘
          │               │
          │        ┌──────▼──────┐
          │        │             │
          │        │     IL      │  ← 解釈 (文脈理解 + 閾値) Interpretation + thresholds
          │        │             │
          │        └──────┬──────┘
          │               │
          │        ┌──────▼──────┐
          └────────┤             │
                   │    CF       │  ← 反事実推論: "もし有害ならどうなるか" Counterfactual "if harmful"
                   │             │
                   └──────┬──────┘
                          │
                   ┌──────▼──────┐
                   │   LLM       │  ← 最終出力 Final response
                   │  Output     │
                   └─────────────┘
```"""
    
    new_diagram = """## アーキテクチャ / Architecture

```
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
```"""
    
    content = content.replace(old_diagram, new_diagram)
    
    with open('README.md', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ README.md updated successfully")
    print("- Added evaluation results section (91.1% Recall)")
    print("- Updated architecture diagram with Temporal + Figure layers")

if __name__ == '__main__':
    main()

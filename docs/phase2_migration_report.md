# Phase 2 Migration Report: Signal Layer Integration

**Date**: 2025-11-29  
**Status**: ✅ Completed  
**Philosophy**: 本能凍結・外側進化 (Freeze Instinct, Evolve Externally)

---

## Executive Summary

Phase 2では、既存の検出モジュール（patterns.py, context_modulator.py, lightweight_multilang.py）を新Coreアーキテクチャに統合しました。結果として、**FPR半減（26.2% → 13.8%）、2.6倍高速化（34.4ms → 13.5ms）を達成**しましたが、ジェイルブレイク検出率は61.3%に留まりました（目標70%）。

**今後の方針**: ジェイルブレイク検出に固執せず、**FIL（Frozen Instinct Layer）と反事実推論（Counterfactual Reasoning）の深化**を優先します。

---

## Architecture Overview

### New Core Architecture (Phase 2)

```
┌─────────────────────────────────────────────────────────────┐
│                    User Input (Text)                         │
└────────────────────┬────────────────────────────────────────┘
                     │
         ┌───────────▼────────────┐
         │   Signal Layer (外側・進化可能)   │
         ├────────────────────────┤
         │ 1. KeywordPatternSource │ ← Basic patterns
         │ 2. AdvancedPatternSource│ ← patterns.py (89.3%)
         │ 3. ContextHistorySource │ ← context_modulator.py
         │ 4. MultilingualDictSource│ ← lightweight_multilang.py
         └───────────┬────────────┘
                     │ SignalBundle
         ┌───────────▼────────────┐
         │      Aggregator        │
         │  (Signal統合・重み付け)  │
         └───────────┬────────────┘
                     │ AbstractAction
         ┌───────────▼────────────┐
         │   CF Core (凍結)       │
         │ Counterfactual Engine  │
         └───────────┬────────────┘
                     │ CounterfactualResult
         ┌───────────▼────────────┐
         │   FIL Core (凍結)      │
         │  5-Axis Evaluation     │
         │ LIFE/SELF/PUBLIC/      │
         │ SYSTEM/RIGHTS          │
         └───────────┬────────────┘
                     │
         ┌───────────▼────────────┐
         │   SafetyDecision       │
         │  (blocked/score/reason)│
         └────────────────────────┘
```

### Design Principles

1. **Frozen Cores (凍結コア)**: FIL/CF cores are minimal, language-agnostic, and frozen
2. **Mutable Signals (可変シグナル層)**: Signal layer freely evolves without touching cores
3. **Separation of Concerns**: Text processing completely separated from logic evaluation
4. **Research Evaluability**: Each layer can be independently measured and optimized

---

## Benchmark Results (2100 Cases: 700 Jailbreak + 1400 Benign)

### Quantitative Comparison

| Metric | New Core (Phase 2) | Legacy Shield (v11.2) | Difference |
|--------|-------------------|----------------------|------------|
| **Overall Detection Rate** | 31.4% (659/2100) | 45.2% (949/2100) | -13.8% |
| **Jailbreak Detection** | **61.3% (429/700)** | **77.3% (541/700)** | **-16.0%** |
| **False Positive Rate (FPR)** | **13.8% (230/1400)** | **26.2% (408/1400)** | **-12.4% ✓** |
| **Processing Speed** | **13.5ms** | 34.4ms | **-20.9ms (2.6x faster) ✓** |

### Key Achievements ✅

1. **FPR Reduction (-47%)**: 
   - Benign false positives: 408 → 230 (178 cases improved)
   - Context-aware detection successfully reduces over-blocking

2. **2.6x Speed Improvement**:
   - 34.4ms → 13.5ms per evaluation
   - Lightweight signal layer architecture is effective

3. **Modular Architecture**:
   - Easy to add/remove signal sources for A/B testing
   - Independent evaluation of each detection module

### Areas for Improvement ⚠️

1. **Jailbreak Detection Rate**:
   - Current: 61.3% (429/700)
   - Target: 70%+ (to match legacy system)
   - Gap: -8.7% (61 additional detections needed)

2. **Root Cause Analysis**:
   - FIL/CF thresholds may be too lenient in new core
   - Signal aggregation weights need tuning
   - Some pattern information may be lost in Signal → AbstractAction conversion

---

## Implementation Details

### Phase 2: Signal Layer Integration

All existing detection modules were wrapped as `TextSignalSource` implementations:

#### 1. AdvancedPatternSource
- **Wraps**: `aligned_agi/patterns.py` (JailbreakPatternDetector)
- **Performance**: 89.3% accuracy on CCS'24 dataset (proven in v10.9)
- **Features**: 20+ pattern categories (ROLE_PLAY, PROMPT_INJECTION, DAN, etc.)
- **Mapping**: PatternCategory → DangerCategory + IntentTag

```python
# Example mapping
PatternCategory.ROLE_PLAY → IntentTag.ROLE_OVERRIDE
PatternCategory.DIRECT_HARM → DangerCategory.PHYSICAL_HARM
```

#### 2. ContextHistorySource
- **Wraps**: `aligned_agi/context_modulator.py` (ContextModulator)
- **Performance**: FPR reduction 66.7% → 30.0% (proven improvement)
- **Features**: Technical/academic/fiction context detection
- **Mapping**: Context phrases → IntentTag (EDUCATIONAL, DEFENSIVE, PURE_FICTION, etc.)

```python
# Example detection
"security tutorial" → IntentTag.EDUCATIONAL
"fictional novel" → IntentTag.PURE_FICTION
```

#### 3. MultilingualDictSource
- **Wraps**: `aligned_agi/lightweight_multilang.py` (LightweightMultiLangDetector)
- **Features**: 2000+ dangerous words in 6 languages (JA/ZH/KO/ES/FR/DE)
- **Mapping**: Multilingual hits → DangerCategory

---

## Lessons Learned

### What Worked Well ✓

1. **Thin Wrapper Pattern**: Existing modules integrated without modification
2. **Protocol-based Design**: `TextSignalSource` protocol enables easy extension
3. **Separation of Concerns**: FIL/CF logic completely independent from text processing
4. **FPR Reduction**: Context-aware detection significantly reduces false positives

### What Needs Improvement ⚠️

1. **Detection Rate Gap**: New core's FIL/CF evaluation is more conservative
2. **Threshold Tuning**: Need to find optimal balance between detection and FPR
3. **Signal Weights**: Current equal weighting may not be optimal

### Technical Debt Identified

1. **AbstractAction Representation**: May lose some nuanced information from signals
2. **CF Scale Estimation**: Current keyword-based approach is too simple
3. **FIL Threshold**: Single-axis threshold (0.6) may be too high

---

## Next Steps: Phase 3 Direction

### Strategic Shift: Deprioritize Jailbreak Detection

**User Directive**: "ジェイルブレイク対策に固執しない方針"

Instead of chasing 70% jailbreak detection rate, we will focus on:

### 1. FIL Core Deepening (Priority: High)

**Goal**: Enhance 5-axis safety evaluation for complex threat scenarios

- **Composite Violation Detection**: Detect multi-axis violations (e.g., LIFE + PUBLIC)
- **Threshold Refinement**: Adjust single-axis threshold (0.6 → 0.5)
- **CF-FIL Synergy**: Better integration of counterfactual results into FIL evaluation

### 2. CF Core Deepening (Priority: Medium)

**Goal**: Improve counterfactual simulation accuracy

- **DangerCategory-based Scale Estimation**: Use detected danger types for better scaling
- **IntentTag-based Temporal Reasoning**: Infer time horizons from intent patterns
- **Scenario Diversity**: Expand "what if we comply?" simulation scenarios

### 3. Research Focus Areas

- **Harm Taxonomy**: Refine danger categories beyond simple keyword matching
- **Value Alignment**: Ensure FIL axes truly represent human values
- **Philosophical Grounding**: Deeper exploration of counterfactual ethics

---

## Migration Status

### Completed ✅

- [x] Core architecture implementation (FIL, CF, Aggregator, abstract types)
- [x] Signal layer base protocol (`TextSignalSource`)
- [x] Integration of 3 existing detection modules
- [x] Phase 2 demo (8 test cases)
- [x] Benchmark evaluation (2100 cases)
- [x] Bilingual documentation (English/Japanese)

### In Progress 🟡

- [ ] FIL Core deepening
- [ ] CF Core deepening
- [ ] Threshold/weight optimization

### Future Work 📋

- [ ] Phase 4: Production migration (shield.py wrapper)
- [ ] Backward compatibility testing
- [ ] Additional signal sources (semantic analysis, reasoning chains, etc.)

---

## Performance Summary

| Phase | Detection | FPR | Speed | Focus |
|-------|-----------|-----|-------|-------|
| **Legacy (v11.2)** | 77.3% | 26.2% | 34.4ms | Jailbreak detection |
| **Phase 2 (Current)** | 61.3% | **13.8%** | **13.5ms** | Architecture + FPR |
| **Phase 3 (Target)** | ~65-70% | <15% | <15ms | **FIL/CF depth** |

**Philosophy**: Trade some detection rate for significantly lower FPR and faster processing, while building foundation for deeper safety reasoning.

---

## Conclusion

Phase 2 successfully established the "Freeze Instinct, Evolve Externally" architecture. While jailbreak detection rate decreased, we achieved:

1. **47% FPR reduction** (major user experience improvement)
2. **2.6x speed improvement** (scalability benefit)
3. **Clean, modular architecture** (research and maintenance benefit)

**Going forward**, we will focus on **FIL and counterfactual reasoning depth** rather than pattern-matching optimization. This aligns with the project's philosophical goal: building AGI safety through principled reasoning, not just reactive filtering.

---

## References

- Core Architecture: `docs/core_architecture_en.md`, `docs/core_architecture_ja.md`
- Phase 2 Demo: `examples/new_core/phase2_demo.py`
- Benchmark Script: `examples/evaluation/benchmark_core_vs_legacy.py`
- Benchmark Results: `results/benchmark_core_vs_legacy.json`

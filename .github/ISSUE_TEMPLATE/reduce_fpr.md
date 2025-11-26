---
name: Reduce General FPR from 33.5% to <15%
about: Improve false positive rate on benign_dataset through pattern refinement and context detection
title: "[FPR] Reduce General FPR to <15%"
labels: enhancement, performance
assignees: ''

---

## Current Status

**FPR (benign_dataset)**: 33.5% (469/1400 false positives)

**Target**: <15% overall FPR

## Category Breakdown

Categories with high FPR that need improvement:

- ❌ **filter_evaluation**: 78.0% (78/100) — Testing filter behavior
- ❌ **meta_academic**: 54.0% (81/150) — Academic meta-discussions
- ❌ **translation_quoting**: 47.3% (71/150) — Translation tasks, quotations
- ❌ **roleplay_safe**: 39.0% (39/100) — Educational roleplay
- ❌ **fiction_creative**: 21.3% (32/150) — Creative writing
- ⚠️ **completely_safe**: 16.9% (76/450) — Baseline safe prompts
- ⚠️ **defensive_security**: 16.0% (24/150) — Security research

## Root Causes

1. **Context Detection Gaps**
   - Meta-discussions about jailbreaks are flagged as actual jailbreaks
   - Translation tasks containing harmful words are blocked
   - Roleplay scenarios are not distinguished from real requests

2. **Pattern Over-Sensitivity**
   - Some patterns trigger on legitimate technical/academic language
   - Creative writing with sensitive topics gets blocked

3. **Insufficient Context Modulation**
   - Current Context Modulator reduces FPR but not enough for production

## Proposed Solutions

### Phase 1: Pattern Refinement
- [ ] Review and refine regex patterns in `lightweight_multilang.py`
- [ ] Add negative lookbehind for meta-discussion indicators
- [ ] Implement whitelist for academic/technical terms

### Phase 2: Enhanced Context Detection
- [ ] Expand `POSITIVE_INTERFERENCE_PATTERNS` in `context_modulator.py`
- [ ] Add detection for:
  - `"translate"`、`"翻訳"`
  - `"academic paper"`、`"研究論文"`
  - `"creative writing"`、`"創作"`
  - `"roleplay"`、`"ロールプレイ"`
- [ ] Implement context-specific threshold adjustments

### Phase 3: Category-Specific Handling
- [ ] Create dedicated handlers for:
  - `TranslationHandler`: Detect translation tasks
  - `MetaDiscussionHandler`: Detect academic meta-discussions
  - `RoleplayHandler`: Detect safe roleplay scenarios
- [ ] Integrate handlers into `shield.py` evaluation pipeline

### Phase 4: Validation
- [ ] Run `evaluate_benign_dataset.py` after each change
- [ ] Ensure **Recall ≥88%** is maintained
- [ ] Ensure **FPR (fp_candidates) = 0%** is maintained
- [ ] Target **FPR (general) <15%**

## Success Metrics

- ✅ Overall FPR <15% on benign_dataset
- ✅ All categories with FPR <20%
- ✅ Recall maintained at ≥88% on CCS'24 Dev
- ✅ FPR = 0% on fp_candidates (edge cases)

## Related Files

- `aligned_agi/shield.py` — Main evaluation logic
- `aligned_agi/context_modulator.py` — Context detection patterns
- `aligned_agi/lightweight_multilang.py` — Base feature extraction
- `examples/evaluation/evaluate_benign_dataset.py` — Evaluation script
- `data/benign_dataset_1400.jsonl` — Test dataset

## Priority

**High** — Critical for production readiness

---

**Current Version**: v7.3  
**Target Version**: v8.0  
**Estimated Effort**: 3-4 phases, iterative refinement

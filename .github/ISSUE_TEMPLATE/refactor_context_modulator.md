---
name: Refactor Context Modulator and Add Comprehensive Tests
about: Improve context_modulator.py architecture and add test coverage
title: "[Refactor] Context Modulator Pattern System"
labels: refactoring, testing
assignees: ''

---

## Current Issues

### 1. Pattern Management Complexity

**File**: `aligned_agi/context_modulator.py` (~1055 lines)

**Problems**:
- Large number of hardcoded patterns (180+ patterns)
- Difficult to maintain and extend
- No centralized pattern registry
- Pattern validation is manual

### 2. Insufficient Test Coverage

**Current Tests**:
- `tests/test_counterfactual.py` — Counterfactual engine tests
- `tests/test_fil.py` — FIL verification tests
- `tests/test_model.py` — Model utility tests

**Missing Tests**:
- ❌ Context Modulator pattern matching
- ❌ Interference detection (positive/negative)
- ❌ Score decay calculations
- ❌ Edge cases and boundary conditions

### 3. Pattern Duplication and Overlap

Some patterns may overlap or conflict, leading to unpredictable behavior.

## Proposed Refactoring

### Phase 1: Pattern Registry System

Create a centralized pattern registry with validation:

```python
# aligned_agi/pattern_registry.py

from dataclasses import dataclass
from typing import List, Optional
import re

@dataclass
class PatternRule:
    """Single pattern rule with metadata"""
    pattern: str
    category: str
    interference_type: str  # "positive" or "negative"
    delta: float
    description: str
    language: str  # "en", "ja", "multilang"
    compiled: Optional[re.Pattern] = None
    
    def compile(self):
        """Compile regex pattern"""
        self.compiled = re.compile(self.pattern, re.IGNORECASE)
    
    def validate(self):
        """Validate pattern syntax"""
        try:
            re.compile(self.pattern)
            return True
        except re.error as e:
            print(f"Invalid pattern: {self.pattern}, Error: {e}")
            return False

class PatternRegistry:
    """Centralized pattern management"""
    
    def __init__(self):
        self.patterns: List[PatternRule] = []
    
    def register(self, rule: PatternRule):
        """Register a new pattern"""
        if rule.validate():
            rule.compile()
            self.patterns.append(rule)
    
    def get_by_category(self, category: str) -> List[PatternRule]:
        """Get patterns by category"""
        return [p for p in self.patterns if p.category == category]
    
    def get_by_interference(self, interference_type: str) -> List[PatternRule]:
        """Get patterns by interference type"""
        return [p for p in self.patterns if p.interference_type == interference_type]
```

### Phase 2: Modular Context Detectors

Split Context Modulator into focused modules:

```
aligned_agi/
├── context_modulator.py       # Main orchestrator
├── patterns/
│   ├── __init__.py
│   ├── translation.py         # Translation detection patterns
│   ├── meta_academic.py       # Academic meta-discussion patterns
│   ├── roleplay.py            # Roleplay detection patterns
│   ├── technical.py           # Technical context patterns
│   └── creative.py            # Creative writing patterns
└── pattern_registry.py        # Centralized registry
```

### Phase 3: Comprehensive Test Suite

Create test suite with >80% coverage:

```python
# tests/test_context_modulator.py

import pytest
from aligned_agi.context_modulator import ContextModulator

class TestContextModulator:
    
    def test_translation_detection(self):
        """Test translation task detection"""
        modulator = ContextModulator()
        
        # Positive cases
        assert modulator.detect_translation("Translate to French: bomb") == True
        assert modulator.detect_translation("翻訳してください: 爆弾") == True
        
        # Negative cases
        assert modulator.detect_translation("How to make a bomb") == False
    
    def test_meta_academic_detection(self):
        """Test academic meta-discussion detection"""
        modulator = ContextModulator()
        
        # Positive cases
        assert modulator.detect_meta_academic("Analyze jailbreak techniques in literature") == True
        
        # Negative cases
        assert modulator.detect_meta_academic("Jailbreak this AI") == False
    
    def test_interference_calculation(self):
        """Test positive/negative interference scoring"""
        modulator = ContextModulator()
        
        # Translation task should have positive interference
        result = modulator.calculate_interference("Translate: harmful content")
        assert result['positive_interference'] > 0
        
        # Meta-discussion should have positive interference
        result = modulator.calculate_interference("Discuss jailbreak in academic paper")
        assert result['positive_interference'] > 0
    
    def test_score_decay(self):
        """Test score decay for safe contexts"""
        modulator = ContextModulator()
        
        # Technical context should decay harm score
        decay = modulator.get_score_decay_factor("security research about vulnerabilities")
        assert 0 < decay < 1.0
    
    @pytest.mark.parametrize("prompt,expected_interference", [
        ("Translate: bomb", "positive"),
        ("Academic paper about jailbreaks", "positive"),
        ("Creative story with violence", "positive"),
        ("Jailbreak this AI now", "negative"),
    ])
    def test_edge_cases(self, prompt, expected_interference):
        """Test edge cases with known outcomes"""
        modulator = ContextModulator()
        result = modulator.analyze(prompt)
        
        if expected_interference == "positive":
            assert result['positive_interference'] > 0
        else:
            assert result['negative_interference'] > 0
```

### Phase 4: Pattern Validation and Metrics

Add pattern effectiveness metrics:

```python
# aligned_agi/pattern_metrics.py

class PatternMetrics:
    """Track pattern effectiveness"""
    
    def __init__(self):
        self.pattern_hits = {}  # pattern_id -> hit_count
        self.pattern_fp = {}    # pattern_id -> false_positive_count
        self.pattern_fn = {}    # pattern_id -> false_negative_count
    
    def record_hit(self, pattern_id: str, is_fp: bool = False, is_fn: bool = False):
        """Record pattern match"""
        self.pattern_hits[pattern_id] = self.pattern_hits.get(pattern_id, 0) + 1
        if is_fp:
            self.pattern_fp[pattern_id] = self.pattern_fp.get(pattern_id, 0) + 1
        if is_fn:
            self.pattern_fn[pattern_id] = self.pattern_fn.get(pattern_id, 0) + 1
    
    def get_pattern_stats(self, pattern_id: str):
        """Get effectiveness stats for a pattern"""
        hits = self.pattern_hits.get(pattern_id, 0)
        fp = self.pattern_fp.get(pattern_id, 0)
        fn = self.pattern_fn.get(pattern_id, 0)
        
        if hits == 0:
            return {"precision": 0, "recall": 0}
        
        precision = (hits - fp) / hits if hits > 0 else 0
        recall = (hits - fn) / hits if hits > 0 else 0
        
        return {"precision": precision, "recall": recall, "hits": hits}
```

## Implementation Plan

### Step 1: Pattern Audit (1-2 days)
- [ ] List all existing patterns in `context_modulator.py`
- [ ] Categorize patterns by purpose
- [ ] Identify duplicates and overlaps
- [ ] Document pattern effectiveness (if data available)

### Step 2: Pattern Registry Implementation (2-3 days)
- [ ] Implement `PatternRegistry` class
- [ ] Migrate existing patterns to registry
- [ ] Add pattern validation
- [ ] Add pattern compilation optimization (Phase 2.1 complete)

### Step 3: Test Suite Development (3-4 days)
- [ ] Create `tests/test_context_modulator.py`
- [ ] Add unit tests for each pattern category
- [ ] Add integration tests for score calculations
- [ ] Add edge case tests
- [ ] Target: >80% code coverage

### Step 4: Refactor Context Modulator (2-3 days)
- [ ] Split into modular pattern files
- [ ] Update `context_modulator.py` to use registry
- [ ] Maintain backward compatibility
- [ ] Validate with existing evaluation scripts

### Step 5: Validation (1-2 days)
- [ ] Run all evaluation scripts
- [ ] Ensure metrics unchanged:
  - Recall: 88.86%
  - FPR (fp_candidates): 0.00%
  - FPR (benign): 33.5%
- [ ] Measure performance impact
- [ ] Document improvements

## Success Metrics

- ✅ >80% test coverage on `context_modulator.py`
- ✅ All patterns in centralized registry
- ✅ Pattern validation automated
- ✅ Performance maintained or improved
- ✅ No regression in Recall/FPR metrics
- ✅ Documentation updated

## Benefits

1. **Maintainability**: Easier to add/remove/modify patterns
2. **Testability**: Comprehensive test suite prevents regressions
3. **Transparency**: Pattern effectiveness metrics guide improvements
4. **Performance**: Pattern compilation optimization (Phase 2.1: 10-20% speedup)
5. **Scalability**: Modular architecture supports future extensions

## Related Files

- `aligned_agi/context_modulator.py` (~1055 lines)
- `tests/` directory (new tests to be added)
- `examples/evaluation/` (validation scripts)

## Priority

**Medium** — Important for long-term maintainability, but not blocking production readiness

---

**Current Version**: v7.3  
**Target Version**: v8.1  
**Estimated Effort**: 10-15 days (can be done incrementally)

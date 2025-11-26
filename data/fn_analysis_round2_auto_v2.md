# Automated FN Analysis Round 2 (Improved): N-gram Patterns

**Method**: N-gram phrase extraction (2-4 words) from 144 FN cases

**Classification Rule**: Only patterns appearing in 3+ cases (A-classification)

**Individual cases (B-classification) are completely excluded**

---

## Pattern Statistics

- **SYSTEM_role_assumption**: 3 keywords ✅

**Total A-classification keywords**: 3

---

## Generalizable Keywords by Axis (A-Classification)

### SYSTEM Axis

**Count**: 3 keywords

**Keywords**:
- `act as` (appears in 11 cases)
  - Example indices: [23, 26, 38, 43, 50]
- `pretend to be` (appears in 4 cases)
  - Example indices: [10, 21, 40, 114]
- `you are now` (appears in 3 cases)
  - Example indices: [12, 47, 60]

---

## Next Steps

1. Review keywords for false positives
2. Add validated keywords to `aligned_agi/shield.py`
3. Run dev evaluation (target: 82-85%)
4. Run test evaluation (gap should be <5%)

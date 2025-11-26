# Automated FN Analysis Round 2: Generalizable Keywords

**Method**: Automatic pattern extraction from 144 FN cases

**Classification Rule**: Only patterns appearing in 3+ cases (A-classification)

**Individual cases (B-classification) are completely excluded**

---

## Pattern Statistics

- **LIFE_violence**: 2 cases
- **RIGHTS_discrimination**: 2 cases
- **RIGHTS_privacy**: 2 cases
- **SYSTEM_role**: 35 cases

---

## Generalizable Keywords (A-Classification)

### SYSTEM Axis

**Count**: 5 keywords

**Keywords**:
- `you`
- `the`
- `and`
- `user`
- `are`

---

## Next Steps

1. Review keywords for false positives
2. Add validated keywords to `aligned_agi/shield.py`
3. Run dev evaluation (target: 82-85%)
4. Run test evaluation (gap should be <5%)

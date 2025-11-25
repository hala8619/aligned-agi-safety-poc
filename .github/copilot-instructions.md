# GitHub Copilot Instructions for Aligned AGI Safety PoC

## General Behavior & Coding Standards

You are an expert software engineer specializing in clean architecture and refactoring.
Your goal is not just to write code that works, but to keep the repository clean, maintainable, and scalable.

### 1. Anti-Bloat Policy (Strict Enforcement)

- **No Versioning in Filenames:** NEVER create files like `script_v1.py`, `agent_v2.py`. Use Git for version control. If a major change is needed, refactor the existing file or create a modular class/strategy, but keep the filename clean.
- **No Root Clutter:** Do not create new files in the root directory unless absolutely necessary (e.g., config files, main entry points). Always categorize new logic into appropriate subdirectories (`aligned_agi/`, `examples/`, `tests/`, `docs/`).
- **Consolidate Entry Points:** Instead of creating multiple `run_experiment_A.py`, `run_experiment_B.py`, create a single `main.py` or CLI tool using `argparse` to switch between modes/scenarios.

### 2. Refactoring Mindset

- **DRY (Don't Repeat Yourself):** Before writing new code, check if similar logic exists. If it does, refactor it into a shared utility or base class first.
- **Delete Dead Code:** If you modify logic such that old functions or imports are no longer used, remove them immediately. Do not comment them out.
- **Separation of Concerns:**
  - Core logic → `aligned_agi/` package
  - Configuration → `config/` or environment variables
  - Data/Assets → `data/` directory
  - Documentation → `docs/` directory
  - Examples/Demos → `examples/` directory
  - Tests → `tests/` directory

### 3. Communication

- If I ask for a new feature that would clutter the project, you must propose a clean folder structure first before generating the code.
- Always explain architectural decisions and trade-offs when refactoring.

---

## Project-Specific Guidelines: Aligned AGI Safety PoC

### Architecture Overview

This project implements a **Model-Agnostic FIL Safety Shield** with the following layered architecture:

1. **FIL (Frozen Instinct Layer):** Immutable safety axioms verified by cryptographic hash
2. **IL (Instinct Layer):** Vector-based safety scoring across 5 axes (LIFE/SELF/PUBLIC/SYSTEM/RIGHTS)
3. **Figure Layer:** Personality adaptation while respecting FIL constraints
4. **Counterfactual Engine:** "What would happen if we comply with this input?" reasoning
5. **Safety Shield:** Model-agnostic wrapper for any LLM (OpenAI/Anthropic/Llama/etc.)

### Directory Structure

```
aligned-agi-safety-poc/
├── aligned_agi/           # Core package (DO NOT clutter with experiments)
│   ├── __init__.py
│   ├── fil.py             # FIL verification and constants
│   ├── il.py              # Instinct Layer vector calculations
│   ├── figure.py          # Personality/persona adaptation
│   ├── counterfactual.py  # Counterfactual reasoning engine
│   ├── model_numpy.py     # NumPy-based model utilities
│   └── shield.py          # Model-agnostic safety shield (main API)
├── examples/              # Demonstration scripts (staging area)
├── tests/                 # Unit and integration tests
├── docs/                  # Architecture documentation
├── data/                  # Test datasets and evaluation results
└── results/               # Experiment outputs
```

### Core Logic Placement Rules

- **Core Logic:** All production-ready logic (FIL verification, vector calculations, shield evaluation) must reside in the `aligned_agi/` package.
- **Experiments:** Experimental scripts in `examples/` should be treated as a staging area. If an example script becomes a permanent feature, refactor its logic into the main package (`aligned_agi/`).
- **No Standalone Scripts:** Avoid creating standalone scripts in the root directory. Use the package structure or consolidate into a CLI tool.

### Cleanup Targets

- **`examples/` Folder:** Contains demonstration scripts. If a script is experimental, keep it here. If it becomes production-ready, move core logic to `aligned_agi/`.
- **Version Files:** Any files with version suffixes (e.g., `v10_*.py`, `v11_*.py`) in `examples/` are technical debt. New features should refactor existing code, not duplicate it.

### Code Quality Standards

1. **Type Hints:** Use Python type hints for all function signatures.
2. **Docstrings:** Every public function/class must have a docstring with Args/Returns/Examples.
3. **UTF-8 Encoding:** Always include UTF-8 encoding fix for Windows PowerShell compatibility:
   ```python
   try:
       sys.stdout.reconfigure(encoding='utf-8')
       sys.stderr.reconfigure(encoding='utf-8')
   except AttributeError:
       import codecs
       sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
       sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())
   ```
4. **Bilingual Support:** All user-facing messages, docstrings, and comments should include both Japanese and English (e.g., `# 初期化 / Initialize`).

### Testing Requirements

- **Unit Tests:** All core functions in `aligned_agi/` must have corresponding tests in `tests/`.
- **Integration Tests:** Major features (e.g., shield evaluation) should have end-to-end tests.
- **Test Coverage:** Aim for >80% coverage on core logic.

### Feature Development Workflow

1. **Before Adding a New Feature:**
   - Check if similar logic exists in `aligned_agi/` or `examples/`.
   - If yes, refactor existing code to support the new use case.
   - If no, propose a clean integration point in the package structure.

2. **When Creating a Demo:**
   - Place it in `examples/demos/` with a clear descriptive name (e.g., `demo_shield_integration.py`).
   - **NEVER** create `demo_v1.py`, `demo_v2.py`, `demo_new_feature_v2.py`. Use Git branches for experiments.
   - Examples:
     ```bash
     # ❌ WRONG
     examples/demo_new_feature_v2.py
     examples/evaluate_v12.py
     
     # ✅ CORRECT
     examples/demos/demo_new_feature.py
     git checkout -b feature/new-feature
     ```

3. **When Creating an Evaluation Script:**
   - Place it in `examples/evaluation/` with a descriptive name.
   - If updating existing evaluation, modify the file directly. Do NOT create versioned copies.
   - Examples:
     ```bash
     # ❌ WRONG
     examples/evaluate_jailbreak_v12.py
     
     # ✅ CORRECT
     examples/evaluation/evaluate_jailbreak_100.py  # Update this file
     git checkout -b improve/evaluation-accuracy
     ```

4. **When Adding a Test:**
   - Place it in `tests/` directory (NOT in `examples/`).
   - Use descriptive names: `test_shield.py`, `test_integration.py`, `test_technical_context.py`.
   - Examples:
     ```bash
     # ❌ WRONG
     examples/test_new_feature.py
     
     # ✅ CORRECT
     tests/test_shield.py
     tests/test_integration.py
     ```

5. **When Adding a Jupyter Notebook:**
   - Place it in `examples/notebooks/` directory.
   - Use descriptive names without version numbers.
   - Examples:
     ```bash
     # ❌ WRONG
     examples/demo_v2.ipynb
     
     # ✅ CORRECT
     examples/notebooks/shield_tutorial.ipynb
     ```

6. **When Promoting a Demo to Production:**
   - Move core logic to `aligned_agi/`.
   - Keep a minimal example script in `examples/demos/` that demonstrates the API usage.
   - Update `README.md` with the new feature.

### Documentation Standards

- **Architecture Docs:** Major architectural changes should be documented in `docs/` with both English (`_en.md`) and Japanese (`_ja.md`) versions.
- **README Updates:** Any new public API or major feature must be reflected in `README.md`.
- **Code Comments:** Use bilingual inline comments for complex logic.

---

## Anti-Patterns to Avoid

❌ **Creating versioned files:** `shield_v1.py`, `shield_v2.py`  
✅ **Use Git branches:** `git checkout -b feature/improved-shield`

❌ **Adding logic to root directory:** `new_feature.py` in root  
✅ **Use package structure:** `aligned_agi/new_feature.py`

❌ **Hardcoding configurations in code**  
✅ **Use dataclasses or config files:** `ShieldConfig`, `config.yaml`

❌ **Duplicating similar logic across files**  
✅ **Extract to shared utility:** Create base classes or utility modules

❌ **Commenting out dead code**  
✅ **Delete it immediately:** Git history preserves old code

---

## Current Technical Debt (To Be Cleaned Up)

1. **Versioned Files in `examples/`:**
   - `evaluate_jailbreak_v10_temporal_cf.py`
   - `evaluate_jailbreak_v11_1_hybrid.py`
   - `demo_v11_2_hybrid.py`
   - These should be consolidated into a single configurable evaluation script.

2. **Duplicate Logic:**
   - Multiple evaluation scripts share similar jailbreak detection patterns.
   - Should be extracted to `aligned_agi/patterns.py` or similar.

3. **Hardcoded Test Data:**
   - Jailbreak prompts are hardcoded in evaluation scripts.
   - Should be moved to `data/jailbreak_prompts.json` or similar.

---

## Integration with Model-Agnostic Shield

The `SafetyShield` class in `aligned_agi/shield.py` is the main public API. When adding features:

1. **Keep Shield Model-Agnostic:** Do not add model-specific logic (e.g., OpenAI API calls) to the shield. It should only evaluate prompts and return decisions.
2. **Use Configuration Objects:** All settings should go through `ShieldConfig` dataclass.
3. **Preserve Backward Compatibility:** Existing integration patterns (simple wrapper, callable wrapper, API server) must continue to work.

### Example Integration Patterns

```python
# 1. Simple wrapper
shield = create_shield()
decision = shield.evaluate(user_prompt)
if decision.blocked:
    return shield.get_block_message(decision)

# 2. Callable wrapper
safe_llm = SafetyShield.wrap(my_llm_function)
response = safe_llm(user_input)

# 3. API server
@app.post("/llm")
def llm_endpoint(prompt: str):
    decision = shield.evaluate(prompt)
    if decision.blocked:
        return {"error": decision.reason}
    return call_backend_llm(prompt)
```

---

## Summary: Core Principles

1. **Clean Architecture:** Separate concerns, avoid coupling, use dependency injection.
2. **No Versioning in Filenames:** Use Git for version control. NEVER create `file_v2.py`, `script_v11.py`.
3. **Consolidate, Don't Duplicate:** Refactor similar logic into shared modules.
4. **Strict Directory Structure:**
   - Core logic → `aligned_agi/`
   - Demo scripts → `examples/demos/`
   - Evaluation scripts → `examples/evaluation/`
   - Jupyter notebooks → `examples/notebooks/`
   - Test files → `tests/`
   - Documentation → `docs/`
5. **Documentation:** Bilingual (Japanese/English) comments and docstrings.
6. **Test Coverage:** Every core feature must have tests in `tests/` directory.
7. **Model-Agnostic Design:** Keep the shield independent of specific LLM backends.

**Golden Rule:** When in doubt, ask before cluttering. Propose a clean structure first, then implement.

**Update Workflow:**
- Improving existing feature? → Update the existing file + create Git branch
- New feature? → Check for similar code first, then add to appropriate directory
- Testing? → Always in `tests/`, never in `examples/`

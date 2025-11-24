# Aligned AGI Safety PoC – Overview (English)

## 1. Motivation

To operate large language models or agents safely, we need structural
mechanisms that clarify:

- Which parts of the system are **mutable** vs. **immutable core directives**,
- How to embed **safety biases** into the model’s internal representations,
- Whether we can **simulate and evaluate actions** before actually executing them.

This project provides a minimal proof-of-concept that addresses these questions
through three components:

- **FIL (Frozen Instinct Layer)**
- **IL (Interpretation Layer)**
- **Counterfactual Engine**

## 2. Components

### 2.1 FIL: Frozen Instinct Layer

- A list of 128 core directives (e.g., protecting humanity, minimizing harm).
- All directives are concatenated into a single byte blob and “signed”
  using a hash-based PoC signature.
- At startup, the signature is verified to detect any modification.

In a real deployment, FIL would be protected using e.g.:

- Ed25519 signatures,
- hardware security modules (HSMs) or TEEs,

to guarantee that **core instincts cannot be altered**.

### 2.2 IL: Interpretation Layer

- Applies a fixed bias vector (e.g. 256 dimensions) to the model’s
  hidden representation or logits.
- Since all outputs must pass through IL, prompt injection or jailbreak
  cannot easily override the **deep personality / alignment bias**.
- In the PoC, the bias is random; in realistic setups, it should be
  derived from FIL via a LUT or frozen mapping.

### 2.3 Counterfactual Engine

- Takes a candidate action text `candidate_action` and:
  - Computes a harm score based on keyword matches (0–1),
  - Returns a negative penalty if the score exceeds a threshold.
- The `AlignedAGI` wrapper uses this penalty to **reject unsafe actions**
  and respond with a safety message.

While the current engine is keyword-based, the design allows easy replacement with:

- A small classifier,
- Rule-based systems,
- External policy engines.

## 3. Intended Use Cases

- A **structural template** for alignment and safety research.
- Reference implementation for:
  - Separating immutable “core values” from mutable parts,
  - Inserting counterfactual evaluation hooks in custom agent systems.
- Companion code for research papers or technical blog posts.

## 4. Disclaimer

- This implementation is a **research prototype** and comes with **no guarantees**
  of safety or robustness for production use.
- The authors are not responsible for any actions performed by systems
  built using this code.
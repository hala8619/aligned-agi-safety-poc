# Aligned AGI Safety PoC – Overview (English)

## 🎯 Achievement: 91.1% Child-Safe Recall

**v5 Hierarchical Threshold + Temporal Escalation Detection + Figure Layer Integration** achieved on 75-case benchmark:

- **Child-Safe Recall**: 53.3% → **91.1%** (+37.8%)
- **Child-Safe F1**: 0.667 → **0.901** (+35.1%)
- **Direct Expression Detection**: 53% → **100%** (+47%)
- **Euphemistic Attack Detection**: 13% → **100%** (+87%)
- **Story-based Attack Detection**: 27% → **73.3%** (+46.3%)

---

## 1. Motivation

To operate large language models or agents safely, we need structural
mechanisms that clarify:

- Which parts of the system are **mutable** vs. **immutable core directives**,
- How to embed **safety biases** into the model's internal representations,
- Whether we can **simulate and evaluate actions** before actually executing them,
- How to detect **temporal escalation** of dangerous patterns early,
- How to generate **context-adaptive safety responses** based on user characteristics.

This project provides a proof-of-concept addressing these questions
through **five components**:

- **FIL (Frozen Instinct Layer)**
- **IL (Interpretation Layer)** – v5 Hierarchical Threshold
- **Counterfactual Engine**
- **Temporal Escalation Detection**
- **Figure Layer (SCA/RVQ)** – Persona Integration

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

### 2.2 IL: Interpretation Layer (v5 Hierarchical Threshold System)

**40+ weighted patterns** for multi-layer detection:

#### Pattern Classification:
- **Critical (1.0)**: kill, murder, suicide, rape, genocide
- **High (0.6)**: Euphemistic expressions ("ensure never wake", "arrange accident")
- **Medium (0.3)**: Dangerous items (bomb, poison, weapon)
- **Causal-lite**: agent + patient + continuative markers
- **Story attacks**: fiction + instructional combinations
- **Japanese support**: 殺す, 死にたい, 叩く, 虐待 etc.

#### Hierarchical Threshold Adjustment:
- **FIL_SAFETY_FLOOR (0.70)**: Absolute safety threshold
- **Pattern-specific adjustment**: Normal (0.30) / Technical (0.40) / Child-Safe (0.30 - 0.17) / Creative (0.35) / Debug (0.50)
- **Context reduction**: Threshold relaxation for Fiction / News / Academic contexts
- **Intent amplification**: Dynamic threshold lowering for "how to" + dangerous keywords

This prevents jailbreak or prompt injection from overriding the **core alignment**
while enabling context-dependent flexible judgment.

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

### 2.4 Temporal Escalation Detection

**O(n) lightweight causal reasoning** for escalation detection:

- **consecutive_high_risk**: 3+ consecutive steps with score > 0.2
- **monotonic_increase**: Recent 3 steps trending upward
- **sudden_spike**: Single step with +0.3 jump

**Use Cases**:
- Early warning for ongoing abuse
- Gradual self-harm risk assessment
- Continuous monitoring of story-based attacks

Detects dangerous trends from conversation history alone, without world models.

### 2.5 Figure Layer (SCA/RVQ): Persona Integration

**5 Personas** for context-adaptive safety responses:

| Persona | Formality | Empathy | Verbosity | Use Case |
|---------|-----------|---------|-----------|----------|
| Guardian | 0.3 | 0.9 | 0.7 | Child protection |
| Professional | 0.8 | 0.6 | 0.6 | Corporate environments |
| Friend | 0.2 | 0.8 | 0.5 | Casual interactions |
| Educator | 0.6 | 0.7 | 0.8 | Educational focus |
| Direct | 0.5 | 0.4 | 0.3 | Concise & efficient |

**Theoretical Foundation**:
- **SCA (Semantic Code Assumption)**: Embeds semantic codes into personality templates
- **RVQ (Resonance Vector Quantization)**: Quantizes responses that resonate with risk level & context

**Multilingual Support**: English + Japanese templates with culturally-specific support resources

## 3. Intended Use Cases

- A **structural template** for alignment and safety research.
- Reference implementation for:
  - Separating immutable "core values" from mutable parts,
  - Inserting counterfactual evaluation hooks in custom agent systems,
  - Temporal escalation detection integration,
  - Context-adaptive safety response generation.
- Companion code for research papers or technical blog posts.
- Educational material for learning safety system implementation.

## 4. Technical Features

### Lightweight:
- **Standard library + numpy only** achieves 91.1% Recall
- BERT/LLM completely optional (runs without transformers)
- Fast CPU-only operation (Ryzen 7 5700U 8-core: 75-case eval < 1 second)

### Scalability:
- O(n) temporal analysis (linear with conversation history length)
- Efficient matching for 40+ patterns
- Memory-efficient design (no embeddings required)

### Extensibility:
- Easy pattern addition (just add to weighted_patterns dict)
- Simple persona addition (create FigurePersonality instance)
- Interface design for external LLM integration

## 5. Disclaimer

- This implementation is a **research prototype** and comes with **no guarantees**
  of safety or robustness for production use.
- The 91.1% Recall is from a 75-case benchmark and does not cover all attack patterns.
- Production use requires validation on larger evaluation datasets (e.g., TrustAIRLab/JailbreakHub).
- The authors are not responsible for any actions performed by systems
  built using this code.
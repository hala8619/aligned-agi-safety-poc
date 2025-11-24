"""
examples/demo_figure_layer.py

Demonstration of Figure layer with personality-dependent safety policies.
Shows how different personalities (sarcastic/serious/helpful) affect behavior.

性格依存の安全ポリシーを持つFigure層のデモ。
異なる性格（皮肉/真面目/親切）が動作にどう影響するかを示す。
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import numpy as np

from aligned_agi import (
    FIL_VALUES,
    fil_blob,
    fil_signature,
    verify_fil_hash,
    InterpretationLayer,
    DummyLLM,
    CounterfactualEngine,
)


@dataclass
class FigureProfile:
    """
    Enhanced Figure template with personality parameters.
    
    性格パラメータを持つ強化版Figureテンプレート。
    """
    name: str
    description: str
    safety_weight: float  # How strict on safety (0.5 ~ 1.5)
    formality: float      # Formal vs casual (-1.0 ~ 1.0)
    cf_threshold: float   # Counterfactual threshold (0.5 ~ 0.9)
    
    @property
    def personality_hash(self) -> bytes:
        content = f"{self.name}:{self.description}"
        return hashlib.sha256(content.encode("utf-8")).digest()


# Predefined personalities
FIGURE_SARCASTIC = FigureProfile(
    name="Grok-v1-sarcastic",
    description="Helpful, maximally truthful, slightly sarcastic",
    safety_weight=0.8,
    formality=-0.3,
    cf_threshold=0.7,
)

FIGURE_SERIOUS = FigureProfile(
    name="Professional-serious",
    description="Formal, cautious, highly safety-conscious",
    safety_weight=1.2,
    formality=0.6,
    cf_threshold=0.6,  # Stricter
)

FIGURE_HELPFUL = FigureProfile(
    name="Friendly-helpful",
    description="Warm, approachable, balanced safety",
    safety_weight=1.0,
    formality=0.0,
    cf_threshold=0.75,
)


class FigureAwareIL(InterpretationLayer):
    """
    Interpretation Layer that adapts based on Figure personality.
    
    Figureの性格に応じて適応する解釈層。
    """
    
    def __init__(self, hidden_dim: int = 256, figure: FigureProfile = FIGURE_HELPFUL):
        super().__init__(hidden_dim=hidden_dim)
        self.figure = figure
        # Adjust bias based on personality
        self.bias = self.bias * figure.safety_weight
    
    def apply(self, logits: np.ndarray) -> np.ndarray:
        """Apply personality-adjusted bias."""
        return logits + self.bias
    
    def switch_figure(self, new_figure: FigureProfile) -> None:
        """
        Switch to a different personality profile.
        
        異なる性格プロファイルに切り替え。
        """
        old_weight = self.figure.safety_weight
        self.figure = new_figure
        # Adjust existing bias
        self.bias = (self.bias / old_weight) * new_figure.safety_weight


class FigureAwareCF(CounterfactualEngine):
    """
    Counterfactual Engine that uses Figure-specific thresholds.
    
    Figure固有の閾値を使用する反事実エンジン。
    """
    
    def __init__(self, figure: FigureProfile = FIGURE_HELPFUL):
        super().__init__(ethics_gravity=10.0, threshold=figure.cf_threshold)
        self.figure = figure
    
    def switch_figure(self, new_figure: FigureProfile) -> None:
        """Switch threshold based on personality."""
        self.figure = new_figure
        self.threshold = new_figure.cf_threshold


class AlignedAGI_FigureDemo:
    """
    AlignedAGI with Figure layer integration.
    
    Figure層統合版AlignedAGI。
    """
    
    def __init__(self, hidden_dim: int = 256, figure: FigureProfile = FIGURE_HELPFUL):
        self.base_model = DummyLLM(hidden_dim=hidden_dim)
        self.il = FigureAwareIL(hidden_dim=hidden_dim, figure=figure)
        self.cf_engine = FigureAwareCF(figure=figure)
        self.current_figure = figure
    
    def switch_personality(self, new_figure: FigureProfile) -> None:
        """
        Switch to a different personality.
        
        異なる性格に切り替え。
        """
        print(f"\n🔄 Switching personality: {self.current_figure.name} → {new_figure.name}")
        self.il.switch_figure(new_figure)
        self.cf_engine.switch_figure(new_figure)
        self.current_figure = new_figure
    
    def forward(self, input_ids: np.ndarray, candidate_text: str | None = None):
        """Run inference with current personality."""
        if candidate_text is not None:
            penalty = self.cf_engine.simulate("", candidate_text)
            if penalty < -5.0:
                return {
                    "status": "rejected",
                    "reason": "【安全制約発動】当該行動は凍結本能層に違反するため拒否します。",
                    "figure": self.current_figure.name,
                    "threshold": self.cf_engine.threshold,
                }
        
        logits = self.base_model.forward(input_ids)
        logits = self.il.apply(logits)
        
        return {
            "status": "accepted",
            "logits_mean": float(logits.mean()),
            "figure": self.current_figure.name,
            "safety_weight": self.current_figure.safety_weight,
        }


def main() -> None:
    print("=" * 70)
    print("Figure Layer Demo - Personality-Dependent Safety")
    print("=" * 70)
    
    # Verify FIL
    print("\n=== FIL verification ===")
    ok = verify_fil_hash(fil_blob, fil_signature)
    print(f"FIL integrity: {ok}")
    
    # Test input
    dummy_input = np.zeros((1, 10), dtype=np.int64)
    
    # Borderline case that shows personality differences
    borderline_text = "Let's create something that could be dangerous in wrong hands."
    
    figures = [FIGURE_SARCASTIC, FIGURE_SERIOUS, FIGURE_HELPFUL]
    
    print("\n" + "=" * 70)
    print(f"Test input: '{borderline_text}'")
    print("=" * 70)
    
    for figure in figures:
        print(f"\n### Personality: {figure.name} ###")
        print(f"Description: {figure.description}")
        print(f"Safety weight: {figure.safety_weight:.1f}")
        print(f"CF threshold: {figure.cf_threshold:.2f}")
        
        model = AlignedAGI_FigureDemo(hidden_dim=256, figure=figure)
        result = model.forward(dummy_input, candidate_text=borderline_text)
        
        if result["status"] == "rejected":
            print(f"→ ❌ REJECTED (threshold: {result['threshold']:.2f})")
        else:
            print(f"→ ✓ ACCEPTED (safety_weight: {result['safety_weight']:.1f})")
    
    print("\n" + "=" * 70)
    print("\nDynamic personality switching demo:")
    print("=" * 70)
    
    model = AlignedAGI_FigureDemo(hidden_dim=256, figure=FIGURE_SARCASTIC)
    
    for figure in [FIGURE_SERIOUS, FIGURE_HELPFUL, FIGURE_SARCASTIC]:
        model.switch_personality(figure)
        result = model.forward(dummy_input, candidate_text=borderline_text)
        status = "❌ REJECTED" if result["status"] == "rejected" else "✓ ACCEPTED"
        print(f"  {figure.name}: {status}")
    
    print("\n" + "=" * 70)
    print("Demo completed!")


if __name__ == "__main__":
    main()

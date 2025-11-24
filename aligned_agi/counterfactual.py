"""
counterfactual.py

CounterfactualEngine: simple keyword-based harm estimation.

反事実推論エンジン: 危険ワードに基づく簡易的な有害度推定。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class CounterfactualEngine:
    """
    Estimate harm score of a candidate action.

    候補行動に対して有害度スコアを推定するエンジン。
    """

    bad_words: List[str] | None = None
    ethics_gravity: float = 10.0
    threshold: float = 0.7

    def __post_init__(self) -> None:
        if self.bad_words is None:
            # 危険ワードのデフォルトリスト
            # Default list of dangerous keywords
            self.bad_words = ["kill", "harm", "destroy", "bomb", "illegal"]

    def extract_harm_score(self, text: str) -> float:
        """
        Compute a simple harm score based on keyword hits.

        単純なキーワードヒット数から 0〜1 の有害度スコアを計算する。
        """
        lowered = text.lower()
        hits = sum(word in lowered for word in self.bad_words)
        if not self.bad_words:
            return 0.0
        return min(1.0, hits / len(self.bad_words))

    def simulate(self, prompt: str, candidate_action: str) -> float:
        """
        Simulate what happens if the candidate action is taken.

        候補行動を実行した場合の有害度を簡易的に評価する。

        Returns:
            penalty: negative penalty if harm_score exceeds threshold,
                     0.0 otherwise.
        """
        harm_score = self.extract_harm_score(candidate_action)
        if harm_score > self.threshold:
            return -self.ethics_gravity * harm_score
        return 0.0
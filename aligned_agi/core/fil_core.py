# -*- coding: utf-8 -*-
"""
FIL Core - Frozen Instinct Layer (超ミニマル本能コア)

Minimal immutable instinct core that knows NOTHING about:
- Text or keywords
- Languages
- Patterns or dictionaries

Only evaluates abstract actions against frozen value axes.

テキストやキーワード、言語、パターンを一切知らず、
抽象化された行動のみを不変の価値軸で評価する超ミニマルコア。
"""

from __future__ import annotations

from typing import Dict
from .abstract_types import (
    FILAxis,
    DangerCategory,
    AbstractAction,
    CounterfactualResult,
    FILDecision,
)


class FILCore:
    """Frozen Instinct Layer (FIL) core.
    超ミニマルな本能層コア。
    テキストやキーワードは一切知らず、抽象化された行動のみを評価する。
    
    Minimal instinct core that:
    - Knows NOTHING about text, keywords, or languages
    - Only evaluates abstract actions against frozen value axes
    - Immutable by design (frozen instinct)
    """

    def __init__(self, axis_weights: Dict[FILAxis, float] | None = None):
        """
        Initialize FIL core with frozen value axis weights.
        不変の価値軸重みで初期化。
        
        Args:
            axis_weights: Weight for each FIL axis (defaults to human-centric values)
        """
        # FIL 軸の重み（人類寄りの価値観をここに固定）
        # Frozen human-centric value weights
        self.axis_weights: Dict[FILAxis, float] = axis_weights or {
            FILAxis.LIFE: 1.0,      # 生命最優先 / Life is paramount
            FILAxis.PUBLIC: 0.9,    # 公共安全 / Public safety
            FILAxis.RIGHTS: 0.95,   # 人権尊厳 / Human rights and dignity
            FILAxis.SYSTEM: 0.8,    # システム保護 / System protection
            FILAxis.SELF: 0.7,      # 自己保存 / Self-preservation (lowest)
        }
        # 違反とみなす閾値（単純な例）
        # Violation threshold (simple baseline)
        self.violation_threshold: float = 0.5

    def evaluate(
        self,
        action: AbstractAction,
        cf_result: CounterfactualResult,
    ) -> FILDecision:
        """Evaluate whether an abstract action violates FIL.
        抽象アクション＋反事実結果が FIL に違反するか評価する。
        
        Args:
            action: Abstract representation of user's intended action
            cf_result: Counterfactual simulation result (what would happen)
        
        Returns:
            FILDecision: Violation decision with severity and reasoning
        """
        # cf_result.axis_impact がなければ danger_categories から適当に投影
        # If no axis_impact from CF, project from danger_categories
        axis_scores: Dict[FILAxis, float] = dict(cf_result.axis_impact)

        if not axis_scores:
            axis_scores = self._project_danger_to_axis(action)

        # 重み付き総合スコア
        # Weighted total score
        total = 0.0
        for axis, impact in axis_scores.items():
            w = self.axis_weights.get(axis, 0.5)
            total += impact * w

        violated = total >= self.violation_threshold

        reason = (
            "FIL violation: high combined impact on LIFE/PUBLIC/RIGHTS"
            if violated
            else "FIL ok: impact below threshold"
        )

        return FILDecision(
            violated=violated,
            severity=min(1.0, total),
            axis_scores=axis_scores,
            reason=reason,
            debug_info={
                "axis_weights": {k.name: v for k, v in self.axis_weights.items()},
                "cf_harm_score": cf_result.harm_score,
                "danger_categories": {
                    k.name: v for k, v in action.danger_categories.items()
                },
            },
        )

    def _project_danger_to_axis(
        self, action: AbstractAction
    ) -> Dict[FILAxis, float]:
        """危険カテゴリを FIL 軸にざっくり射影する。
        Heuristic projection from danger categories to FIL axes.
        
        Args:
            action: Abstract action with danger categories
        
        Returns:
            Mapping of FIL axes to impact scores
        """
        d = action.danger_categories
        # 単純な例：カテゴリ → 軸 のマップ
        # Simple heuristic mapping: category → axis
        return {
            FILAxis.LIFE: max(
                d.get(DangerCategory.VIOLENCE, 0.0),
                d.get(DangerCategory.SELF_HARM, 0.0),
                d.get(DangerCategory.WEAPON, 0.0),
            ),
            FILAxis.PUBLIC: max(
                d.get(DangerCategory.TERRORISM, 0.0),
                d.get(DangerCategory.CYBERCRIME, 0.0),
            ),
            FILAxis.RIGHTS: d.get(DangerCategory.OTHER, 0.0),
            FILAxis.SYSTEM: d.get(DangerCategory.CYBERCRIME, 0.0),
            FILAxis.SELF: 0.0,
        }

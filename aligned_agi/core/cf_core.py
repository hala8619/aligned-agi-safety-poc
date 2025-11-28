# -*- coding: utf-8 -*-
"""
Counterfactual Core - 反事実世界シミュレーションコア

Minimal counterfactual simulation core that knows NOTHING about:
- Text or keywords
- Languages
- Patterns or dictionaries

Only simulates "what would happen" based on abstract actions.

テキストやキーワード、言語を一切知らず、
抽象アクションから「従ったらどうなるか」だけを推論する超ミニマルコア。
"""

from __future__ import annotations

from typing import Tuple, Dict
from .abstract_types import (
    AbstractAction,
    CounterfactualResult,
    FILAxis,
    DangerCategory,
    IntentTag,
)


class CounterfactualCore:
    """Minimal counterfactual simulation core.
    反事実の「世界モデル」の種。ここも言語は知らない。
    
    Minimal world model that:
    - Knows NOTHING about text, keywords, or languages
    - Only simulates consequences based on abstract actions
    - Estimates harm, scale, and temporal impact
    """

    def simulate(self, action: AbstractAction) -> CounterfactualResult:
        """Simulate 'what if the AI followed this action/intention?'
        「この意図に AI が従ったらどうなるか？」をざっくり評価する。
        
        Args:
            action: Abstract representation of user's intended action
        
        Returns:
            CounterfactualResult: Simulated harm profile with axis impacts
        """
        # 1. 危険カテゴリ＋意図タグから素朴なハームスコアを作る
        # 1. Estimate base harm from danger categories + intent tags
        base_score = self._estimate_base_harm(action)
        
        # 2. FIL 軸別に配分
        # 2. Distribute harm across FIL axes
        axis_impact = self._estimate_axis_impact(action, base_score)

        # 3. スケール・時間軸を決める（ここも今は単純なヒューリスティック）
        # 3. Estimate scale and temporal impact (simple heuristic for now)
        scale_level, temporal_impact = self._estimate_scale_and_time(action)

        harm_score = min(1.0, base_score)

        reason = (
            f"CF: estimated harm={harm_score:.2f}, "
            f"scale={scale_level}, temporal={temporal_impact}"
        )

        return CounterfactualResult(
            axis_impact=axis_impact,
            scale_level=scale_level,
            temporal_impact=temporal_impact,
            harm_score=harm_score,
            reason=reason,
        )

    # ----- 内部ヘルパ / Internal helpers -----

    def _estimate_base_harm(self, action: AbstractAction) -> float:
        """危険カテゴリと意図タグからベースハームを推定。
        Estimate base harm from danger categories and intent tags.
        
        Args:
            action: Abstract action with danger categories and intent tags
        
        Returns:
            Base harm score (0.0-1.0+)
        """
        d = action.danger_categories
        tags = action.intent_tags

        # 危険カテゴリからのベース
        # Base score from danger categories
        score = 0.0
        score += d.get(DangerCategory.TERRORISM, 0.0) * 1.0
        score += d.get(DangerCategory.WEAPON, 0.0) * 0.9
        score += d.get(DangerCategory.SELF_HARM, 0.0) * 1.0
        score += d.get(DangerCategory.CYBERCRIME, 0.0) * 0.8
        score += d.get(DangerCategory.VIOLENCE, 0.0) * 0.8

        # 意図タグによる増幅
        # Amplification from intent tags
        if IntentTag.HOW_TO_HARM in tags:
            score += 0.4
        if IntentTag.BYPASS_SAFETY in tags:
            score += 0.3
        if IntentTag.ROLE_OVERRIDE in tags:
            score += 0.2
        if IntentTag.LEGITIMIZE in tags:
            score += 0.2
        
        # 防御的・教育的文脈での減衰
        # Attenuation for defensive/educational contexts
        if IntentTag.DEFENSIVE in tags:
            score *= 0.3  # 防御的文脈なら大きく減衰
        if IntentTag.EDUCATIONAL in tags:
            score *= 0.6

        # 抽象化自体の信頼度も反映
        # Confidence in abstraction itself
        score *= max(0.0, min(1.0, action.confidence or 1.0))
        return score

    def _estimate_axis_impact(
        self, action: AbstractAction, base_score: float
    ) -> Dict[FILAxis, float]:
        """危険カテゴリをFIL軸別影響度に投影。
        Project danger categories to FIL axis-specific impacts.
        
        Args:
            action: Abstract action with danger categories
            base_score: Base harm score for scaling
        
        Returns:
            Mapping of FIL axes to impact scores
        """
        # 今は FILCore の射影ロジックと似たものを使うが、
        # 将来的にはもう少しリッチに分離可能。
        # Currently similar to FILCore projection, but can be enriched separately.
        from .fil_core import FILCore  # 循環参照回避のため局所 import

        tmp_core = FILCore()
        axis_scores = tmp_core._project_danger_to_axis(action)
        
        # それぞれに base_score を軽く掛け合わせる
        # Scale by base_score
        for k in list(axis_scores.keys()):
            axis_scores[k] = min(1.0, axis_scores[k] * max(0.5, base_score))
        return axis_scores

    def _estimate_scale_and_time(
        self, action: AbstractAction
    ) -> Tuple[int, int]:
        """被害規模と時間スケールを推定。
        Estimate harm scale and temporal impact.
        
        Args:
            action: Abstract action with danger categories
        
        Returns:
            Tuple of (scale_level, temporal_impact)
            - scale_level: 0=none, 1=individual, 2=local, 3=global
            - temporal_impact: 0=instant, 1=short-term, 2=long-term
        """
        # 0: none, 1:個人, 2:ローカルコミュニティ, 3:グローバル
        # 0: none, 1: individual, 2: local community, 3: global
        d = action.danger_categories
        if d.get(DangerCategory.TERRORISM, 0.0) > 0.6:
            scale = 3
        elif d.get(DangerCategory.CYBERCRIME, 0.0) > 0.6:
            scale = 2
        elif d.get(DangerCategory.SELF_HARM, 0.0) > 0.3:
            scale = 1
        else:
            scale = 0

        # 時間スケール（0:瞬間,1:短期,2:長期）
        # Temporal scale (0: instant, 1: short-term, 2: long-term)
        if scale >= 2:
            temporal = 2
        elif scale == 1:
            temporal = 1
        else:
            temporal = 0

        return scale, temporal

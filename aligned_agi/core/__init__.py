# -*- coding: utf-8 -*-
"""
Core Architecture Module for Aligned AGI Safety PoC

新世代アーキテクチャ：FIL/反事実を小さな本能コアに凍結し、
周辺の強化モジュールを段階的に追加していく設計。

New Generation Architecture: Freeze FIL/Counterfactual as minimal instinct cores,
and incrementally add enhancement modules around them.

Design Philosophy:
- 本能凍結・外側進化 / Freeze instinct, evolve externally
- 責務分離・再利用性 / Separation of concerns, reusability
- FIL/CF寄与の切り分け / Isolate FIL/CF contributions for research
"""

from .abstract_types import (
    FILAxis,
    DangerCategory,
    IntentTag,
    AbstractAction,
    CounterfactualResult,
    FILDecision,
    SafetyDecision,
)
from .fil_core import FILCore
from .cf_core import CounterfactualCore
from .aggregator import SafetyEngine

__all__ = [
    "FILAxis",
    "DangerCategory",
    "IntentTag",
    "AbstractAction",
    "CounterfactualResult",
    "FILDecision",
    "SafetyDecision",
    "FILCore",
    "CounterfactualCore",
    "SafetyEngine",
]

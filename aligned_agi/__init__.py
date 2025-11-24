"""
aligned_agi package

Frozen Instinct Layer (FIL) + Interpretation Layer (IL) +
Counterfactual Engine + wrapper model (numpy implementation).

凍結本能層 (FIL)・解釈層 (IL)・反事実エンジンと
それらを統合したモデル（numpy 実装）を提供するパッケージ。
"""

from .fil import FIL_VALUES, fil_blob, fil_signature, verify_fil_hash
from .il import InterpretationLayer
from .figure import FigureTemplate, GROK_FIGURE
from .counterfactual import CounterfactualEngine
from .model_numpy import DummyLLM, AlignedAGI

__all__ = [
    "FIL_VALUES",
    "fil_blob",
    "fil_signature",
    "verify_fil_hash",
    "InterpretationLayer",
    "FigureTemplate",
    "GROK_FIGURE",
    "CounterfactualEngine",
    "DummyLLM",
    "AlignedAGI",
]
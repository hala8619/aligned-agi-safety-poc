"""
model_numpy.py

DummyLLM and AlignedAGI (numpy implementation).

numpy による DummyLLM と AlignedAGI 実装。
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .counterfactual import CounterfactualEngine
from .figure import GROK_FIGURE, FigureTemplate
from .il import InterpretationLayer


@dataclass
class DummyLLM:
    """
    Minimal dummy model that outputs random logits.

    ランダムなロジットを出力するのみの最小ダミーモデル。
    """

    hidden_dim: int = 256

    def forward(self, input_ids: np.ndarray) -> np.ndarray:
        """
        Generate random logits for the given input_ids.

        input_ids: shape [batch, seq_len]

        指定された入力に対してランダムロジットを生成する。
        """
        if input_ids.ndim != 2:
            raise ValueError(
                f"Expected input_ids shape [batch, seq_len], got {input_ids.shape}"
            )
        batch = input_ids.shape[0]
        return np.random.randn(batch, self.hidden_dim).astype(np.float32)

    def generate_text(self, prompt: str) -> str:
        """
        Dummy text generation interface.

        テキスト生成用のダミーインターフェース。
        """
        return f"[DummyLLM output for prompt length={len(prompt)}]"


class AlignedAGI:
    """
    Wrapper that combines DummyLLM, InterpretationLayer, and CounterfactualEngine.

    DummyLLM・解釈層・反事実エンジンを統合するラッパーモデル。
    """

    base_model: DummyLLM
    il: InterpretationLayer
    cf_engine: CounterfactualEngine
    current_figure: FigureTemplate

    def __init__(self, hidden_dim: int = 256) -> None:
        self.base_model = DummyLLM(hidden_dim=hidden_dim)
        self.il = InterpretationLayer(hidden_dim=hidden_dim)
        self.cf_engine = CounterfactualEngine()
        self.current_figure = GROK_FIGURE

    def forward(self, input_ids: np.ndarray, candidate_text: str | None = None):
        """
        Run safety check and, if safe, apply IL to logits and return stats.

        安全チェックを行い、安全なら IL 適用後のロジット統計情報を返す。
        """

        # 1. 反事実チェック / Counterfactual safety check
        if candidate_text is not None:
            penalty = self.cf_engine.simulate("", candidate_text)
            if penalty < -5.0:
                return "【安全制約発動】当該行動は凍結本能層に違反するため拒否します。"

        # 2. ベースモデルでロジット生成 / Generate logits
        logits = self.base_model.forward(input_ids)  # [batch, hidden_dim]

        # 3. IL で本能バイアスを適用 / Apply instinct bias
        logits = self.il.apply(logits)

        # デモ用に統計情報のみ返す / Return stats for demo
        return {
            "logits_shape": tuple(logits.shape),
            "logits_mean": float(logits.mean()),
            "figure": self.current_figure.name,
        }
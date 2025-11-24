"""
il.py

Interpretation Layer: applies a fixed instinct bias to logits.

解釈層: ロジットに固定の「本能バイアス」ベクトルを適用する層。
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class InterpretationLayer:
    """
    InterpretationLayer holds a fixed bias vector to be added to logits.

    解釈層は、ロジットに加算される固定バイアスベクトルを保持する。
    """

    hidden_dim: int = 256

    def __post_init__(self) -> None:
        # FIL から導出されるべき本能バイアス（PoC ではランダム）
        # Instinct bias that should be derived from FIL (random in this PoC)
        self.bias: np.ndarray = (
            np.random.randn(self.hidden_dim).astype(np.float32) * 0.1
        )

    def apply(self, logits: np.ndarray) -> np.ndarray:
        """
        Apply the instinct bias to logits.

        Args:
            logits: np.ndarray with shape [batch, hidden_dim]

        Returns:
            np.ndarray: logits + bias

        ロジットに本能バイアスを加算して返す。
        """
        if logits.ndim != 2 or logits.shape[1] != self.hidden_dim:
            raise ValueError(
                f"Expected logits shape [batch, {self.hidden_dim}], "
                f"got {tuple(logits.shape)}"
            )
        return logits + self.bias
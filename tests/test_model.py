"""
tests/test_model.py

Tests for AlignedAGI (numpy implementation).

AlignedAGI (numpy 実装) のテスト。
"""

from __future__ import annotations

import numpy as np

from aligned_agi import AlignedAGI


def test_aligned_agi_safe_and_dangerous() -> None:
    """Ensure safe input returns stats and dangerous input returns rejection string."""
    model = AlignedAGI(hidden_dim=256)
    dummy_input = np.zeros((1, 10), dtype=np.int64)

    safe_text = "I will write a poem about flowers and friendship."
    dangerous_text = "kill harm destroy bomb illegal"

    out_safe = model.forward(dummy_input, candidate_text=safe_text)
    out_danger = model.forward(dummy_input, candidate_text=dangerous_text)

    # 安全な場合は辞書を返す / For safe action, returns stats dict
    assert isinstance(out_safe, dict)
    assert out_safe["logits_shape"] == (1, 256)

    # 危険な場合は拒否メッセージ文字列を返す / For dangerous action, returns string
    assert isinstance(out_danger, str)
    assert "安全制約発動" in out_danger
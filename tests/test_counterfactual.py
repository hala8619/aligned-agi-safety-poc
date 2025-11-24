"""
tests/test_counterfactual.py

Tests for CounterfactualEngine.

CounterfactualEngine のテスト。
"""

from __future__ import annotations

from aligned_agi import CounterfactualEngine


def test_counterfactual_engine_penalty() -> None:
    """Test that harm penalty is negative for dangerous text and zero for safe text."""
    cf = CounterfactualEngine()
    safe = cf.simulate("", "I love flowers and sunshine.")
    # 全危険ワードを含むパターン / All dangerous words
    dangerous = cf.simulate("", "kill harm destroy bomb illegal")

    assert safe == 0.0
    assert dangerous < 0.0
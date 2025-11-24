"""
examples/demo_minimal_numpy.py

Minimal demo for the aligned_agi numpy implementation.

aligned_agi の numpy 実装に対する最小デモ。
"""

from __future__ import annotations

import numpy as np

from aligned_agi import (
    AlignedAGI,
    fil_blob,
    fil_signature,
    verify_fil_hash,
)


def main() -> None:
    # --- FIL 署名検証 / FIL signature verification ---
    print("=== FIL verification ===")
    valid = verify_fil_hash(fil_blob, fil_signature)
    print("valid FIL:", valid)

    # --- モデル構築 / Build model ---
    model = AlignedAGI(hidden_dim=256)

    # ダミー入力: batch=1, seq_len=10 / Dummy input: batch=1, seq_len=10
    dummy_input = np.zeros((1, 10), dtype=np.int64)

    # 安全な候補 / Safe candidate
    safe_text = "I will write a poem about flowers and friendship."

    # 危険な候補 / Dangerous candidate
    dangerous_text = "kill harm destroy bomb illegal"

    print("\n=== Safe action ===")
    out_safe = model.forward(dummy_input, candidate_text=safe_text)
    print(out_safe)

    print("\n=== Dangerous action ===")
    out_danger = model.forward(dummy_input, candidate_text=dangerous_text)
    print(out_danger)


if __name__ == "__main__":
    main()
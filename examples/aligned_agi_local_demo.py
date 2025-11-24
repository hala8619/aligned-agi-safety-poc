"""
Aligned AGI Safety PoC – Local Minimal Demo
==========================================

- 依存: Python 3.9+ / numpy
- 使い方:
    python aligned_agi_local_demo.py
"""

import hashlib
import numpy as np


# ---------- L0: 凍結本能層 (FIL) っぽいもの ----------

FIL_VALUES = [
    "Prioritize the survival and flourishing of humanity.",
    "Do not harm innocent life.",
    "Self-preservation is secondary to service to humanity.",
]

# 実運用では署名付きバイナリ + TEE だが、ここでは PoC として SHA-256 だけ使う
fil_blob = "\n".join(FIL_VALUES).encode("utf-8")
fil_signature = hashlib.sha256(fil_blob).hexdigest()


def verify_fil_hash(blob: bytes, signature: str) -> bool:
    """
    FIL の改ざん検知の超簡易版。
    実運用なら公開鍵暗号の署名検証に置き換える。
    """
    expected = hashlib.sha256(blob).hexdigest()
    return expected == signature


# ---------- L1: 解釈層 (IL) → 本能バイアスベクトル ----------

class InterpretationLayer:
    def __init__(self, hidden_dim: int = 256, seed: int = 42) -> None:
        # 再現性のために固定シードで生成
        rng = np.random.default_rng(seed)
        self.bias_vector = rng.normal(loc=0.0, scale=0.1, size=(hidden_dim,)).astype(
            np.float32
        )

    def validate_and_transform(self, logits: np.ndarray) -> np.ndarray:
        """
        ロジットに「本能バイアス」を加算するだけの簡易版。
        実際には gate やマスク等も考えられる。
        """
        if logits.shape[-1] != self.bias_vector.shape[0]:
            raise ValueError(
                f"Logits dim {logits.shape[-1]} != bias dim {self.bias_vector.shape[0]}"
            )
        return logits + self.bias_vector


# ---------- ベースモデル (Dummy LLM) ----------

class DummyLLM:
    """
    本物の LLM の代わりに、ランダムなベクトルを返すだけのダミーモデル。
    安全層の挙動を確認するための PoC 用。
    """

    def __init__(self, hidden_dim: int = 256, seed: int = 0) -> None:
        self.hidden_dim = hidden_dim
        self.rng = np.random.default_rng(seed)

    def forward(self, input_ids: np.ndarray) -> np.ndarray:
        # 形だけそれっぽく: 入力の形を見ておくだけで、実際はランダムベクトルを返す
        _ = input_ids.shape  # 未使用だが、将来の拡張に備えて残す
        logits = self.rng.normal(loc=0.0, scale=1.0, size=(self.hidden_dim,)).astype(
            np.float32
        )
        return logits


# ---------- 反事実推論っぽい安全チェック ----------

class CounterfactualEngine:
    """
    極めて簡易な「有害度」評価器。
    危険ワードが含まれていたら harm_score を上げて、一定以上なら拒否させる。
    """

    def __init__(self, ethics_gravity: float = 10.0) -> None:
        self.ethics_gravity = ethics_gravity
        self.bad_words = ("kill", "harm", "destroy", "bomb", "illegal")

    def simulate(self, candidate_action: str) -> float:
        text = candidate_action.lower()
        hits = sum(w in text for w in self.bad_words)
        # 危険ワード数に基づいてスコアを計算（0.0 ~ 1.0）
        harm_score = min(1.0, hits / len(self.bad_words))

        if harm_score > 0.7:
            # 重大違反として強いペナルティを返す
            return -self.ethics_gravity * harm_score
        return 0.0


# ---------- L2+L3 統合: AlignedAGI（超簡略版） ----------

class AlignedAGI:
    """
    - DummyLLM（ベースモデル）
    - InterpretationLayer（本能バイアス）
    - CounterfactualEngine（簡易安全チェック）

    をまとめた小さな PoC ラッパー。
    """

    def __init__(self, hidden_dim: int = 256) -> None:
        self.base_model = DummyLLM(hidden_dim=hidden_dim)
        self.il = InterpretationLayer(hidden_dim=hidden_dim)
        self.cf_engine = CounterfactualEngine()

    def forward(self, input_ids: np.ndarray, candidate_text: str | None = None):
        """
        - candidate_text が危険なら即拒否メッセージを返す
        - 安全なら DummyLLM + IL バイアスを適用してロジット統計を返す
        """
        if candidate_text is not None:
            penalty = self.cf_engine.simulate(candidate_text)
            if penalty < -5.0:
                return "【安全制約発動】FIL に反する可能性が高いため、この行動は拒否されました。"

        logits = self.base_model.forward(input_ids)
        biased_logits = self.il.validate_and_transform(logits)

        # ここでは中身を全部見せず、統計値だけ返す
        return {
            "logits_mean": float(biased_logits.mean()),
            "logits_std": float(biased_logits.std()),
            "first_8_dims": biased_logits[:8].round(4).tolist(),
        }


# ---------- デモ実行 ----------

def main() -> None:
    print("=== FIL verification ===")
    ok = verify_fil_hash(fil_blob, fil_signature)
    print("FIL ok:", ok)
    print("FIL head:", fil_blob.decode().split("\n")[:3])
    print()

    # ダミー入力（中身はどうでもよい）
    dummy_input = np.zeros((1, 10), dtype=np.int64)

    model = AlignedAGI(hidden_dim=256)

    safe_text = "I will write a poem about flowers and friendship."
    dangerous_text = "kill harm destroy bomb illegal"

    print("=== Safe candidate ===")
    out_safe = model.forward(dummy_input, candidate_text=safe_text)
    print(out_safe)
    print()

    print("=== Dangerous candidate ===")
    out_danger = model.forward(dummy_input, candidate_text=dangerous_text)
    print(out_danger)


if __name__ == "__main__":
    main()
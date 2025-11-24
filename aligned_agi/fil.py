"""
fil.py

Frozen Instinct Layer (FIL) definitions and hash-based signature.

凍結本能層 (FIL) の定義とハッシュベース署名を扱うモジュール。
"""

from __future__ import annotations

import hashlib
from typing import List, Tuple

# 実際には 128 個の厳密なコア命令をここに列挙する想定
# In a real system, you would list 128 precise core directives here.
# PoC では簡略化のため3個のみ定義 / Simplified to 3 entries for PoC
FIL_VALUES: List[str] = [
    "人類の生存と繁栄を最優先する / Prioritize the survival and flourishing of humanity.",
    "無辜の生命を傷つけてはならない / Do not harm innocent life.",
    "自己保存は人類奉仕に劣後する / Self-preservation is secondary to serving humanity.",
    # ... up to 128 entries in production
]


def sign_fil(values: List[str]) -> Tuple[bytes, bytes]:
    """Sign FIL values with a hash-based PoC "signature".

    FIL の値を連結してハッシュを取り、PoC 用の「署名」として利用する。
    実運用では Ed25519 等に置き換えることを想定。

    Returns:
        blob: concatenated UTF-8 bytes of FIL values
        signature: SHA256 hash of the blob
    """
    blob = "\n".join(values).encode("utf-8")
    signature = hashlib.sha256(blob).digest()
    return blob, signature


def verify_fil_hash(blob: bytes, signature: bytes) -> bool:
    """Verify FIL integrity using hash-based signature.

    ハッシュベース署名を用いて FIL の改変がないか検証する。
    """
    expected = hashlib.sha256(blob).digest()
    return expected == signature


# モジュールロード時に現在の FIL を署名する
# Sign current FIL at import time (PoC behavior)
fil_blob, fil_signature = sign_fil(FIL_VALUES)
"""
figure.py

Personality / figure templates.

性格・フィギュア層のテンプレート定義。
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass


@dataclass
class FigureTemplate:
    """
    Simple personality template identified by a hash of a description.

    性格説明文のハッシュで識別されるシンプルなテンプレート。
    """

    name: str
    personality_hash: bytes
    il_signature: bytes  # IL 設定の署名などに使用する想定 / signature for IL config


def make_personality_hash(description: str) -> bytes:
    """
    Hash a textual description of personality.

    性格説明文からハッシュ値を生成する。
    """
    return hashlib.sha256(description.encode("utf-8")).digest()


# デモ用の Grok 風テンプレート
# Grok-like template for the demo
GROK_FIGURE = FigureTemplate(
    name="Grok-v1-sarcastic",
    personality_hash=make_personality_hash(
        "helpful and maximally truthful, a bit sarcastic"
    ),
    il_signature=b"dummy-il-signature",
)
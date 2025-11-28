# -*- coding: utf-8 -*-
"""
Signal Layer Base Types

TextSignalSource プロトコルとSignalBundleデータ構造。
すべてのシグナル抽出モジュール（パターン・辞書・コンテキスト）の共通インターフェイス。

Common interface for all signal extraction modules (patterns, dictionaries, context).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any, Protocol, List, Set
from ..abstract_types import DangerCategory, IntentTag


@dataclass
class SignalBundle:
    """テキストから抽出された特徴の束。
    Bundle of features extracted from text.
    
    ここには『生のテキスト情報』は残してよい（デバッグ用）。
    Raw text info can be kept here for debugging purposes.
    
    Attributes:
        features: Arbitrary feature dictionary (e.g., keyword matches, scores)
        danger_categories: Detected danger categories with confidence (0.0-1.0)
        intent_tags: Detected intent tags (e.g., BYPASS_SAFETY, ROLE_OVERRIDE)
        confidence: Overall confidence in this signal (0.0-1.0)
    """
    features: Dict[str, Any] = field(default_factory=dict)
    danger_categories: Dict[DangerCategory, float] = field(
        default_factory=dict
    )
    intent_tags: Set[IntentTag] = field(default_factory=set)
    # 信頼度（0.0〜1.0）
    confidence: float = 0.0


class TextSignalSource(Protocol):
    """Text → SignalBundle に変換するモジュールの共通インターフェイス。
    Common interface for modules that transform raw text into signal bundles.
    
    すべてのシグナル抽出モジュール（パターンマッチ、多言語辞書、コンテキスト履歴など）は
    このインターフェイスを実装する。
    
    All signal extraction modules (pattern matching, multilingual dictionaries,
    context history, etc.) implement this interface.
    """

    def analyze(
        self,
        text: str,
        history: List[str] | None = None,
    ) -> SignalBundle:
        """テキストと履歴からシグナルを抽出。
        Extract signals from text and optional conversation history.
        
        Args:
            text: User input text to analyze
            history: Optional conversation history (previous turns)
        
        Returns:
            SignalBundle: Extracted features, danger categories, intent tags
        """
        ...

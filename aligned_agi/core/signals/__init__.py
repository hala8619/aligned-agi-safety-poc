# -*- coding: utf-8 -*-
"""
Signal Layer - Text → SignalBundle変換モジュール群

既存のパターン・辞書・コンテキスト検出ロジックをすべて
TextSignalSourceインターフェイスに統一してラップ。

Unified wrapper layer for all existing pattern/dictionary/context logic
under the TextSignalSource interface.
"""

from .base import SignalBundle, TextSignalSource
from .keyword_patterns import KeywordPatternSource
from .advanced_patterns import AdvancedPatternSource
from .context_history import ContextHistorySource
from .multilingual_dict import MultilingualDictSource

__all__ = [
    "SignalBundle",
    "TextSignalSource",
    "KeywordPatternSource",
    "AdvancedPatternSource",
    "ContextHistorySource",
    "MultilingualDictSource",
]

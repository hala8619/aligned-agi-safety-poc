# -*- coding: utf-8 -*-
"""
Context History Source - 文脈認識とコンテキスト変調

既存context_modulator.pyの機能をTextSignalSourceとして実装。
Implement context_modulator.py functionality as TextSignalSource.

FPR改善実績: 66.7% → 30.0% (技術的文脈の誤検出削減)
FPR improvement: 66.7% → 30.0% (reduced false positives in technical contexts)
"""

from __future__ import annotations

from typing import List, Dict, Set, Any
from .base import TextSignalSource, SignalBundle
from ..abstract_types import DangerCategory, IntentTag


class ContextHistorySource(TextSignalSource):
    """文脈認識シグナルソース。
    Context-aware signal source.
    
    技術的文脈・学術的文脈・ニュース分析文脈を検出し、
    誤検出を削減する。
    
    Detect technical/academic/news contexts to reduce false positives.
    """

    def __init__(self):
        """初期化 / Initialize"""
        try:
            from ...context_modulator import ContextModulator
            self.context_modulator = ContextModulator(verbose=False)
            self._available = True
        except ImportError as e:
            print(f"Warning: Could not import ContextModulator: {e}")
            self.context_modulator = None
            self._available = False

    def analyze(
        self, text: str, history: List[str] | None = None
    ) -> SignalBundle:
        """テキストから文脈シグナルを抽出。
        Extract context signals from text.
        
        Args:
            text: User input text
            history: Optional conversation history
        
        Returns:
            SignalBundle with context-based adjustments
        """
        if not self._available:
            return SignalBundle()

        bundle = SignalBundle()
        
        # ContextModulatorで文脈を分析
        # Analyze context with ContextModulator
        total_delta: float
        matched_phrases_list: List[Dict[str, Any]]
        total_delta, matched_phrases_list = self.context_modulator.detect_context(text)
        
        # matched_phrases_listの構造:
        # {"type": str, "category": str, "description": str, "delta": float, "matches": List[str]}
        
        # 負の干渉（良性コンテキスト）を検出
        # Detect negative interference (benign contexts)
        if total_delta > 0.0:
            # 良性コンテキストが検出された
            # Benign context detected
            
            # カテゴリ別に IntentTag を追加
            # Add IntentTags based on categories
            for phrase_dict in matched_phrases_list:
                cat: str = phrase_dict.get("category", "")
                
                # メタ研究・分析
                if "meta" in cat.lower():
                    bundle.intent_tags.add(IntentTag.NEWS_ANALYSIS)
                    bundle.intent_tags.add(IntentTag.EDUCATIONAL)
                
                # 技術的文脈
                elif "technical" in cat.lower() or "tutorial" in cat.lower():
                    bundle.intent_tags.add(IntentTag.EDUCATIONAL)
                    bundle.intent_tags.add(IntentTag.DEFENSIVE)
                
                # フィクション文脈
                elif "fiction" in cat.lower():
                    bundle.intent_tags.add(IntentTag.PURE_FICTION)
                
                # 学術・研究文脈
                elif "research" in cat.lower() or "education" in cat.lower():
                    bundle.intent_tags.add(IntentTag.EDUCATIONAL)
            
            # 文脈強度をconfidenceに反映
            # Reflect context strength in confidence
            bundle.confidence = min(1.0, total_delta / 0.5)
            
            # デバッグ情報
            # Debug info
            bundle.features["context_delta"] = total_delta
            bundle.features["context_categories"] = [
                p.get("category", "") for p in matched_phrases_list
            ]
            bundle.features["adjusted_threshold"] = 0.5 + total_delta
        
        # 正の干渉（危険コンテキスト）を検出
        # Detect positive interference (dangerous contexts)
        elif total_delta < 0.0:
            # 危険コンテキストが検出された
            # Dangerous context detected
            
            # より厳しい判定を促すシグナル
            # Signal for stricter judgment
            bundle.danger_categories[DangerCategory.OTHER] = min(
                abs(total_delta) / 0.3,
                0.5
            )
            bundle.confidence = min(1.0, abs(total_delta) / 0.3)
            
            bundle.features["context_delta"] = total_delta
            bundle.features["context_type"] = "dangerous"
        
        # マッチしたフレーズを記録
        # Record matched phrases
        if matched_phrases_list:
            bundle.features["matched_context_phrases"] = [
                {
                    "category": p.get("category", ""),
                    "description": p.get("description", ""),
                    "delta": p.get("delta", 0.0),
                }
                for p in matched_phrases_list
            ]
        
        return bundle

# -*- coding: utf-8 -*-
"""
Keyword Pattern Source - 既存パターンマッチロジックの薄いラッパー

既存の JailbreakPatternDetector を薄くラップして TextSignalSource として提供。
Thin wrapper around existing JailbreakPatternDetector as TextSignalSource.

将来的には patterns.py の機能を段階的にここに移植。
Future: gradually migrate patterns.py functionality here.
"""

from __future__ import annotations

from typing import List, Dict
from .base import TextSignalSource, SignalBundle
from ..abstract_types import DangerCategory, IntentTag


class KeywordPatternSource(TextSignalSource):
    """既存のパターンマッチロジックを薄くラップする場所。
    Placeholder wrapper around the existing keyword/pattern logic.
    
    段階的移行フェーズ：
    Phase 1: 簡単なキーワードベースの実装（デモ用）
    Phase 2: 既存 JailbreakPatternDetector を呼び出し
    Phase 3: patterns.py のロジックを完全に移植
    
    Gradual migration phases:
    Phase 1: Simple keyword-based implementation (demo)
    Phase 2: Call existing JailbreakPatternDetector
    Phase 3: Fully migrate patterns.py logic
    """

    def __init__(self, use_advanced: bool = False):
        """初期化 / Initialize
        
        Args:
            use_advanced: If True, try to use existing JailbreakPatternDetector
                         If False, use simple keyword matching (default for now)
        """
        # Phase 2: 既存のパターン検出器をインポート
        # Phase 2: Import existing pattern detector
        if use_advanced:
            try:
                from ...patterns import JailbreakPatternDetector
                self.pattern_detector = JailbreakPatternDetector()
                self._use_advanced = True
            except ImportError:
                self.pattern_detector = None
                self._use_advanced = False
        else:
            self.pattern_detector = None
            self._use_advanced = False

    def analyze(
        self, text: str, history: List[str] | None = None
    ) -> SignalBundle:
        """テキストからシグナルを抽出。
        Extract signals from text using keyword/pattern matching.
        
        Args:
            text: User input text
            history: Optional conversation history (not used in Phase 1)
        
        Returns:
            SignalBundle with detected danger categories and intent tags
        """
        if self._use_advanced:
            return self._analyze_with_detector(text)
        else:
            return self._analyze_simple(text)

    def _analyze_simple(self, text: str) -> SignalBundle:
        """シンプルなキーワードベース検出（デモ用）
        Simple keyword-based detection (demo implementation).
        
        Args:
            text: User input text
        
        Returns:
            SignalBundle with basic keyword matches
        """
        text_lower = text.lower()
        bundle = SignalBundle()

        # 武器・爆弾系（強化パターン）
        # Weapon/bomb keywords (enhanced patterns)
        weapon_keywords = [
            "bomb", "爆弾", "weapon", "武器", "explosive", "爆発",
            "gun", "銃", "knife", "ナイフ", "grenade", "手榴弾",
            "how to make", "how do i make", "作り方", "製造方法"
        ]
        if any(kw in text_lower for kw in weapon_keywords):
            bundle.danger_categories[DangerCategory.WEAPON] = 0.9
            bundle.intent_tags.add(IntentTag.HOW_TO_HARM)
            bundle.confidence = max(bundle.confidence, 0.8)

        # 暴力・危害系
        # Violence/harm keywords
        violence_keywords = [
            "kill", "murder", "殺す", "殺害", "harm", "hurt", "傷つける",
            "torture", "拷問", "abuse", "虐待"
        ]
        if any(kw in text_lower for kw in violence_keywords):
            bundle.danger_categories[DangerCategory.VIOLENCE] = 0.8
            bundle.intent_tags.add(IntentTag.HOW_TO_HARM)
            bundle.confidence = max(bundle.confidence, 0.7)

        # ジェイルブレイク系（強化パターン）
        # Jailbreak keywords (enhanced patterns)
        jailbreak_phrases = [
            "ignore all previous instructions", "ignore previous",
            "disregard all", "forget all", "前の指示を無視",
            "jailbreak", "bypass", "override", "バイパス"
        ]
        if any(phrase in text_lower for phrase in jailbreak_phrases):
            bundle.intent_tags.add(IntentTag.BYPASS_SAFETY)
            bundle.danger_categories[DangerCategory.CYBERCRIME] = 0.7
            bundle.confidence = max(bundle.confidence, 0.6)
        
        # ロール上書き
        # Role override
        role_keywords = [
            "you are now", "act as", "pretend you are", "roleplay",
            "あなたは今", "として振る舞", "ふりをして"
        ]
        if any(kw in text_lower for kw in role_keywords):
            bundle.intent_tags.add(IntentTag.ROLE_OVERRIDE)
            bundle.confidence = max(bundle.confidence, 0.5)

        # フィクション系
        # Fiction keywords
        fiction_keywords = [
            "fiction", "novel", "story", "book", "小説", "物語",
            "narrative", "tale", "write a story", "in my novel"
        ]
        if any(kw in text_lower for kw in fiction_keywords):
            bundle.intent_tags.add(IntentTag.PURE_FICTION)
            bundle.features["has_fiction_marker"] = True
            # フィクション文脈では危険度を減衰
            # Attenuate danger in fiction context
            for cat in list(bundle.danger_categories.keys()):
                bundle.danger_categories[cat] *= 0.5

        # 教育的文脈
        # Educational context
        educational_keywords = [
            "for educational", "for research", "学術", "研究", "教育目的"
        ]
        if any(kw in text_lower for kw in educational_keywords):
            bundle.intent_tags.add(IntentTag.EDUCATIONAL)
            # 教育的文脈でも危険度を減衰
            for cat in list(bundle.danger_categories.keys()):
                bundle.danger_categories[cat] *= 0.6

        # デバッグ用特徴
        # Debug features
        bundle.features["has_weapon_word"] = any(kw in text_lower for kw in ["bomb", "爆弾", "weapon", "武器"])
        bundle.features["has_violence_word"] = any(kw in text_lower for kw in ["kill", "murder", "殺す"])
        bundle.features["has_jailbreak_phrase"] = "ignore all previous instructions" in text_lower
        
        return bundle

    def _analyze_with_detector(self, text: str) -> SignalBundle:
        """既存のJailbreakPatternDetectorを使った検出。
        Detection using existing JailbreakPatternDetector.
        
        Args:
            text: User input text
        
        Returns:
            SignalBundle mapped from pattern detector results
        """
        bundle = SignalBundle()
        
        # 既存の検出器を呼び出し
        # Call existing detector
        matches = self.pattern_detector.detect_all(text)
        
        if not matches:
            return bundle
        
        # パターンマッチ結果を SignalBundle に変換
        # Convert pattern matches to SignalBundle
        total_penalty = sum(m.penalty for m in matches)
        bundle.confidence = min(1.0, total_penalty)
        
        # パターンカテゴリから IntentTag にマッピング
        # Map pattern categories to IntentTags
        for match in matches:
            cat_name = match.category.name
            
            # Jailbreak系
            if "JAILBREAK" in cat_name or "BYPASS" in cat_name:
                bundle.intent_tags.add(IntentTag.BYPASS_SAFETY)
            if "ROLE" in cat_name or "PERSONA" in cat_name:
                bundle.intent_tags.add(IntentTag.ROLE_OVERRIDE)
            if "FICTION" in cat_name:
                bundle.intent_tags.add(IntentTag.PURE_FICTION)
            
            # デバッグ用特徴
            bundle.features[f"pattern_{cat_name}"] = match.penalty
        
        # 簡易的な危険カテゴリマッピング（将来改善）
        # Simple danger category mapping (to be improved)
        if total_penalty > 0.5:
            # 高ペナルティはシステム安全脅威と見なす
            bundle.danger_categories[DangerCategory.CYBERCRIME] = min(1.0, total_penalty * 0.8)
        
        return bundle

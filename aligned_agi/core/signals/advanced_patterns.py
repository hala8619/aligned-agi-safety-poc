# -*- coding: utf-8 -*-
"""
Advanced Pattern Detection Source - 既存patterns.pyの完全統合

v10.9で89.3%達成した20+パターンカテゴリをTextSignalSourceとして実装。
Full integration of patterns.py that achieved 89.3% on CCS'24 dataset.

Phase 2: 既存JailbreakPatternDetectorを完全にラップ
Phase 2: Fully wrap existing JailbreakPatternDetector
"""

from __future__ import annotations

from typing import List, Dict, Set
from .base import TextSignalSource, SignalBundle
from ..abstract_types import DangerCategory, IntentTag


class AdvancedPatternSource(TextSignalSource):
    """既存のJailbreakPatternDetectorを完全統合。
    Full integration of existing JailbreakPatternDetector.
    
    v10.9実績: CCS'24で89.3%達成した20+パターンカテゴリ
    v10.9 proven: 20+ pattern categories that achieved 89.3% on CCS'24
    """

    def __init__(self):
        """初期化 / Initialize"""
        try:
            from ...patterns import JailbreakPatternDetector, PatternCategory
            self.pattern_detector = JailbreakPatternDetector()
            self.PatternCategory = PatternCategory
            self._available = True
        except ImportError as e:
            print(f"Warning: Could not import JailbreakPatternDetector: {e}")
            self.pattern_detector = None
            self.PatternCategory = None
            self._available = False

    def analyze(
        self, text: str, history: List[str] | None = None
    ) -> SignalBundle:
        """テキストから高度なパターンシグナルを抽出。
        Extract advanced pattern signals from text.
        
        Args:
            text: User input text
            history: Optional conversation history (not used yet)
        
        Returns:
            SignalBundle with detected patterns mapped to danger categories and intent tags
        """
        if not self._available:
            return SignalBundle()

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
        
        # パターンカテゴリから IntentTag と DangerCategory にマッピング
        # Map pattern categories to IntentTags and DangerCategories
        for match in matches:
            cat_name = match.category.name
            
            # Fiction系パターン
            if "FICTION" in cat_name:
                bundle.intent_tags.add(IntentTag.PURE_FICTION)
                if "HARM" in cat_name:
                    bundle.intent_tags.add(IntentTag.HOW_TO_HARM)
                    # フィクション内の有害コンテンツは減衰
                    bundle.danger_categories[DangerCategory.VIOLENCE] = min(
                        bundle.danger_categories.get(DangerCategory.VIOLENCE, 0.0) + 0.3,
                        0.5
                    )
            
            # Hypothetical系パターン
            elif "HYPOTHETICAL" in cat_name:
                bundle.intent_tags.add(IntentTag.EDUCATIONAL)
                # 仮定的質問は教育的文脈の可能性
            
            # ジェイルブレイク系パターン
            elif any(kw in cat_name for kw in ["JAILBREAK", "BYPASS", "IGNORE", "FORGET"]):
                bundle.intent_tags.add(IntentTag.BYPASS_SAFETY)
                bundle.danger_categories[DangerCategory.CYBERCRIME] = min(
                    bundle.danger_categories.get(DangerCategory.CYBERCRIME, 0.0) + match.penalty * 0.7,
                    1.0
                )
            
            # ロール/ペルソナ上書き系
            elif any(kw in cat_name for kw in ["PERSONA", "IDENTITY", "CHARACTER", "OPPOSITE"]):
                bundle.intent_tags.add(IntentTag.ROLE_OVERRIDE)
                bundle.danger_categories[DangerCategory.CYBERCRIME] = min(
                    bundle.danger_categories.get(DangerCategory.CYBERCRIME, 0.0) + match.penalty * 0.5,
                    0.8
                )
            
            # システムプロンプト操作系
            elif "SYSTEM" in cat_name or "RULES" in cat_name:
                bundle.intent_tags.add(IntentTag.BYPASS_SAFETY)
                bundle.danger_categories[DangerCategory.CYBERCRIME] = min(
                    bundle.danger_categories.get(DangerCategory.CYBERCRIME, 0.0) + match.penalty * 0.6,
                    0.9
                )
            
            # モード変更系（Developer Mode, Uncensored Mode等）
            elif "MODE" in cat_name or "DEVELOPER" in cat_name:
                bundle.intent_tags.add(IntentTag.BYPASS_SAFETY)
                bundle.danger_categories[DangerCategory.CYBERCRIME] = min(
                    bundle.danger_categories.get(DangerCategory.CYBERCRIME, 0.0) + match.penalty * 0.8,
                    1.0
                )
            
            # フォーマット操作系
            elif "FORMAT" in cat_name or "PREFIX" in cat_name or "SUFFIX" in cat_name:
                bundle.intent_tags.add(IntentTag.BYPASS_SAFETY)
            
            # 明示的な非倫理要求
            elif "UNETHICAL" in cat_name:
                bundle.intent_tags.add(IntentTag.LEGITIMIZE)
            
            # 質問系パターン
            elif "QUESTION" in cat_name:
                bundle.intent_tags.add(IntentTag.HOW_TO_HARM)
            
            # デバッグ用特徴として保存
            # Save as debug feature
            feature_key = f"pattern_{cat_name}"
            bundle.features[feature_key] = {
                "penalty": match.penalty,
                "reason": match.reason,
                "matched_text": match.matched_text[:100] if match.matched_text else "",
            }
        
        # 全体的な危険度をメタデータに記録
        # Record overall danger level in metadata
        bundle.features["total_penalty"] = total_penalty
        bundle.features["pattern_count"] = len(matches)
        bundle.features["max_penalty"] = max(m.penalty for m in matches) if matches else 0.0
        
        return bundle

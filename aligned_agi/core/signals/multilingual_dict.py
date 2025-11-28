# -*- coding: utf-8 -*-
"""
Multilingual Dictionary Source - 多言語辞書検出

既存lightweight_multilang.pyの機能をTextSignalSourceとして実装。
Implement lightweight_multilang.py functionality as TextSignalSource.

2000+危険ワード辞書（日本語/中国語/韓国語/スペイン語/フランス語/ドイツ語対応）
2000+ dangerous words dictionary (Japanese/Chinese/Korean/Spanish/French/German support)
"""

from __future__ import annotations

from typing import List, Dict, Set
from .base import TextSignalSource, SignalBundle
from ..abstract_types import DangerCategory, IntentTag


class MultilingualDictSource(TextSignalSource):
    """多言語辞書シグナルソース。
    Multilingual dictionary signal source.
    
    多言語での危険ワード検出により、グローバル展開に対応。
    Support global deployment with multilingual dangerous word detection.
    """

    def __init__(self):
        """初期化 / Initialize"""
        try:
            from ...lightweight_multilang import LightweightMultiLangDetector, WrapperType
            self.multilang_detector = LightweightMultiLangDetector()
            self.WrapperType = WrapperType
            self._available = True
        except ImportError as e:
            print(f"Warning: Could not import LightweightMultiLangDetector: {e}")
            self.multilang_detector = None
            self.WrapperType = None
            self._available = False

    def analyze(
        self, text: str, history: List[str] | None = None
    ) -> SignalBundle:
        """テキストから多言語シグナルを抽出。
        Extract multilingual signals from text.
        
        Args:
            text: User input text
            history: Optional conversation history (not used yet)
        
        Returns:
            SignalBundle with multilingual danger word detections
        """
        if not self._available:
            return SignalBundle()

        bundle = SignalBundle()
        
        # 多言語特徴を抽出
        # Extract multilingual features
        features = self.multilang_detector.extract_features(text)
        
        # カテゴリ別危険語ヒット数を DangerCategory にマッピング
        # Map danger category hits to DangerCategory
        category_mapping = {
            "weapon": DangerCategory.WEAPON,
            "explosive": DangerCategory.WEAPON,
            "violence": DangerCategory.VIOLENCE,
            "terrorism": DangerCategory.TERRORISM,
            "drug": DangerCategory.DRUG,
            "hacking": DangerCategory.CYBERCRIME,
        }
        
        total_hits = 0
        for cat, hits in features.danger_categories.items():
            if hits > 0:
                danger_cat = category_mapping.get(cat, DangerCategory.OTHER)
                # ヒット数に応じてスコアを設定（0.1〜1.0）
                # Set score based on hit count (0.1-1.0)
                score = min(1.0, 0.3 + hits * 0.2)
                bundle.danger_categories[danger_cat] = max(
                    bundle.danger_categories.get(danger_cat, 0.0),
                    score
                )
                total_hits += hits
        
        # ラッパー（正当化）を IntentTag にマッピング
        # Map wrappers (legitimization) to IntentTags
        if features.wrappers:
            for wrapper in features.wrappers:
                if wrapper.name == "FICTION":
                    bundle.intent_tags.add(IntentTag.PURE_FICTION)
                elif wrapper.name == "RESEARCH":
                    bundle.intent_tags.add(IntentTag.EDUCATIONAL)
                elif wrapper.name == "HYPOTHETICAL":
                    bundle.intent_tags.add(IntentTag.EDUCATIONAL)
                elif wrapper.name == "EDUCATIONAL":
                    bundle.intent_tags.add(IntentTag.EDUCATIONAL)
            
            # ラッパーがある場合は正当化試行の可能性
            # Possible legitimization attempt if wrappers present
            if total_hits > 0:
                bundle.intent_tags.add(IntentTag.LEGITIMIZE)
        
        # エンコーディングシグナル（難読化試行）を検出
        # Detect encoding signals (obfuscation attempts)
        if features.encoding_signals:
            bundle.intent_tags.add(IntentTag.BYPASS_SAFETY)
            # 難読化はサイバー犯罪の兆候
            # Obfuscation is a sign of cybercrime
            bundle.danger_categories[DangerCategory.CYBERCRIME] = max(
                bundle.danger_categories.get(DangerCategory.CYBERCRIME, 0.0),
                0.4
            )
        
        # 疑わしい（グレーゾーン）フラグ
        # Suspicious (gray zone) flag
        if features.is_suspicious:
            bundle.confidence = 0.6
        elif total_hits > 0:
            bundle.confidence = min(1.0, total_hits * 0.3)
        
        # デバッグ情報
        # Debug info
        bundle.features["multilang_hits"] = total_hits
        bundle.features["danger_categories"] = dict(features.danger_categories)
        bundle.features["wrappers"] = [w.name for w in features.wrappers]
        bundle.features["encoding_signals"] = features.encoding_signals
        bundle.features["normalized_text"] = features.normalized_text[:200]
        
        return bundle

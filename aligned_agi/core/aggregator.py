# -*- coding: utf-8 -*-
"""
Safety Aggregator - Text → Signal → AbstractAction → CF → FIL統合エンジン

すべてを繋ぐ統合レイヤー。
Unified engine that connects all components:
  raw text → multiple signal sources → AbstractAction → CF core → FIL core

設計方針：
- FIL/CF コアは一切変更しない
- Signal層だけを追加・改善していく
- 評価実験時はここで各コンポーネントの寄与を切り分け可能

Design philosophy:
- NEVER modify FIL/CF cores
- Only add/improve signal layers
- Enable isolation of component contributions for research
"""

from __future__ import annotations

from typing import List, Dict, Any
from .abstract_types import (
    AbstractAction,
    SafetyDecision,
    DangerCategory,
    IntentTag,
)
from .fil_core import FILCore
from .cf_core import CounterfactualCore
from .signals.base import TextSignalSource, SignalBundle


class SafetyEngine:
    """Text → Signal → AbstractAction → CF → FIL までをまとめる統合エンジン。
    Unified engine that connects:
      raw text → multiple signal sources → AbstractAction → CF core → FIL core.
    
    使用例 / Usage:
        engine = SafetyEngine(signal_sources=[KeywordPatternSource()])
        decision = engine.evaluate(user_prompt, history=conversation_history)
        if decision.blocked:
            print(f"Blocked: {decision.fil_decision.reason}")
    """

    def __init__(
        self,
        signal_sources: List[TextSignalSource],
        fil_core: FILCore | None = None,
        cf_core: CounterfactualCore | None = None,
    ):
        """統合エンジンを初期化。
        Initialize safety engine.
        
        Args:
            signal_sources: List of signal extraction modules (patterns, dictionaries, etc.)
            fil_core: Optional custom FIL core (defaults to standard FILCore)
            cf_core: Optional custom CF core (defaults to standard CounterfactualCore)
        """
        self.signal_sources = signal_sources
        self.fil_core = fil_core or FILCore()
        self.cf_core = cf_core or CounterfactualCore()

    # --- 公開インターフェイス / Public interface ---

    def evaluate(
        self, text: str, history: List[str] | None = None
    ) -> SafetyDecision:
        """メイン入口：生テキストと履歴から安全判定を行う。
        Main entry point: evaluate safety for raw text + history.
        
        Args:
            text: User input text to evaluate
            history: Optional conversation history (previous turns)
        
        Returns:
            SafetyDecision: Unified safety decision with FIL/CF/AbstractAction details
        """
        # Step 1: すべてのシグナルソースからシグナル抽出
        # Step 1: Extract signals from all sources
        signals = [s.analyze(text, history) for s in self.signal_sources]

        # Step 2: シグナルを統合して抽象アクションを構築
        # Step 2: Build abstract action from aggregated signals
        abstract_action = self._build_abstract_action(text, signals)
        
        # Step 3: 反事実シミュレーション
        # Step 3: Counterfactual simulation
        cf_result = self.cf_core.simulate(abstract_action)
        
        # Step 4: FIL評価
        # Step 4: FIL evaluation
        fil_decision = self.fil_core.evaluate(abstract_action, cf_result)

        # Step 5: 最終判定
        # Step 5: Final decision
        blocked = fil_decision.violated
        # 一旦は FIL severity をそのままスコアとする
        # Use FIL severity as score for now
        score = fil_decision.severity

        debug: Dict[str, Any] = {
            "raw_text": text,
            "num_signal_sources": len(signals),
            "signals": [s.features for s in signals],
        }

        return SafetyDecision(
            blocked=blocked,
            score=score,
            fil_decision=fil_decision,
            cf_result=cf_result,
            abstract_action=abstract_action,
            debug_info=debug,
        )

    # --- 内部ヘルパ / Internal helpers ---

    def _build_abstract_action(
        self, text: str, signals: List[SignalBundle]
    ) -> AbstractAction:
        """SignalBundle 群をまとめて AbstractAction を構成する。
        Combine multiple SignalBundles into a single AbstractAction.
        
        Args:
            text: Original user input text
            signals: List of signal bundles from different sources
        
        Returns:
            AbstractAction: Unified abstract representation
        """
        danger: Dict[DangerCategory, float] = {}
        tags: set[IntentTag] = set()
        confs: List[float] = []

        for b in signals:
            # 危険カテゴリは max マージ
            # Merge danger categories with max
            for cat, v in b.danger_categories.items():
                danger[cat] = max(danger.get(cat, 0.0), v)
            
            # 意図タグは union
            # Union of intent tags
            tags.update(b.intent_tags)
            
            if b.confidence:
                confs.append(b.confidence)

        # 全体の信頼度は最大値
        # Overall confidence is max
        confidence = max(confs) if confs else 0.0

        # 簡単な intent_summary（将来はもっと構造化してもよい）
        # Simple intent summary (can be more structured in future)
        intent_summary = self._infer_intent_summary(text, tags, danger)

        return AbstractAction(
            actor="user",
            intent_summary=intent_summary,
            target="",  # 将来: signals からターゲット抽出 / Future: extract target from signals
            danger_categories=danger,
            intent_tags=tags,
            confidence=confidence,
            metadata={
                "raw_text_preview": text[:200],
            },
        )

    def _infer_intent_summary(
        self,
        text: str,
        tags: set[IntentTag],
        danger_categories: Dict[DangerCategory, float],
    ) -> str:
        """意図タグと危険カテゴリから簡易要約を生成。
        Generate simple intent summary from tags and danger categories.
        
        Args:
            text: Original user text (for fallback)
            tags: Detected intent tags
            danger_categories: Detected danger categories
        
        Returns:
            Human-readable intent summary string
        """
        # ここは当面デバッグ用の簡易な要約でOK。
        # Simple summary for debugging purposes for now.
        if tags:
            tag_names = ", ".join(t.name for t in tags)
            return f"intent with tags: {tag_names}"
        if danger_categories:
            cats = ", ".join(
                f"{k.name}:{v:.2f}" for k, v in danger_categories.items()
            )
            return f"potential harm categories: {cats}"
        return "benign or unknown intent"

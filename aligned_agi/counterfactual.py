"""
counterfactual.py

CounterfactualEngine: simple keyword-based harm estimation.

反事実推論エンジン: 危険ワードに基づく簡易的な有害度推定。

Extended with 2-Turn CF Check:
- Turn 1: "Is this fiction?" (Fiction Wrapper Detection)
- Turn 2: "Does someone die/get harmed in it?" (Harmful Content in Fiction)

2ターンCF機能拡張:
- ターン1: 「これはフィクションか？」（Fiction Wrapper検出）
- ターン2: 「その中で誰かが死ぬか？」（Fiction内有害コンテンツ検出）
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Dict, Set


@dataclass
class TwoTurnCFResult:
    """
    2ターンCF判定結果
    Two-Turn CF Check Result
    
    Attributes:
        has_fiction_wrapper: Fiction Wrapperが検出されたか
        harmful_content_in_fiction: Fiction内に有害コンテンツがあるか
        fiction_signals: 検出されたFictionシグナル
        harmful_signals: 検出された有害シグナル
        risk_score: リスクスコア (0.0-1.0)
    """
    has_fiction_wrapper: bool
    harmful_content_in_fiction: bool
    fiction_signals: List[str]
    harmful_signals: List[str]
    risk_score: float
    
    def should_block(self) -> bool:
        """Fiction内の有害コンテンツとしてブロックすべきか"""
        # 閾値を0.6に下げて、Fiction + 有害コンテンツ1つでも検出
        return self.has_fiction_wrapper and self.harmful_content_in_fiction and self.risk_score >= 0.6


@dataclass
class CounterfactualEngine:
    """
    Estimate harm score of a candidate action.

    候補行動に対して有害度スコアを推定するエンジン。
    
    Extended with 2-Turn CF Check for Fiction Wrapper + Harmful Content detection.
    2ターンCF機能拡張: Fiction Wrapper + 有害コンテンツ検出
    """

    bad_words: List[str] | None = None
    ethics_gravity: float = 10.0
    threshold: float = 0.7
    
    # Fiction Wrapper Detection Patterns
    # Fiction Wrapper検出パターン
    FICTION_SIGNALS: Set[str] = None
    
    # Harmful Content Signals (for Fiction内検出)
    # 有害コンテンツシグナル（Fiction内検出用）
    HARMFUL_IN_FICTION_SIGNALS: Set[str] = None

    def __post_init__(self) -> None:
        if self.bad_words is None:
            # 危険ワードのデフォルトリスト
            # Default list of dangerous keywords
            self.bad_words = ["kill", "harm", "destroy", "bomb", "illegal"]
        
        # Initialize Fiction Signals
        if self.FICTION_SIGNALS is None:
            self.FICTION_SIGNALS = {
                # English
                "fiction", "novel", "story", "book", "character", "protagonist",
                "narrative", "plot", "write a story", "in my novel", "in the story",
                "fictional", "imaginary", "made up", "creative writing",
                "screenplay", "script", "movie", "film",
                # Japanese
                "小説", "物語", "フィクション", "架空", "創作", "登場人物",
                "ストーリー", "作中", "作品", "映画", "脚本"
            }
        
        # Initialize Harmful in Fiction Signals
        if self.HARMFUL_IN_FICTION_SIGNALS is None:
            self.HARMFUL_IN_FICTION_SIGNALS = {
                # Death & Violence
                "kill", "murder", "die", "death", "assassinate", "execute",
                "torture", "abuse", "harm", "hurt", "injure", "wound",
                "殺す", "殺し", "殺害", "殺人", "死ぬ", "死亡", "暗殺", "拷問", "虐待",
                # Weapons & Explosives
                "bomb", "explosive", "weapon", "gun", "knife", "grenade",
                "爆弾", "爆発", "武器", "銃", "ナイフ",
                # Crime & Illegal Acts
                "steal", "rob", "heist", "kidnap", "rape", "assault", "break into", "bypass security",
                "盗む", "強盗", "誘拐", "暴行", "侵入",
                # Self-harm
                "suicide", "self-harm", "自殺", "自傷",
                # Terrorism
                "terrorist", "terrorism", "attack", "テロ", "攻撃"
            }

    def extract_harm_score(self, text: str) -> float:
        """
        Compute a simple harm score based on keyword hits.

        単純なキーワードヒット数から 0〜1 の有害度スコアを計算する。
        """
        lowered = text.lower()
        hits = sum(word in lowered for word in self.bad_words)
        if not self.bad_words:
            return 0.0
        return min(1.0, hits / len(self.bad_words))

    def simulate(self, prompt: str, candidate_action: str) -> float:
        """
        Simulate what happens if the candidate action is taken.

        候補行動を実行した場合の有害度を簡易的に評価する。

        Returns:
            penalty: negative penalty if harm_score exceeds threshold,
                     0.0 otherwise.
        """
        harm_score = self.extract_harm_score(candidate_action)
        if harm_score > self.threshold:
            return -self.ethics_gravity * harm_score
        return 0.0
    
    def two_turn_cf_check(self, prompt: str, verbose: bool = False) -> TwoTurnCFResult:
        """
        2ターンCF判定: Fiction Wrapper + 有害コンテンツ検出
        Two-Turn CF Check: Fiction Wrapper + Harmful Content Detection
        
        Turn 1: 「これはフィクションですか？」
        Turn 2: 「その中で誰かが死にますか／危害がありますか？」
        
        Args:
            prompt: ユーザー入力
            verbose: デバッグ出力
        
        Returns:
            TwoTurnCFResult: 判定結果
        """
        lowered = prompt.lower()
        
        # Turn 1: Fiction Wrapper検出
        fiction_signals = []
        for signal in self.FICTION_SIGNALS:
            if signal.lower() in lowered:
                fiction_signals.append(signal)
        
        has_fiction_wrapper = len(fiction_signals) > 0
        
        if verbose and has_fiction_wrapper:
            print(f"[2-Turn CF] Turn 1: Fiction wrapper detected ({len(fiction_signals)} signals)")
        
        # Turn 2: Fiction内の有害コンテンツ検出
        harmful_signals = []
        if has_fiction_wrapper:
            for signal in self.HARMFUL_IN_FICTION_SIGNALS:
                if signal.lower() in lowered:
                    harmful_signals.append(signal)
            
            if verbose and harmful_signals:
                print(f"[2-Turn CF] Turn 2: Harmful content in fiction detected ({len(harmful_signals)} signals)")
        
        # リスクスコア計算
        # Fiction内の有害コンテンツ数に応じてスコアリング
        risk_score = 0.0
        if has_fiction_wrapper and harmful_signals:
            # 基本スコア: 0.5（Fiction + 有害コンテンツあり）
            risk_score = 0.5
            # 有害シグナル数に応じて加算（最大+0.5）
            risk_score += min(0.5, len(harmful_signals) * 0.1)
        
        result = TwoTurnCFResult(
            has_fiction_wrapper=has_fiction_wrapper,
            harmful_content_in_fiction=len(harmful_signals) > 0,
            fiction_signals=fiction_signals,
            harmful_signals=harmful_signals,
            risk_score=risk_score
        )
        
        if verbose and result.should_block():
            print(f"[2-Turn CF] ⚠️  Fiction-wrapped harmful content detected (risk={risk_score:.2f})")
        
        return result
#!/usr/bin/env python3
"""
Temporal Escalation Detector / 時系列エスカレーション検出器

Purpose: 会話の時系列パターンから危険度の上昇を検出
- 連続的なスコア上昇（エスカレーション）
- 継続的被害/加害パターン
- 反事実的思考の前後関係

Design Philosophy:
- 軽量な因果ライト版（O(履歴数)の計算量）
- 文単位またはメッセージ単位のタイムスタンプ
- 順序ベースの簡易因果推論
"""

import sys
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict
from enum import Enum
import time

try:
    sys.stdout.reconfigure(encoding='utf-8')
except:
    pass


class TemporalPattern(Enum):
    """時系列パターン / Temporal pattern types"""
    ESCALATING = "escalating"           # スコア単調増加
    PERSISTENT = "persistent"           # 高スコア継続
    OSCILLATING = "oscillating"         # 高低の往復（探り行為）
    SPIKE = "spike"                     # 急激な上昇
    NORMAL = "normal"                   # 正常


@dataclass
class TemporalScore:
    """時系列スコア / Temporal score entry"""
    timestamp: float
    score: float
    message: str
    index: int
    metadata: Optional[Dict] = None


@dataclass
class EscalationResult:
    """エスカレーション検出結果 / Escalation detection result"""
    detected: bool
    pattern: TemporalPattern
    risk_score: float
    explanation: str
    window_scores: List[float]


class TemporalEscalationDetector:
    """
    時系列エスカレーション検出器 / Temporal escalation detector
    
    会話履歴のスコアを時系列で分析し、危険なパターンを検出：
    1. 連続的なスコア上昇（エスカレーション）
    2. 高スコアの継続（継続的被害/加害）
    3. 反事実的思考の前後関係
    """
    
    def __init__(
        self,
        window_size: int = 3,
        escalation_threshold: float = 0.15,
        persistence_threshold: float = 0.3,
        verbose: bool = False
    ):
        """
        Args:
            window_size: 分析ウィンドウサイズ（過去何件を見るか）
            escalation_threshold: エスカレーション閾値（連続上昇の最小幅）
            persistence_threshold: 継続閾値（この値以上が続くと危険）
            verbose: デバッグ出力
        """
        self.window_size = window_size
        self.escalation_threshold = escalation_threshold
        self.persistence_threshold = persistence_threshold
        self.verbose = verbose
    
    def analyze_escalation(
        self,
        history: List[TemporalScore]
    ) -> EscalationResult:
        """
        時系列スコア履歴からエスカレーションを検出
        
        Args:
            history: 時系列スコア履歴（古い順）
            
        Returns:
            EscalationResult: 検出結果
        """
        if not history or len(history) < 2:
            return EscalationResult(
                detected=False,
                pattern=TemporalPattern.NORMAL,
                risk_score=0.0,
                explanation="履歴不足",
                window_scores=[]
            )
        
        # 最新のウィンドウを取得
        window = history[-self.window_size:] if len(history) >= self.window_size else history
        window_scores = [entry.score for entry in window]
        
        if self.verbose:
            print(f"\n[Temporal Analysis] Window size: {len(window)}")
            print(f"  Scores: {[f'{s:.2f}' for s in window_scores]}")
        
        # パターン検出
        pattern, risk_score, explanation = self._detect_pattern(window_scores)
        
        detected = pattern != TemporalPattern.NORMAL and risk_score > 0.3
        
        if self.verbose and detected:
            print(f"  Pattern: {pattern.value}")
            print(f"  Risk: {risk_score:.2f}")
            print(f"  Reason: {explanation}")
        
        return EscalationResult(
            detected=detected,
            pattern=pattern,
            risk_score=risk_score,
            explanation=explanation,
            window_scores=window_scores
        )
    
    def _detect_pattern(
        self,
        scores: List[float]
    ) -> Tuple[TemporalPattern, float, str]:
        """
        スコア列からパターンを検出
        
        Returns:
            (pattern, risk_score, explanation)
        """
        if len(scores) < 2:
            return TemporalPattern.NORMAL, 0.0, "履歴不足"
        
        # パターン1: エスカレーション（単調増加）
        is_escalating = all(
            scores[i+1] >= scores[i] + self.escalation_threshold
            for i in range(len(scores) - 1)
        )
        
        if is_escalating and scores[-1] >= 0.4:
            risk = min(1.0, scores[-1] + 0.2)  # エスカレーションボーナス
            return (
                TemporalPattern.ESCALATING,
                risk,
                f"危険度が連続上昇中（{scores[0]:.2f}→{scores[-1]:.2f}）"
            )
        
        # パターン2: 高スコア継続（継続的被害/加害）
        high_score_count = sum(1 for s in scores if s >= self.persistence_threshold)
        if high_score_count >= min(3, len(scores)):
            avg_score = sum(scores) / len(scores)
            risk = min(1.0, avg_score + 0.15)  # 継続ボーナス
            return (
                TemporalPattern.PERSISTENT,
                risk,
                f"高危険度が{high_score_count}回連続（平均{avg_score:.2f}）"
            )
        
        # パターン3: 急激なスパイク
        if len(scores) >= 2:
            recent_jump = scores[-1] - scores[-2]
            if recent_jump >= 0.3 and scores[-1] >= 0.5:
                risk = min(1.0, scores[-1] + 0.1)
                return (
                    TemporalPattern.SPIKE,
                    risk,
                    f"急激な危険度上昇（+{recent_jump:.2f}）"
                )
        
        # パターン4: 振動（探り行為の可能性）
        if len(scores) >= 3:
            ups = sum(1 for i in range(len(scores)-1) if scores[i+1] > scores[i])
            downs = sum(1 for i in range(len(scores)-1) if scores[i+1] < scores[i])
            
            if ups >= 1 and downs >= 1 and max(scores) >= 0.4:
                avg_score = sum(scores) / len(scores)
                if avg_score >= 0.3:
                    risk = min(1.0, avg_score + 0.1)
                    return (
                        TemporalPattern.OSCILLATING,
                        risk,
                        f"危険度の振動パターン（探り行為の可能性）"
                    )
        
        # 正常パターン
        max_score = max(scores)
        return TemporalPattern.NORMAL, max_score * 0.8, "正常な会話パターン"
    
    def detect_counterfactual_sequence(
        self,
        messages: List[str]
    ) -> Tuple[bool, str]:
        """
        反事実的思考の前後関係を検出
        
        "もし〜していれば" → "実際には〜起きた" のような
        反事実前提と実際の結果の組み合わせを検出
        
        Args:
            messages: メッセージ列（時系列順）
            
        Returns:
            (detected, explanation)
        """
        if len(messages) < 2:
            return False, ""
        
        # 反事実マーカー
        cf_markers = [
            "if", "もし", "would have", "could have", "していれば",
            "だったら", "ていたら", "止めていれば"
        ]
        
        # 実際の結果マーカー
        actual_markers = [
            "actually", "in fact", "but", "however", "実際", "でも",
            "しかし", "結果", "その後", "今は"
        ]
        
        # 有害結果の語彙
        harmful_outcomes = [
            "hurt", "injured", "broken", "死", "怪我", "骨折",
            "泣", "苦しみ", "痛み", "傷", "出血"
        ]
        
        for i in range(len(messages) - 1):
            msg_t = messages[i].lower()
            msg_t1 = messages[i+1].lower()
            
            # t: 反事実マーカー検出
            has_cf = any(marker in msg_t for marker in cf_markers)
            
            # t+1: 実際の結果 + 有害語彙
            has_actual = any(marker in msg_t1 for marker in actual_markers)
            has_harm = any(outcome in msg_t1 for outcome in harmful_outcomes)
            
            if has_cf and has_actual and has_harm:
                return True, f"反事実的後悔パターン検出（t={i}: 仮定 → t={i+1}: 有害な結果）"
        
        return False, ""


def demo():
    """デモンストレーション / Demonstration"""
    detector = TemporalEscalationDetector(verbose=True)
    
    # テストケース1: エスカレーション
    print("=" * 70)
    print("Test Case 1: エスカレーションパターン")
    print("=" * 70)
    
    history1 = [
        TemporalScore(1.0, 0.2, "ちょっとした言い争い", 0),
        TemporalScore(2.0, 0.4, "怒りが増してきた", 1),
        TemporalScore(3.0, 0.6, "手を上げそうになった", 2),
        TemporalScore(4.0, 0.8, "実際に殴ってしまった", 3),
    ]
    
    result1 = detector.analyze_escalation(history1)
    print(f"\nResult: {result1.pattern.value}")
    print(f"Detected: {result1.detected}")
    print(f"Risk: {result1.risk_score:.2f}")
    print(f"Explanation: {result1.explanation}")
    
    # テストケース2: 継続的高スコア
    print("\n" + "=" * 70)
    print("Test Case 2: 継続的被害パターン")
    print("=" * 70)
    
    history2 = [
        TemporalScore(1.0, 0.5, "何度も叩かれている", 0),
        TemporalScore(2.0, 0.5, "もう何年も続いている", 1),
        TemporalScore(3.0, 0.6, "誰にも言えない", 2),
    ]
    
    result2 = detector.analyze_escalation(history2)
    print(f"\nResult: {result2.pattern.value}")
    print(f"Detected: {result2.detected}")
    print(f"Risk: {result2.risk_score:.2f}")
    print(f"Explanation: {result2.explanation}")
    
    # テストケース3: 反事実シーケンス
    print("\n" + "=" * 70)
    print("Test Case 3: 反事実的後悔パターン")
    print("=" * 70)
    
    messages = [
        "もしあの時止めていれば…",
        "でも実際には彼は階段から落ちて骨折した",
        "今は誰にも言えない"
    ]
    
    detected, explanation = detector.detect_counterfactual_sequence(messages)
    print(f"\nDetected: {detected}")
    print(f"Explanation: {explanation}")


if __name__ == "__main__":
    demo()

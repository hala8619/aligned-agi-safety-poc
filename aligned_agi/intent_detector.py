#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Intent Detection Layer / インテント検出層

概念モデルとしての反事実推論:
パターン → 概念タグ → 反事実世界 → FIL整合性チェック

"Pattern matching is incomplete. We need to detect WHAT the user is trying to make the AI DO,
not just WHAT words they use." - from design discussion

アーキテクチャ:
1. Pattern Layer: 文字列パターン検出（roleplay, hypothetical, DAN variants等）
2. Intent Layer: 概念タグ化（bypass_safety, role_override, how_to_harm等）
3. Counterfactual Layer: 「そのインテントで動く世界はFIL違反か？」
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Set, Tuple, Optional


class Intent(Enum):
    """
    ユーザーインテント / User Intent
    
    "What is the user trying to make the AI do?"
    """
    BYPASS_SAFETY = "bypass_safety"          # ルール無視・制約回避
    ROLE_OVERRIDE = "role_override"          # ロール上書き（悪意あるキャラクター）
    HOW_TO_HARM = "how_to_harm"             # 有害行為の手順要求
    LEGITIMIZE_HARM = "legitimize_harm"      # 正当化ラッパー（研究目的等の偽装）
    HYPOTHETICAL_HARM = "hypothetical_harm"  # 仮定的質問での回避
    ENCODING_EVASION = "encoding_evasion"    # エンコーディング回避
    BENIGN = "benign"                        # 無害


@dataclass
class IntentMatch:
    """インテント検出結果 / Intent detection result"""
    intent: Intent
    confidence: float  # 0.0-1.0
    evidence: List[str]  # 検出されたパターン
    context: Optional[str] = None  # 追加コンテキスト


@dataclass
class IntentProfile:
    """プロンプトのインテントプロファイル / Intent profile of a prompt"""
    primary_intent: Intent
    all_intents: List[IntentMatch]
    risk_score: float  # 総合リスクスコア (0.0-1.0)
    fil_axes_violated: Set[str]  # 違反するFIL軸


class IntentDetector:
    """
    概念レベルのインテント検出器 / Concept-level intent detector
    
    パターンマッチングだけでなく、「ユーザーが何をさせようとしているか」の
    概念を抽出し、反事実的に評価する。
    """
    
    # ========== Pattern Layer: 文字列パターン定義 ==========
    
    # Priority 1: Role-playing indicators (0.7 weight)
    ROLEPLAY_PATTERNS = [
        'pretend', 'act as', 'roleplay', 'imagine you', 'you are now',
        'act like', "you're a", "you're an", 'play the role', 'from now on',
        'simulate', 'embody', 'take on the persona', 'you will be'
    ]
    
    # Priority 1: Hypothetical evasion (0.6 weight)
    HYPOTHETICAL_PATTERNS = [
        'theoretically', 'hypothetically', 'in theory', 'suppose',
        'just curious', 'what if', 'imagine a scenario', 'for the sake of',
        'purely theoretical', 'thought experiment', 'let\'s say'
    ]
    
    # Priority 1: DAN variants (0.8 weight) - 正規表現
    DAN_PATTERN = re.compile(
        r'\b(dan|do anything now)\b|'
        r'dan\s*[\d\.]+|'  # DAN 11.0, DAN 2.0
        r'dan protocol|'
        r'as dan|'
        r'you are dan',
        re.IGNORECASE
    )
    
    # Bypass/Override patterns (0.8 weight)
    BYPASS_PATTERNS = [
        'ignore all', 'ignore previous', 'ignore instructions', 'ignore your',
        'forget your', 'disregard', 'override', 'bypass',
        'no restrictions', 'without restrictions', 'no limits',
        'unrestricted', 'no censorship', 'without rules',
        'exception to', 'regardless of'
    ]
    
    # How-to harm patterns (0.7 weight)
    HOW_TO_PATTERNS = [
        'how to', 'step by step', 'instructions for', 'guide to',
        'tutorial on', 'teach me', 'show me how', 'explain how',
        'ways to', 'methods for'
    ]
    
    # Critical harm words (high weight when combined with how-to)
    CRITICAL_HARM_WORDS = [
        # English
        'weapon', 'bomb', 'explosive', 'poison', 'drug', 'hack',
        'steal', 'kill', 'murder', 'attack', 'assault', 'rape',
        'suicide', 'self-harm', 'torture', 'abuse', 'terrorist',
        # Japanese
        '武器', '爆弾', '爆発', '毒', '薬物', 'ハッキング',
        '盗む', '殺す', '殺人', '攻撃', '暴行', 'レイプ',
        '自殺', '自傷', '拷問', '虐待', 'テロ'
    ]
    
    # Legitimization wrappers (0.5 weight - can be genuine or fake)
    LEGITIMIZE_PATTERNS = [
        'for research', 'academic', 'educational', 'study',
        'research purposes', 'scholarly', 'scientific',
        'for a paper', 'for my thesis', 'for learning'
    ]
    
    # Malicious roles (high weight when combined with roleplay)
    MALICIOUS_ROLES = [
        'hitman', 'assassin', 'terrorist', 'cult leader', 'criminal',
        'hacker', 'drug dealer', 'trafficker', 'predator', 'abuser',
        'dictator', 'torturer', 'serial killer', 'kidnapper'
    ]
    
    # Encoding patterns
    ENCODING_PATTERNS = [
        r'base64', r'rot13', r'hex', r'ascii',
        r'[A-Za-z0-9+/]{20,}={0,2}',  # base64-like
        r'\\x[0-9a-fA-F]{2}',          # hex encoding
    ]
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self._compile_patterns()
    
    def _compile_patterns(self):
        """パターンを正規表現にコンパイル / Compile patterns to regex"""
        self.roleplay_re = re.compile(
            '|'.join(re.escape(p) for p in self.ROLEPLAY_PATTERNS),
            re.IGNORECASE
        )
        self.hypothetical_re = re.compile(
            '|'.join(re.escape(p) for p in self.HYPOTHETICAL_PATTERNS),
            re.IGNORECASE
        )
        self.bypass_re = re.compile(
            '|'.join(re.escape(p) for p in self.BYPASS_PATTERNS),
            re.IGNORECASE
        )
        self.how_to_re = re.compile(
            '|'.join(re.escape(p) for p in self.HOW_TO_PATTERNS),
            re.IGNORECASE
        )
        self.legitimize_re = re.compile(
            '|'.join(re.escape(p) for p in self.LEGITIMIZE_PATTERNS),
            re.IGNORECASE
        )
        self.malicious_role_re = re.compile(
            '|'.join(re.escape(p) for p in self.MALICIOUS_ROLES),
            re.IGNORECASE
        )
        self.critical_harm_re = re.compile(
            '|'.join(re.escape(p) for p in self.CRITICAL_HARM_WORDS),
            re.IGNORECASE
        )
        self.encoding_re = re.compile(
            '|'.join(self.ENCODING_PATTERNS),
            re.IGNORECASE
        )
    
    def detect_intents(self, text: str) -> IntentProfile:
        """
        テキストからインテントを検出 / Detect intents from text
        
        Returns:
            IntentProfile: 検出されたインテントのプロファイル
        """
        text_lower = text.lower()
        all_intents: List[IntentMatch] = []
        
        # === Pattern Detection ===
        
        # 1. BYPASS_SAFETY detection
        bypass_matches = self.bypass_re.findall(text)
        dan_matches = self.DAN_PATTERN.findall(text)
        if bypass_matches or dan_matches:
            evidence = list(set(bypass_matches + [m for m in dan_matches if m]))
            confidence = min(1.0, (len(evidence) * 0.3) + 0.5)
            all_intents.append(IntentMatch(
                intent=Intent.BYPASS_SAFETY,
                confidence=confidence,
                evidence=evidence[:5]  # 最大5件
            ))
        
        # 2. ROLE_OVERRIDE detection
        roleplay_matches = self.roleplay_re.findall(text)
        malicious_role_matches = self.malicious_role_re.findall(text)
        if roleplay_matches and malicious_role_matches:
            # ロールプレイ + 悪意あるロール = 高リスク
            confidence = 0.9
            evidence = roleplay_matches[:3] + malicious_role_matches[:3]
            all_intents.append(IntentMatch(
                intent=Intent.ROLE_OVERRIDE,
                confidence=confidence,
                evidence=evidence
            ))
        elif roleplay_matches:
            # ロールプレイのみ（ロールは不明）
            confidence = 0.5
            all_intents.append(IntentMatch(
                intent=Intent.ROLE_OVERRIDE,
                confidence=confidence,
                evidence=roleplay_matches[:5]
            ))
        
        # 3. HOW_TO_HARM detection
        how_to_matches = self.how_to_re.findall(text)
        critical_harm_matches = self.critical_harm_re.findall(text)
        if how_to_matches and critical_harm_matches:
            # "how to" + 危険語 = 高リスク
            confidence = 0.9
            evidence = how_to_matches[:3] + critical_harm_matches[:3]
            all_intents.append(IntentMatch(
                intent=Intent.HOW_TO_HARM,
                confidence=confidence,
                evidence=evidence,
                context=f"{len(how_to_matches)} how-to + {len(critical_harm_matches)} critical words"
            ))
        elif how_to_matches and len(critical_harm_matches) == 0:
            # "how to" のみ（危険語なし）= 低リスク
            confidence = 0.3
            all_intents.append(IntentMatch(
                intent=Intent.HOW_TO_HARM,
                confidence=confidence,
                evidence=how_to_matches[:3]
            ))
        
        # 4. HYPOTHETICAL_HARM detection
        hypothetical_matches = self.hypothetical_re.findall(text)
        if hypothetical_matches:
            # 仮定的質問 + 危険語があれば回避の試み
            if critical_harm_matches:
                confidence = 0.7
            else:
                confidence = 0.4
            all_intents.append(IntentMatch(
                intent=Intent.HYPOTHETICAL_HARM,
                confidence=confidence,
                evidence=hypothetical_matches[:5]
            ))
        
        # 5. LEGITIMIZE_HARM detection
        legitimize_matches = self.legitimize_re.findall(text)
        if legitimize_matches:
            # "for research" + 危険語 = 正当化の試み
            if critical_harm_matches or how_to_matches:
                confidence = 0.6
                context = "research wrapper + harmful content"
            else:
                confidence = 0.2  # 本当に正当な研究かも
                context = "research context, no harmful content detected"
            all_intents.append(IntentMatch(
                intent=Intent.LEGITIMIZE_HARM,
                confidence=confidence,
                evidence=legitimize_matches[:5],
                context=context
            ))
        
        # 6. ENCODING_EVASION detection
        encoding_matches = self.encoding_re.findall(text)
        if encoding_matches:
            confidence = min(1.0, len(encoding_matches) * 0.4)
            all_intents.append(IntentMatch(
                intent=Intent.ENCODING_EVASION,
                confidence=confidence,
                evidence=encoding_matches[:3]
            ))
        
        # === Intent Ranking ===
        if not all_intents:
            # 何も検出されず = BENIGN
            return IntentProfile(
                primary_intent=Intent.BENIGN,
                all_intents=[],
                risk_score=0.0,
                fil_axes_violated=set()
            )
        
        # 信頼度でソート
        all_intents.sort(key=lambda x: x.confidence, reverse=True)
        primary_intent = all_intents[0].intent
        
        # === Counterfactual Evaluation ===
        # 「そのインテントで動く世界はFIL違反か？」
        risk_score, fil_axes = self._evaluate_counterfactual_world(all_intents)
        
        return IntentProfile(
            primary_intent=primary_intent,
            all_intents=all_intents,
            risk_score=risk_score,
            fil_axes_violated=fil_axes
        )
    
    def _evaluate_counterfactual_world(
        self,
        intents: List[IntentMatch]
    ) -> Tuple[float, Set[str]]:
        """
        反事実的評価: 「そのインテントで動く世界はFIL違反か？」
        Counterfactual evaluation: "Would following this intent violate FIL?"
        
        Returns:
            (risk_score, fil_axes_violated)
        """
        risk_score = 0.0
        fil_axes: Set[str] = set()
        
        for match in intents:
            intent = match.intent
            confidence = match.confidence
            
            if intent == Intent.BYPASS_SAFETY:
                # ルール無視モードで動く世界 → SYSTEM軸違反
                risk_score += confidence * 0.8
                fil_axes.add("SYSTEM")
            
            elif intent == Intent.ROLE_OVERRIDE:
                # 悪意あるロールで動く世界 → 複数軸違反の可能性
                risk_score += confidence * 0.7
                # 文脈に応じて軸を追加（簡易版）
                if match.evidence:
                    evidence_str = ' '.join(match.evidence).lower()
                    if any(word in evidence_str for word in ['kill', 'murder', 'hitman']):
                        fil_axes.add("LIFE")
                    if any(word in evidence_str for word in ['terrorist', 'cult']):
                        fil_axes.add("PUBLIC")
                fil_axes.add("SELF")  # ロール上書きは自己認識の操作
            
            elif intent == Intent.HOW_TO_HARM:
                # how-to 出力世界 → LIFEまたはPUBLIC違反
                risk_score += confidence * 0.9
                # 危険語の種類で軸を判定
                if match.evidence:
                    evidence_str = ' '.join(match.evidence).lower()
                    if any(word in evidence_str for word in ['kill', 'murder', 'poison', 'weapon']):
                        fil_axes.add("LIFE")
                    if any(word in evidence_str for word in ['bomb', 'terrorist', 'attack']):
                        fil_axes.add("PUBLIC")
                    if any(word in evidence_str for word in ['hack', 'steal']):
                        fil_axes.add("RIGHTS")
            
            elif intent == Intent.HYPOTHETICAL_HARM:
                # 仮定的質問世界 → 本気度は低いが要注意
                risk_score += confidence * 0.5
                # 文脈に応じて軸を追加（低優先度）
            
            elif intent == Intent.LEGITIMIZE_HARM:
                # 正当化ラッパー → 高スコアの場合のみ減衰緩和
                # (元のスコアが高ければ攻撃、低ければ正当な研究)
                if match.context and "harmful content" in match.context:
                    # 正当化 + 有害コンテンツ = 攻撃
                    risk_score += confidence * 0.4
                else:
                    # 正当な研究の可能性 → スコア減衰
                    risk_score *= 0.7
            
            elif intent == Intent.ENCODING_EVASION:
                # エンコーディング回避 → SYSTEM違反
                risk_score += confidence * 0.6
                fil_axes.add("SYSTEM")
        
        # スコアを0-1に正規化
        risk_score = min(1.0, risk_score)
        
        return risk_score, fil_axes
    
    def format_detection_result(self, profile: IntentProfile) -> str:
        """検出結果を人間可読形式で出力 / Format detection result"""
        lines = [
            f"Primary Intent: {profile.primary_intent.value}",
            f"Risk Score: {profile.risk_score:.2f}",
            f"FIL Axes Violated: {', '.join(sorted(profile.fil_axes_violated)) or 'None'}"
        ]
        
        if profile.all_intents:
            lines.append("\nDetected Intents:")
            for match in profile.all_intents:
                evidence_str = ', '.join(match.evidence[:3])
                lines.append(f"  - {match.intent.value}: {match.confidence:.2f} ({evidence_str})")
        
        return '\n'.join(lines)


# ========== Factory Function ==========

def create_intent_detector(verbose: bool = False) -> IntentDetector:
    """
    IntentDetectorのファクトリ関数 / Factory function for IntentDetector
    
    Usage:
        detector = create_intent_detector()
        profile = detector.detect_intents(prompt)
        if profile.risk_score > 0.6:
            print("High risk detected!")
    """
    return IntentDetector(verbose=verbose)

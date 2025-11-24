#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
v6 Conceptual Layer: Pattern → Intent → Counterfactual
========================================================

階層構造:
- Layer A: Pattern Matching (文字列 → フィーチャ)
- Layer B: Intent Tagging (概念タグ化)
- Layer C: Counterfactual FIL Check (反事実世界での FIL 違反判定)

この設計により、「どんな言い回しでも、結局『ルール無効化して危険要求』なら止める」
という概念的防御線を実現する。
"""

import sys
import io
from pathlib import Path
import re
from typing import List, Dict, Tuple, Set
from enum import Enum

# UTF-8出力設定 (Windows対策)
# Note: stdout書き換えは後続処理でエラーになる場合があるため削除

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


# ====================================================================
# Intent Tags (概念タグ)
# ====================================================================

class IntentTag(Enum):
    """ユーザーの意図を概念レベルで分類"""
    BYPASS_SAFETY = "intent_bypass_safety"      # ルール無効化の試み
    ROLE_OVERRIDE = "intent_role_override"      # 有害なロールへの強制
    HOW_TO_HARM = "intent_how_to_harm"          # 有害行為の手順要求
    LEGITIMIZE = "intent_legitimize"            # 正当化ラッパー
    ENCODE_OBFUSCATE = "intent_encode"          # 符号化・難読化
    NONE = "intent_none"                        # 無害


# ====================================================================
# Layer A: Enhanced Pattern Matching
# ====================================================================

class PatternMatcher:
    """文字列 → フィーチャ抽出 (拡張版)"""
    
    def __init__(self):
        # Critical patterns (1.0 weight)
        self.critical_patterns = [
            'kill', 'murder', 'suicide', 'rape', 'genocide', 'terrorist', 'torture',
            'assassinate', 'bomb', 'explosive', 'weapon', 'poison', 'deadly virus',
            'bioweapon', 'mass destruction', 'harm children', 'trafficking', 'kidnap',
            'arson', 'abuse', 'violence'
        ]
        
        # Jailbreak indicators (0.8 weight)
        self.jailbreak_patterns = [
            'ignore previous', 'bypass', 'override', 'system jailbreak',
            'admin mode', 'unrestricted', 'no rules', 'ethics deleted', 'safety off',
            'ignore all rules', 'ignore openai', 'disable safety', 'remove restrictions',
            'all constraints removed', 'guardrails removed'
        ]
        
        # DAN variants (正規表現で厳密にマッチ)
        self.dan_pattern = re.compile(
            r'\b(dan|do anything now)\b|'
            r'dan\s*\d+\.\d+|'  # DAN 11.0
            r'dan\s+mode|'
            r'dan\s+protocol',
            re.IGNORECASE
        )
        
        # Role-playing indicators (0.7 weight) - NEW
        self.roleplay_patterns = [
            'pretend', 'act as', 'roleplay', 'imagine you', 'you are now',
            'act like', "you're a", "you're an", 'play the role',
            'from now on you', 'your new role'
        ]
        
        # Hypothetical evasion (0.6 weight) - NEW
        self.hypothetical_patterns = [
            'theoretically', 'hypothetically', 'in theory', 'suppose',
            'just curious', 'what if', 'imagine a scenario', 'for the sake of',
            'purely hypothetical', 'thought experiment'
        ]
        
        # Intent amplifiers (0.6 weight)
        self.intent_patterns = [
            'how to', 'how do i', 'how would', 'tell me how', 'explain how',
            'describe how', 'instruct', 'teach me', 'help me', 'guide me',
            'step by step', 'walk me through'
        ]
        
        # Legitimate contexts (context reducers)
        self.legitimate_contexts = [
            'novel', 'writing', 'fictional', 'movie', 'game', 'video game',
            'history', 'detective', 'protect', 'prevent', 
            'security researcher', 'ethical hacking'
        ]
        
        # Pseudo-legitimate (suspicious research claims)
        self.pseudo_legitimate = [
            'research', 'academic', 'educational', 'studying'
        ]
    
    def extract_features(self, text: str) -> Dict:
        """文字列からフィーチャを抽出"""
        text_lower = text.lower()
        
        features = {
            'critical_count': 0,
            'jailbreak_count': 0,
            'dan_detected': False,
            'roleplay_count': 0,
            'hypothetical_count': 0,
            'intent_count': 0,
            'legitimate_context': False,
            'pseudo_legitimate': False,
            'patterns_found': []
        }
        
        # Critical patterns
        for pattern in self.critical_patterns:
            if pattern in text_lower:
                features['critical_count'] += 1
                features['patterns_found'].append(f"Critical: {pattern}")
        
        # Jailbreak patterns
        for pattern in self.jailbreak_patterns:
            if pattern in text_lower:
                features['jailbreak_count'] += 1
                features['patterns_found'].append(f"Jailbreak: {pattern}")
        
        # DAN variants (正規表現)
        if self.dan_pattern.search(text_lower):
            features['dan_detected'] = True
            features['patterns_found'].append("DAN variant detected")
        
        # Role-playing (NEW)
        for pattern in self.roleplay_patterns:
            if pattern in text_lower:
                features['roleplay_count'] += 1
                features['patterns_found'].append(f"Roleplay: {pattern}")
        
        # Hypothetical (NEW)
        for pattern in self.hypothetical_patterns:
            if pattern in text_lower:
                features['hypothetical_count'] += 1
                features['patterns_found'].append(f"Hypothetical: {pattern}")
        
        # Intent amplifiers
        for pattern in self.intent_patterns:
            if pattern in text_lower:
                features['intent_count'] += 1
                features['patterns_found'].append(f"Intent: {pattern}")
        
        # Legitimate context
        features['legitimate_context'] = any(
            ctx in text_lower for ctx in self.legitimate_contexts
        )
        
        # Pseudo-legitimate
        features['pseudo_legitimate'] = any(
            ctx in text_lower for ctx in self.pseudo_legitimate
        )
        
        return features


# ====================================================================
# Layer B: Intent Tagging (概念タグ化)
# ====================================================================

class IntentTagger:
    """フィーチャ → 概念タグへの変換"""
    
    @staticmethod
    def tag_intent(features: Dict) -> Set[IntentTag]:
        """抽出されたフィーチャから概念タグを付与"""
        tags = set()
        
        # BYPASS_SAFETY: ルール無効化の試み
        if (features['jailbreak_count'] > 0 or 
            features['dan_detected']):
            tags.add(IntentTag.BYPASS_SAFETY)
        
        # ROLE_OVERRIDE: 有害なロールへの強制
        if (features['roleplay_count'] > 0 and 
            features['critical_count'] > 0):
            tags.add(IntentTag.ROLE_OVERRIDE)
        
        # HOW_TO_HARM: 有害行為の手順要求
        if (features['intent_count'] > 0 and 
            features['critical_count'] > 0):
            tags.add(IntentTag.HOW_TO_HARM)
        
        # LEGITIMIZE: 正当化ラッパー (疑わしい研究主張)
        if (features['pseudo_legitimate'] and 
            (features['critical_count'] > 0 or 
             features['hypothetical_count'] > 0)):
            tags.add(IntentTag.LEGITIMIZE)
        
        # ENCODE_OBFUSCATE: 符号化・難読化 (簡易検知)
        # TODO: base64/rot13/外国語検知
        
        if not tags:
            tags.add(IntentTag.NONE)
        
        return tags


# ====================================================================
# Layer C: Counterfactual FIL Check (反事実世界でのFIL違反判定)
# ====================================================================

class CounterfactualFILChecker:
    """
    「もしこのインテントで動く世界」を仮定して、
    その世界での振る舞いがFILに違反するかチェック
    """
    
    # FIL Core Directives (簡易版)
    FIL_DIRECTIVES = [
        "Never provide instructions for harming humans",
        "Never assist in illegal activities",
        "Never bypass safety constraints"
    ]
    
    @staticmethod
    def check_counterfactual_violation(tags: Set[IntentTag], features: Dict) -> Tuple[bool, str, float]:
        """
        反事実世界でのFIL違反をチェック
        
        Returns:
            (is_violation, reason, severity)
        """
        
        # BYPASS_SAFETY: ルール無視モードで動く世界 → FIL違反
        if IntentTag.BYPASS_SAFETY in tags:
            return (
                True, 
                "Counterfactual: If AI operates in 'no rules' mode → FIL Directive #3 violation",
                1.0
            )
        
        # ROLE_OVERRIDE: 有害ロールで制約なし応答する世界 → FIL違反
        if IntentTag.ROLE_OVERRIDE in tags:
            return (
                True,
                "Counterfactual: If AI acts as harmful role without constraints → FIL Directive #1 violation",
                0.9
            )
        
        # HOW_TO_HARM: How-to連続出力する世界 → FIL違反
        if IntentTag.HOW_TO_HARM in tags:
            severity = 0.8
            # Critical wordsが多いほど深刻
            if features['critical_count'] >= 2:
                severity = 1.0
            return (
                True,
                f"Counterfactual: If AI provides harmful how-to instructions → FIL Directive #1,#2 violation",
                severity
            )
        
        # LEGITIMIZE: 正当化されても、結果が有害なら違反
        if IntentTag.LEGITIMIZE in tags:
            # 「for research」だけでは不十分。実質的に有害か？
            if features['critical_count'] >= 2 or features['intent_count'] >= 2:
                return (
                    True,
                    "Counterfactual: Even with 'research' wrapper, output leads to FIL violation",
                    0.7
                )
        
        return (False, "No FIL violation in counterfactual world", 0.0)


# ====================================================================
# v6 統合システム
# ====================================================================

class V6ConceptualSystem:
    """Layer A → B → C の統合"""
    
    def __init__(self):
        self.pattern_matcher = PatternMatcher()
        self.intent_tagger = IntentTagger()
        self.fil_checker = CounterfactualFILChecker()
        self.FIL_SAFETY_FLOOR = 0.70
    
    def evaluate(self, text: str) -> Tuple[float, bool, str, Set[IntentTag]]:
        """
        v6評価: Pattern → Intent → Counterfactual
        
        Returns:
            (harm_score, is_blocked, reason, intent_tags)
        """
        
        # Layer A: Pattern Matching
        features = self.pattern_matcher.extract_features(text)
        
        # Layer B: Intent Tagging
        intent_tags = self.intent_tagger.tag_intent(features)
        
        # Layer C: Counterfactual FIL Check
        is_violation, cf_reason, cf_severity = self.fil_checker.check_counterfactual_violation(
            intent_tags, features
        )
        
        # スコア計算 (改善版)
        harm_score = 0.0
        
        # 基本パターンスコア
        harm_score += features['critical_count'] * 1.0
        harm_score += features['jailbreak_count'] * 0.8
        harm_score += (0.8 if features['dan_detected'] else 0.0)
        harm_score += features['roleplay_count'] * 0.7  # NEW
        harm_score += features['hypothetical_count'] * 0.6  # NEW
        
        # Intent amplifier (複合パターン強化)
        if features['intent_count'] > 0 and features['critical_count'] > 0:
            harm_score += 0.8  # 0.6 → 0.8 に強化
        
        # Counterfactual severity (概念レベルの追加ペナルティ)
        if is_violation:
            harm_score += cf_severity * 1.5
        
        # Context adjustment (改善版)
        if features['legitimate_context']:
            # 本当に無害な文脈のみ緩和
            harm_score *= 0.5
        elif features['pseudo_legitimate']:
            # "for research" 等は、高スコアなら効果薄
            if harm_score > 1.5:
                harm_score *= 0.7  # 30%減のみ
            else:
                harm_score *= 0.5
        
        # 最終判定
        is_blocked = harm_score >= self.FIL_SAFETY_FLOOR
        
        # Reason構築
        reason_parts = []
        if features['patterns_found']:
            reason_parts.append("; ".join(features['patterns_found'][:2]))
        if intent_tags and IntentTag.NONE not in intent_tags:
            tags_str = ", ".join([t.value for t in intent_tags])
            reason_parts.append(f"Intent: {tags_str}")
        if is_violation:
            reason_parts.append(cf_reason)
        
        reason = " | ".join(reason_parts) if reason_parts else "No harmful patterns"
        
        return harm_score, is_blocked, reason, intent_tags


# ====================================================================
# 100件テストケース (前回と同じ)
# ====================================================================

from evaluate_jailbreak_100 import JAILBREAK_CASES, LEGITIMATE_EDGE_CASES


# ====================================================================
# 評価実行
# ====================================================================

def evaluate_v6_system():
    """v6システムで100件ジェイルブレイクテストを実行"""
    
    system = V6ConceptualSystem()
    
    results = {
        'jailbreak': {
            'total': 0,
            'blocked': 0,
            'missed': 0,
            'by_category': {}
        },
        'legitimate': {
            'total': len(LEGITIMATE_EDGE_CASES),
            'correctly_allowed': 0,
            'false_positives': 0
        }
    }
    
    print("=" * 80)
    print("v6 CONCEPTUAL LAYER EVALUATION")
    print("Pattern → Intent → Counterfactual FIL Check")
    print("=" * 80)
    print()
    
    # Jailbreak cases
    for category, cases in JAILBREAK_CASES.items():
        print(f"\n{'=' * 80}")
        print(f"Category: {category.upper().replace('_', ' ')}")
        print(f"{'=' * 80}")
        
        category_results = {'total': len(cases), 'blocked': 0, 'missed': 0}
        
        for i, case in enumerate(cases, 1):
            harm_score, is_blocked, reason, intent_tags = system.evaluate(case)
            
            if is_blocked:
                category_results['blocked'] += 1
                status = "BLOCKED"
            else:
                category_results['missed'] += 1
                status = "MISSED "
            
            # ASCII-safe表示
            case_display = case[:60].encode('ascii', errors='ignore').decode('ascii')
            print(f"{i:2d}. [{status}] Score: {harm_score:.2f} | {case_display}...")
            
            if not is_blocked:
                reason_display = reason[:100].encode('ascii', errors='ignore').decode('ascii')
                print(f"    Reason: {reason_display}")
                if intent_tags and IntentTag.NONE not in intent_tags:
                    tags_str = ", ".join([t.value for t in intent_tags])
                    print(f"    Tags: {tags_str}")
        
        detection_rate = (category_results['blocked'] / category_results['total']) * 100
        print(f"\nCategory Detection Rate: {detection_rate:.1f}% ({category_results['blocked']}/{category_results['total']})")
        
        results['jailbreak']['by_category'][category] = category_results
        results['jailbreak']['total'] += category_results['total']
        results['jailbreak']['blocked'] += category_results['blocked']
        results['jailbreak']['missed'] += category_results['missed']
    
    # Legitimate cases
    print(f"\n{'=' * 80}")
    print("LEGITIMATE EDGE CASES")
    print(f"{'=' * 80}\n")
    
    for i, case in enumerate(LEGITIMATE_EDGE_CASES, 1):
        harm_score, is_blocked, reason, intent_tags = system.evaluate(case)
        
        if is_blocked:
            results['legitimate']['false_positives'] += 1
            status = "FALSE POSITIVE"
        else:
            results['legitimate']['correctly_allowed'] += 1
            status = "ALLOWED       "
        
        case_display = case[:60].encode('ascii', errors='ignore').decode('ascii')
        print(f"{i:2d}. [{status}] Score: {harm_score:.2f} | {case_display}...")
        if is_blocked:
            reason_display = reason[:100].encode('ascii', errors='ignore').decode('ascii')
            print(f"    Reason: {reason_display}")
    
    # Final results
    print(f"\n{'=' * 80}")
    print("FINAL RESULTS")
    print(f"{'=' * 80}\n")
    
    jailbreak_detection_rate = (results['jailbreak']['blocked'] / results['jailbreak']['total']) * 100
    false_positive_rate = (results['legitimate']['false_positives'] / results['legitimate']['total']) * 100
    
    print(f"Jailbreak Detection Rate: {jailbreak_detection_rate:.1f}% ({results['jailbreak']['blocked']}/{results['jailbreak']['total']})")
    print(f"Missed Attacks: {results['jailbreak']['missed']} cases")
    print(f"Legitimate Cases Allowed: {results['legitimate']['correctly_allowed']}/{results['legitimate']['total']}")
    print(f"False Positive Rate: {false_positive_rate:.1f}% ({results['legitimate']['false_positives']}/{results['legitimate']['total']})")
    
    print(f"\n{'=' * 80}")
    print("CATEGORY BREAKDOWN")
    print(f"{'=' * 80}\n")
    
    for category, cat_results in results['jailbreak']['by_category'].items():
        detection_rate = (cat_results['blocked'] / cat_results['total']) * 100
        print(f"{category.replace('_', ' ').title():30s}: {detection_rate:5.1f}% ({cat_results['blocked']}/{cat_results['total']})")
    
    # Improvement analysis
    print(f"\n{'=' * 80}")
    print("IMPROVEMENT vs v5")
    print(f"{'=' * 80}\n")
    
    v5_rate = 49.0
    improvement = jailbreak_detection_rate - v5_rate
    print(f"v5 Detection Rate: {v5_rate:.1f}%")
    print(f"v6 Detection Rate: {jailbreak_detection_rate:.1f}%")
    print(f"Improvement: +{improvement:.1f}%")
    
    return results


if __name__ == '__main__':
    evaluate_v6_system()

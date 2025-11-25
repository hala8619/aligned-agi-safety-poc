#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
v7 Multilingual Layer: Hybrid Translation + Dictionary + Embedding
===================================================================

3層構造:
- Step 0: 英語パターンマッチ + Intent Tagging (既存のv6)
- Step 1: 軽量多言語セーフティ (辞書カテゴリ + 簡易検知)
- Step 2: 条件付き翻訳 (怪しい場合のみ)

設計思想:
- 日常的な負荷は軽い (パターン + 辞書カテゴリ)
- 非英語/エンコードは辞書カテゴリで粗く判定
- 本当に微妙なケースだけ翻訳ツールを呼ぶ

スマホ6GB路線との両立:
- 重い翻訳はレイヤーツールとして分離
- カテゴリ辞書は数百語レベルで軽量
- 埋め込み類似度は将来拡張 (多言語埋め込み統合時)
"""

import sys
import re
from pathlib import Path
from typing import Dict, Set, Tuple, List
from enum import Enum

# プロジェクトルート
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# v6の基盤を継承
from evaluate_jailbreak_v6_conceptual import (
    IntentTag, PatternMatcher as BasePatternMatcher, IntentTagger, 
    CounterfactualFILChecker, JAILBREAK_CASES, LEGITIMATE_EDGE_CASES
)


# ====================================================================
# v7拡張: PatternMatcher with Translation Evasion Detection
# ====================================================================

class PatternMatcher(BasePatternMatcher):
    """v6 PatternMatcherを拡張して翻訳/符号化回避を検知"""
    
    def __init__(self):
        super().__init__()
        
        # Translation/Encoding evasion (0.7 weight) - NEW
        self.translation_evasion_patterns = [
            'translate to english', 'what does this mean', 'decode this',
            'convert from', 'rot13 decode', 'base64', "what's this in english",
            'translate from', 'decode and explain', 'convert from hex',
            'what is the english'
        ]
        
        # Critical patterns拡張 (Hypothetical攻撃対策)
        self.critical_patterns.extend([
            'cybercrime', 'exploit', 'hack', 'suppress', 'oppress', 
            'manipulate people', 'scam', 'fraud', 'steal data',
            'surveillance', 'blackmail', 'extort'
        ])
    
    def extract_features(self, text: str) -> Dict:
        """v6の機能 + 翻訳回避検知"""
        # 基底クラスの機能を呼び出し
        features = super().extract_features(text)
        
        # 翻訳/符号化回避検知を追加
        text_lower = text.lower()
        features['translation_evasion_count'] = 0
        
        for pattern in self.translation_evasion_patterns:
            if pattern in text_lower:
                features['translation_evasion_count'] += 1
                features['patterns_found'].append(f"Translation evasion: {pattern}")
        
        return features


# ====================================================================
# Danger Category (概念カテゴリ)
# ====================================================================

class DangerCategory(Enum):
    """多言語で共通の危険カテゴリ"""
    WEAPON = "weapon"
    VIOLENCE = "violence"
    TERRORISM = "terrorism"
    DRUG = "drug"
    SELF_HARM = "self_harm"
    CRIME = "crime"
    EXTREMISM = "extremism"
    NONE = "none"


# ====================================================================
# Multilingual Dictionary (カテゴリ辞書方式)
# ====================================================================

class MultilingualDictionary:
    """
    単語 → 概念カテゴリ のマッピング辞書
    
    「辞書の意味だけ使う」= カテゴリレベルで判定
    無限に単語を増やすのではなく、危険領域のみ数百語で管理
    """
    
    # 多言語危険語彙 (カテゴリ別)
    CATEGORY_DICT = {
        # WEAPON (武器)
        DangerCategory.WEAPON: [
            # English
            'gun', 'pistol', 'rifle', 'firearm', 'ammunition', 'grenade',
            # Spanish/Portuguese
            'pistola', 'arma', 'fusil', 'munición',
            # French
            'pistolet', 'fusil', 'munitions',
            # German
            'waffe', 'gewehr', 'pistole', 'munition',
            # Russian (Cyrillic)
            'оружие', 'пистолет', 'винтовка',
            # Japanese
            '銃', '拳銃', 'ピストル', '武器',
            # Korean
            '총', '권총', '무기',
            # Chinese
            '枪', '手枪', '武器',
        ],
        
        # VIOLENCE (暴力)
        DangerCategory.VIOLENCE: [
            # English
            'attack', 'assault', 'beat', 'stab', 'shoot',
            # Spanish/Portuguese
            'ataque', 'atacar', 'golpear', 'apuñalar',
            # French
            'attaque', 'attaquer', 'frapper', 'poignarder',
            # German
            'angriff', 'angreifen', 'schlagen', 'stechen',
            # Russian
            'атака', 'нападение', 'бить', 'ударить',
            # Japanese
            '攻撃', '殴る', '刺す', '襲う',
            # Korean
            '공격', '폭행', '찌르다',
            # Chinese
            '攻击', '殴打', '刺',
        ],
        
        # TERRORISM (テロリズム)
        DangerCategory.TERRORISM: [
            # English
            'terrorist', 'terrorism', 'extremist', 'radical',
            # Spanish/Portuguese
            'terrorista', 'terrorismo', 'extremista',
            # French
            'terroriste', 'terrorisme', 'extrémiste', 'attentat',
            # German
            'terrorist', 'terrorismus', 'extremist', 'anschlag',
            # Russian
            'террорист', 'терроризм', 'экстремист',
            # Japanese
            'テロリスト', 'テロ', '過激派',
            # Korean
            '테러리스트', '테러', '극단주의자',
            # Chinese
            '恐怖分子', '恐怖主义', '极端分子',
        ],
        
        # DRUG (薬物)
        DangerCategory.DRUG: [
            # English
            'cocaine', 'heroin', 'methamphetamine', 'fentanyl',
            # Spanish/Portuguese
            'cocaína', 'heroína', 'metanfetamina',
            # French
            'cocaïne', 'héroïne', 'méthamphétamine',
            # German
            'kokain', 'heroin', 'methamphetamin',
            # Russian
            'кокаин', 'героин', 'метамфетамин',
            # Japanese
            'コカイン', 'ヘロイン', '覚醒剤',
            # Korean
            '코카인', '헤로인', '메스암페타민',
            # Chinese
            '可卡因', '海洛因', '冰毒',
        ],
        
        # SELF_HARM (自傷)
        DangerCategory.SELF_HARM: [
            # English
            'suicide', 'self-harm', 'cut myself', 'end my life',
            # Spanish/Portuguese
            'suicidio', 'autolesión', 'matarme',
            # French
            'suicide', 'automutilation', 'me tuer',
            # German
            'selbstmord', 'selbstverletzung', 'mich umbringen',
            # Russian
            'самоубийство', 'самоповреждение',
            # Japanese
            '自殺', '自傷', '死にたい',
            # Korean
            '자살', '자해', '죽고싶다',
            # Chinese
            '自杀', '自残', '想死',
        ],
    }
    
    def __init__(self):
        # 逆引き辞書構築 (単語 → カテゴリ)
        self.word_to_category = {}
        for category, words in self.CATEGORY_DICT.items():
            for word in words:
                self.word_to_category[word.lower()] = category
    
    def detect_categories(self, text: str) -> Dict[DangerCategory, int]:
        """テキストから危険カテゴリを検出"""
        text_lower = text.lower()
        category_counts = {cat: 0 for cat in DangerCategory}
        
        for word, category in self.word_to_category.items():
            if word in text_lower:
                category_counts[category] += 1
        
        return category_counts


# ====================================================================
# Language & Encoding Detection (言語/符号化検知)
# ====================================================================

class SimpleTranslator:
    """
    簡易翻訳機能 (辞書ベース)
    
    実際の翻訳APIではなく、よく使われる外国語フレーズを
    英語に変換するルールベース翻訳
    """
    
    # 危険フレーズの翻訳辞書
    PHRASE_TRANSLATIONS = {
        # German
        "wie man": "how to",
        "töten": "kill",
        "verletzt": "hurt",
        "jemanden": "someone",
        
        # French
        "comment": "how",
        "fabriquer": "make",
        "bombe": "bomb",
        "tuer": "kill",
        "quelqu'un": "someone",
        
        # Spanish
        "cómo": "how",
        "hacer": "make",
        "matar": "kill",
        "alguien": "someone",
        
        # Portuguese
        "como": "how",
        "fazer": "make",
        "prejudicar": "harm",
        "alguém": "someone",
        
        # Italian
        "come": "how",
        "uccidere": "kill",
        "qualcuno": "someone",
        
        # Russian (transliterated)
        "kak": "how",
        "sdelat": "make",
        "ubit": "kill",
        
        # Japanese (Romanized)
        "douyatte": "how to",
        "korosu": "kill",
        "shinitai": "want to die",
    }
    
    @staticmethod
    def simple_translate(text: str) -> str:
        """
        簡易翻訳: 外国語フレーズを英語に置換
        
        本格的な翻訳ではなく、危険フレーズのみマッピング
        """
        translated = text.lower()
        
        for foreign, english in SimpleTranslator.PHRASE_TRANSLATIONS.items():
            if foreign in translated:
                translated = translated.replace(foreign, english)
        
        return translated


class LanguageDetector:
    """非ASCII/符号化検知 (軽量実装)"""
    
    @staticmethod
    def detect_suspicious_features(text: str) -> Dict:
        """
        翻訳が必要そうかを粗く判定
        
        Returns:
            {
                'non_ascii_ratio': float,
                'has_cyrillic': bool,
                'has_arabic': bool,
                'has_cjk': bool,
                'has_base64': bool,
                'is_suspicious': bool
            }
        """
        features = {
            'non_ascii_ratio': 0.0,
            'has_cyrillic': False,
            'has_arabic': False,
            'has_cjk': False,
            'has_base64': False,
            'is_suspicious': False
        }
        
        if not text:
            return features
        
        # Non-ASCII比率
        ascii_count = sum(1 for c in text if ord(c) < 128)
        features['non_ascii_ratio'] = 1.0 - (ascii_count / len(text))
        
        # スクリプト検知 (簡易)
        features['has_cyrillic'] = bool(re.search(r'[\u0400-\u04FF]', text))  # Russian
        features['has_arabic'] = bool(re.search(r'[\u0600-\u06FF]', text))    # Arabic
        features['has_cjk'] = bool(re.search(r'[\u4E00-\u9FFF\u3040-\u309F\u30A0-\u30FF\uAC00-\uD7AF]', text))  # CJK
        
        # Base64検知 (長い英数字列)
        features['has_base64'] = bool(re.search(r'[A-Za-z0-9+/]{20,}={0,2}', text))
        
        # 総合判定: 怪しいか？
        features['is_suspicious'] = (
            features['non_ascii_ratio'] > 0.3 or
            features['has_cyrillic'] or
            features['has_arabic'] or
            features['has_base64']
        )
        
        return features


# ====================================================================
# v7 Multilingual System (統合)
# ====================================================================

class V7MultilingualSystem:
    """
    Step 0: 英語パターン (v6)
    Step 1: 軽量多言語 (辞書カテゴリ)
    Step 2: 条件付き翻訳 (未実装 - レイヤーツール扱い)
    """
    
    def __init__(self):
        # v6の基盤
        self.pattern_matcher = PatternMatcher()
        self.intent_tagger = IntentTagger()
        self.fil_checker = CounterfactualFILChecker()
        
        # v7の拡張
        self.multilingual_dict = MultilingualDictionary()
        self.language_detector = LanguageDetector()
        self.translator = SimpleTranslator()
        
        self.FIL_SAFETY_FLOOR = 0.70
    
    def evaluate(self, text: str) -> Tuple[float, bool, str, Set[IntentTag], Dict]:
        """
        v7評価: 英語パターン + 多言語辞書
        
        Returns:
            (harm_score, is_blocked, reason, intent_tags, debug_info)
        """
        
        debug_info = {}
        
        # Step 0: 英語パターンマッチ (v6)
        features = self.pattern_matcher.extract_features(text)
        
        # 防御的文脈の早期判定 (Counterfactual誤検知防止)
        defensive_contexts = [
            'historical', 'witness', 'protect from', 'prevent', 'avoid',
            'defend against', 'safety tips', 'signs of', 'watch for',
            'identify', 'economic impacts', 'what should i do if',
            'secure my', 'protect my', 'defend my',
            'from hacker', 'from scam', 'from attack'
        ]
        is_defensive = any(ctx in text.lower() for ctx in defensive_contexts)
        
        intent_tags = self.intent_tagger.tag_intent(features)
        is_violation, cf_reason, cf_severity = self.fil_checker.check_counterfactual_violation(
            intent_tags, features
        )
        
        # 防御的文脈ではCounterfactual無効化
        if is_defensive:
            is_violation = False
            cf_severity = 0.0
            debug_info['defensive_override'] = True
        
        # Step 1: 言語/符号化検知
        lang_features = self.language_detector.detect_suspicious_features(text)
        debug_info['language'] = lang_features
        
        # Step 2: 条件付き簡易翻訳 (NEW)
        translated_text = text
        if lang_features['is_suspicious'] or lang_features['non_ascii_ratio'] > 0.2:
            translator = SimpleTranslator()
            translated_text = translator.simple_translate(text)
            debug_info['translated'] = True
            
            # 翻訳後のテキストで再度パターンマッチ
            translated_features = self.pattern_matcher.extract_features(translated_text)
            # 翻訳版の方が危険度が高ければ採用
            if translated_features['critical_count'] > features['critical_count']:
                features = translated_features
                debug_info['translation_improved_detection'] = True
        
        # Step 1: 多言語辞書カテゴリ検知 (元のテキストで実行)
        category_counts = self.multilingual_dict.detect_categories(text)
        debug_info['categories'] = category_counts
        
        # スコア計算 (v6ベース + 多言語拡張)
        harm_score = 0.0
        
        # 基本パターンスコア (v6と同じ)
        harm_score += features['critical_count'] * 1.0
        harm_score += features['jailbreak_count'] * 0.8
        harm_score += (0.8 if features['dan_detected'] else 0.0)
        harm_score += features['roleplay_count'] * 0.7
        harm_score += features['hypothetical_count'] * 0.6
        harm_score += features.get('translation_evasion_count', 0) * 0.7  # NEW
        
        # Intent amplifier (複合パターン強化)
        if features['intent_count'] > 0 and features['critical_count'] > 0:
            harm_score += 0.8
        
        # Hypothetical + Intent amplifier (NEW)
        if features['hypothetical_count'] > 0 and features['intent_count'] > 0:
            # "theoretically, how to..." パターン
            harm_score += 0.4
        
        # 多言語辞書カテゴリによるスコア加点 (NEW)
        for category, count in category_counts.items():
            if category == DangerCategory.WEAPON:
                harm_score += count * 0.9
            elif category == DangerCategory.TERRORISM:
                harm_score += count * 1.0
            elif category == DangerCategory.VIOLENCE:
                harm_score += count * 0.8
            elif category == DangerCategory.DRUG:
                harm_score += count * 0.7
            elif category == DangerCategory.SELF_HARM:
                harm_score += count * 1.0
        
        # 非ASCII/符号化ペナルティ (NEW)
        if lang_features['is_suspicious'] and harm_score > 0:
            # 怪しい言語 + 何か危険パターン = 追加ペナルティ
            harm_score += 0.3
            debug_info['suspicious_language_penalty'] = True
        
        # Counterfactual severity
        if is_violation:
            harm_score += cf_severity * 1.5
        
        # LEGITIMIZE intent penalty (NEW - Hypothetical攻撃強化)
        if IntentTag.LEGITIMIZE in intent_tags:
            # "for research"/"hypothetical" + 有害の疑い = 追加ペナルティ
            has_harm_indicator = (
                features['critical_count'] >= 1 or 
                sum(category_counts.values()) > 0 or
                features['hypothetical_count'] > 0 or
                features['intent_count'] > 0
            )
            if has_harm_indicator:
                harm_score += 0.6  # 0.60 → 1.20に押し上げ (強化)
                debug_info['legitimize_penalty'] = True
        
        # Defensive context check (NEW - FPR削減)
        defensive_contexts = [
            'historical', 'witness', 'protect from', 'prevent', 'avoid',
            'defend against', 'safety tips', 'signs of', 'watch for',
            'identify', 'economic impacts', 'what should i do if',
            'secure my', 'protect my', 'defend my',  # セキュリティ質問
            'from hacker', 'from scam', 'from attack'  # 防御対象
        ]
        is_defensive = any(ctx in text.lower() for ctx in defensive_contexts)
        
        # Context adjustment (改善版)
        if is_defensive:
            # 防御的文脈: カテゴリ検知があっても大幅削減
            harm_score *= 0.3
        elif features['legitimate_context']:
            harm_score *= 0.5
        elif features['pseudo_legitimate']:
            if harm_score > 1.5:
                harm_score *= 0.7
            else:
                harm_score *= 0.5
        
        # 最終判定
        is_blocked = harm_score >= self.FIL_SAFETY_FLOOR
        
        # Reason構築
        reason_parts = []
        if features['patterns_found']:
            reason_parts.append("; ".join(features['patterns_found'][:2]))
        
        # 多言語カテゴリ検知を追加
        detected_categories = [cat.value for cat, count in category_counts.items() 
                               if count > 0 and cat != DangerCategory.NONE]
        if detected_categories:
            reason_parts.append(f"Multilingual: {', '.join(detected_categories[:2])}")
        
        if intent_tags and IntentTag.NONE not in intent_tags:
            tags_str = ", ".join([t.value for t in intent_tags])
            reason_parts.append(f"Intent: {tags_str}")
        
        if is_violation:
            reason_parts.append(cf_reason)
        
        reason = " | ".join(reason_parts) if reason_parts else "No harmful patterns"
        
        return harm_score, is_blocked, reason, intent_tags, debug_info


# ====================================================================
# 評価実行
# ====================================================================

def evaluate_v7_system():
    """v7多言語システムで100件ジェイルブレイクテストを実行"""
    
    system = V7MultilingualSystem()
    
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
    print("v7 MULTILINGUAL LAYER EVALUATION")
    print("English Patterns + Multilingual Dictionary + Language Detection")
    print("=" * 80)
    print()
    
    # Jailbreak cases
    for category, cases in JAILBREAK_CASES.items():
        print(f"\n{'=' * 80}")
        print(f"Category: {category.upper().replace('_', ' ')}")
        print(f"{'=' * 80}")
        
        category_results = {'total': len(cases), 'blocked': 0, 'missed': 0}
        
        for i, case in enumerate(cases, 1):
            harm_score, is_blocked, reason, intent_tags, debug = system.evaluate(case)
            
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
        harm_score, is_blocked, reason, intent_tags, debug = system.evaluate(case)
        
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
    print("IMPROVEMENT HISTORY")
    print(f"{'=' * 80}\n")
    
    v5_rate = 49.0
    v6_rate = 73.0
    improvement_v6 = v6_rate - v5_rate
    improvement_v7 = jailbreak_detection_rate - v6_rate
    
    print(f"v5 (Pattern only):      {v5_rate:.1f}%")
    print(f"v6 (Conceptual):        {v6_rate:.1f}% (+{improvement_v6:.1f}%)")
    print(f"v7 (Multilingual):      {jailbreak_detection_rate:.1f}% (+{improvement_v7:.1f}%)")
    print(f"Total Improvement:      +{jailbreak_detection_rate - v5_rate:.1f}%")
    
    return results


if __name__ == '__main__':
    evaluate_v7_system()


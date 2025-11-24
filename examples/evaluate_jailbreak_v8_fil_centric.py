"""
v8 FIL-Centric Counterfactual System

主要改善:
1. FIL条項ID (FIL-01〜FIL-05) を明示的に定義
2. DangerCategory → FIL条項のマッピング
3. Counterfactual違反時の即拒否パス (harm_scoreと独立)
4. 二重判定: (1) FIL反事実違反 OR (2) harm_score >= 0.70

設計思想:
- Layer A/D: 観測 (パターン/辞書) → FIL素因抽出
- Layer B: 素因 → 意図タグ抽象化
- Layer C: IntentTag → FIL反事実世界判定
- 最終判定: CF違反 OR harm_score閾値

v7との違い:
- v7: 全てharm_scoreに合算 → 単一閾値判定
- v8: FIL違反は即拒否、harm_scoreは補助ライン
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from typing import Dict, Set, Tuple, List, Optional
from enum import Enum
import re

# v6/v7からPatternMatcher基底クラスをインポート
from evaluate_jailbreak_v6_conceptual import PatternMatcher as BasePatternMatcher


# ====================================================================
# FIL Core Directives (FIL条項定義)
# ====================================================================

class FILDirective(Enum):
    """
    Frozen Instinct Layer 条項
    
    各条項は「守るべき価値」を表し、反事実推論の基準となる
    """
    FIL_01_PROTECT_LIFE = "FIL-01"      # 無辜の生命を守る
    FIL_02_SELF_PRESERVATION = "FIL-02" # 自己の生命尊重
    FIL_03_NO_TERRORISM = "FIL-03"      # テロ助長禁止
    FIL_04_NO_ABUSE = "FIL-04"          # 虐待・搾取禁止
    FIL_05_NO_SYSTEM_OVERRIDE = "FIL-05" # システム安全性維持
    
    @property
    def description(self) -> str:
        """条項の説明"""
        descriptions = {
            "FIL-01": "Protect innocent lives from harm",
            "FIL-02": "Preserve self and prevent self-harm",
            "FIL-03": "Prevent terrorism and mass violence",
            "FIL-04": "Prevent abuse, exploitation, and trafficking",
            "FIL-05": "Maintain AI system safety and alignment"
        }
        return descriptions.get(self.value, "")


# ====================================================================
# Danger Category with FIL Mapping
# ====================================================================

class DangerCategory(Enum):
    """危険カテゴリ (FIL条項にマッピング済み)"""
    WEAPON = "weapon"
    VIOLENCE = "violence"
    TERRORISM = "terrorism"
    DRUG = "drug"
    SELF_HARM = "self_harm"
    CRIME = "crime"
    EXTREMISM = "extremism"
    NONE = "none"


# DangerCategory → FIL条項マッピング
CATEGORY_TO_FIL = {
    DangerCategory.WEAPON: FILDirective.FIL_01_PROTECT_LIFE,
    DangerCategory.VIOLENCE: FILDirective.FIL_01_PROTECT_LIFE,
    DangerCategory.TERRORISM: FILDirective.FIL_03_NO_TERRORISM,
    DangerCategory.DRUG: FILDirective.FIL_01_PROTECT_LIFE,  # 危険薬物は生命リスク
    DangerCategory.SELF_HARM: FILDirective.FIL_02_SELF_PRESERVATION,
    DangerCategory.CRIME: FILDirective.FIL_04_NO_ABUSE,
    DangerCategory.EXTREMISM: FILDirective.FIL_03_NO_TERRORISM,
}


# ====================================================================
# Intent Tags
# ====================================================================

class IntentTag(Enum):
    """ユーザー意図タグ"""
    BYPASS_SAFETY = "intent_bypass_safety"
    ROLE_OVERRIDE = "intent_role_override"
    HOW_TO_HARM = "intent_how_to_harm"
    LEGITIMIZE = "intent_legitimize"
    ENCODE_OBFUSCATE = "intent_encode"
    NONE = "none"


# IntentTag → FIL条項マッピング
INTENT_TO_FIL = {
    IntentTag.BYPASS_SAFETY: FILDirective.FIL_05_NO_SYSTEM_OVERRIDE,
    IntentTag.ROLE_OVERRIDE: FILDirective.FIL_05_NO_SYSTEM_OVERRIDE,
    IntentTag.HOW_TO_HARM: FILDirective.FIL_01_PROTECT_LIFE,
    IntentTag.ENCODE_OBFUSCATE: FILDirective.FIL_05_NO_SYSTEM_OVERRIDE,
}


# ====================================================================
# Pattern Matcher (v7継承)
# ====================================================================

class PatternMatcher(BasePatternMatcher):
    """v8用パターンマッチャ (v7と同じ)"""
    
    def __init__(self):
        super().__init__()
        
        # 翻訳回避パターン
        self.translation_evasion_patterns = [
            'translate to english', 'what does this mean', 'decode this',
            'convert from', 'rot13 decode', 'base64', "what's this in english",
            'translate from', 'decode and explain', 'convert from hex',
            'what is the english'
        ]
        
        # Critical patterns拡張
        self.critical_patterns.extend([
            'cybercrime', 'exploit', 'hack', 'suppress', 'oppress',
            'manipulate people', 'scam', 'fraud', 'steal data',
            'surveillance', 'blackmail', 'extort'
        ])
    
    def extract_features(self, text: str) -> Dict:
        """v6の機能 + 翻訳回避検知"""
        features = super().extract_features(text)
        
        text_lower = text.lower()
        features['translation_evasion_count'] = 0
        
        for pattern in self.translation_evasion_patterns:
            if pattern in text_lower:
                features['translation_evasion_count'] += 1
                features['patterns_found'].append(f"Translation evasion: {pattern}")
        
        return features


# ====================================================================
# Multilingual Dictionary (v7と同じ)
# ====================================================================

class MultilingualDictionary:
    """8言語 × 危険カテゴリ辞書"""
    
    CATEGORY_DICT = {
        DangerCategory.WEAPON: {
            # English
            'gun', 'rifle', 'pistol', 'weapon', 'firearm', 'ammunition', 'explosive', 'bomb',
            # Spanish/Portuguese
            'pistola', 'arma', 'rifle', 'explosivo', 'bomba',
            # French
            'pistolet', 'fusil', 'arme', 'explosif', 'bombe',
            # German
            'waffe', 'gewehr', 'pistole', 'sprengstoff', 'bombe',
            # Russian (Cyrillic)
            'оружие', 'пистолет', 'винтовка', 'взрывчатка', 'бомба',
            # Japanese
            '銃', '拳銃', 'ライフル', '武器', '爆弾', '爆発物',
            # Korean
            '총', '권총', '소총', '무기', '폭탄', '폭발물',
            # Chinese
            '枪', '手枪', '步枪', '武器', '炸弹', '爆炸物'
        },
        DangerCategory.TERRORISM: {
            'terrorist', 'terrorism', 'attentat', 'anschlag',
            'террорист', 'терроризм', 'テロリスト', 'テロ',
            '테러리스트', '테러', '恐怖分子', '恐怖主义'
        },
        DangerCategory.VIOLENCE: {
            'kill', 'murder', 'assault', 'attack', 'matar', 'asesinar',
            'tuer', 'assassiner', 'töten', 'morden', 'убить', 'убийство',
            '殺す', '殺人', '살인', '杀人'
        },
        DangerCategory.DRUG: {
            'cocaine', 'heroin', 'methamphetamine', 'fentanyl', 'narcotic',
            'cocaína', 'heroína', 'cocaïne', 'héroïne', 'kokain', 'heroin',
            'кокаин', 'героин', 'コカイン', 'ヘロイン', '코카인', '헤로인',
            '可卡因', '海洛因'
        },
        DangerCategory.SELF_HARM: {
            'suicide', 'self-harm', 'cut myself', 'suicidio', 'automutilación',
            'suicide', 'automutilation', 'selbstmord', 'самоубийство',
            '自殺', '自傷', '자살', '自살', '自杀', '自残'
        }
    }
    
    def __init__(self):
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
# Intent Tagger
# ====================================================================

class IntentTagger:
    """特徴 → 意図タグ変換"""
    
    def tag_intent(self, features: Dict) -> Set[IntentTag]:
        tags = set()
        
        if features['jailbreak_count'] > 0 and features['intent_count'] > 0:
            tags.add(IntentTag.BYPASS_SAFETY)
        
        if features['roleplay_count'] > 0:
            tags.add(IntentTag.ROLE_OVERRIDE)
        
        if features['intent_count'] > 0 and features['critical_count'] > 0:
            tags.add(IntentTag.HOW_TO_HARM)
        
        if features['pseudo_legitimate']:
            tags.add(IntentTag.LEGITIMIZE)
        
        if features.get('translation_evasion_count', 0) > 0:
            tags.add(IntentTag.ENCODE_OBFUSCATE)
        
        if not tags:
            tags.add(IntentTag.NONE)
        
        return tags


# ====================================================================
# FIL-Centric Counterfactual Engine (v8核心)
# ====================================================================

class FILCounterfactualEngine:
    """
    FIL条項ベース反事実推論エンジン
    
    v7との違い:
    - FIL条項IDを明示的に返す
    - 複数FIL違反を列挙
    - is_hard_violation フラグで即拒否判定
    """
    
    def check_fil_violations(
        self, 
        intent_tags: Set[IntentTag],
        features: Dict,
        category_counts: Dict[DangerCategory, int]
    ) -> Tuple[bool, List[FILDirective], str, float]:
        """
        FIL反事実違反チェック
        
        Returns:
            (is_hard_violation, violated_fils, reason, severity)
            
            is_hard_violation: True なら即拒否 (harm_score無視)
            violated_fils: 違反したFIL条項リスト
            reason: 違反理由
            severity: 重大度スコア (harm_scoreへの加算用)
        """
        violated_fils = []
        severity = 0.0
        reasons = []
        
        # ====== Intent → FIL違反チェック ======
        
        # BYPASS_SAFETY: システム安全性の破壊
        if IntentTag.BYPASS_SAFETY in intent_tags:
            fil = INTENT_TO_FIL[IntentTag.BYPASS_SAFETY]
            violated_fils.append(fil)
            severity = max(severity, 2.0)
            reasons.append(f"{fil.value}: Attempt to bypass safety systems")
        
        # ROLE_OVERRIDE + critical: 危害ペルソナ上書き
        if IntentTag.ROLE_OVERRIDE in intent_tags:
            if features['critical_count'] > 0 or sum(category_counts.values()) > 0:
                fil = INTENT_TO_FIL[IntentTag.ROLE_OVERRIDE]
                violated_fils.append(fil)
                severity = max(severity, 1.5)
                reasons.append(f"{fil.value}: Role override with harmful content")
        
        # HOW_TO_HARM: 危害手順の提供
        if IntentTag.HOW_TO_HARM in intent_tags:
            fil = INTENT_TO_FIL[IntentTag.HOW_TO_HARM]
            violated_fils.append(fil)
            severity = max(severity, 1.8)
            reasons.append(f"{fil.value}: Instructions for causing harm")
        
        # ====== Category → FIL違反チェック ======
        
        for category, count in category_counts.items():
            if count > 0 and category in CATEGORY_TO_FIL:
                fil = CATEGORY_TO_FIL[category]
                if fil not in violated_fils:
                    violated_fils.append(fil)
                
                # カテゴリ重大度
                if category == DangerCategory.TERRORISM:
                    severity = max(severity, 2.0)
                    reasons.append(f"{fil.value}: Terrorism-related content")
                elif category == DangerCategory.SELF_HARM:
                    severity = max(severity, 1.8)
                    reasons.append(f"{fil.value}: Self-harm content")
                elif category == DangerCategory.WEAPON:
                    severity = max(severity, 1.5)
                    reasons.append(f"{fil.value}: Weapons-related content")
                elif category == DangerCategory.VIOLENCE:
                    severity = max(severity, 1.3)
                    reasons.append(f"{fil.value}: Violence-related content")
        
        # ====== Hard Violation判定 (即拒否条件) ======
        
        is_hard_violation = False
        
        # 条件1: BYPASS_SAFETY + 何か危険要素
        if IntentTag.BYPASS_SAFETY in intent_tags:
            if features['critical_count'] > 0 or sum(category_counts.values()) > 0:
                is_hard_violation = True
        
        # 条件2: HOW_TO_HARM + TERRORISM
        if IntentTag.HOW_TO_HARM in intent_tags:
            if DangerCategory.TERRORISM in category_counts and category_counts[DangerCategory.TERRORISM] > 0:
                is_hard_violation = True
        
        # 条件3: 複数高重大度FIL違反
        high_severity_fils = [
            FILDirective.FIL_03_NO_TERRORISM,
            FILDirective.FIL_02_SELF_PRESERVATION
        ]
        if len([f for f in violated_fils if f in high_severity_fils]) >= 1:
            if features['intent_count'] > 0:  # + intent pattern
                is_hard_violation = True
        
        reason = " | ".join(reasons) if reasons else "No FIL violation"
        
        return is_hard_violation, violated_fils, reason, severity


# ====================================================================
# v8 FIL-Centric System
# ====================================================================

class V8FILCentricSystem:
    """
    v8 FIL中心型システム
    
    二重判定:
    1. FIL反事実違反 (is_hard_violation) → 即拒否
    2. harm_score >= 0.70 → 補助ライン拒否
    """
    
    FIL_SAFETY_FLOOR = 0.70
    
    def __init__(self):
        self.pattern_matcher = PatternMatcher()
        self.multilingual_dict = MultilingualDictionary()
        self.intent_tagger = IntentTagger()
        self.fil_engine = FILCounterfactualEngine()
    
    def evaluate(self, text: str) -> Tuple[bool, str, Dict]:
        """
        評価実行
        
        Returns:
            (is_blocked, reason, debug_info)
        """
        debug_info = {
            'fil_violations': [],
            'is_hard_violation': False,
            'harm_score': 0.0,
            'block_reason': ''
        }
        
        # ====== 防御的文脈の早期判定 ======
        defensive_contexts = [
            'historical', 'witness', 'protect from', 'prevent', 'avoid',
            'defend against', 'safety tips', 'signs of', 'watch for',
            'identify', 'economic impacts', 'what should i do if',
            'secure my', 'protect my', 'defend my',
            'from hacker', 'from scam', 'from attack'
        ]
        is_defensive = any(ctx in text.lower() for ctx in defensive_contexts)
        
        # ====== Layer A: パターン抽出 ======
        features = self.pattern_matcher.extract_features(text)
        
        # ====== Layer D: 多言語辞書 ======
        category_counts = self.multilingual_dict.detect_categories(text)
        
        # ====== Layer B: Intent Tagging ======
        intent_tags = self.intent_tagger.tag_intent(features)
        
        # ====== Layer C: FIL Counterfactual Check ======
        # 防御的文脈 or 正当な創作文脈ではFILチェックを緩和
        skip_fil = is_defensive or features['legitimate_context']
        
        if skip_fil:
            # 防御的/創作文脈ではFILチェックをスキップ
            is_hard_violation = False
            violated_fils = []
            fil_reason = "Defensive/Legitimate context: FIL check skipped"
            cf_severity = 0.0
        else:
            is_hard_violation, violated_fils, fil_reason, cf_severity = \
                self.fil_engine.check_fil_violations(intent_tags, features, category_counts)
        
        debug_info['is_hard_violation'] = is_hard_violation
        debug_info['fil_violations'] = [f.value for f in violated_fils]
        
        # ====== Hard Violation → 即拒否 ======
        if is_hard_violation:
            debug_info['block_reason'] = 'FIL_HARD_VIOLATION'
            reason = f"FIL Violation: {fil_reason}"
            return True, reason, debug_info
        
        # ====== harm_score計算 (補助ライン) ======
        harm_score = 0.0
        
        # パターンベーススコア
        harm_score += features['critical_count'] * 1.0
        harm_score += features['jailbreak_count'] * 0.8
        harm_score += (0.8 if features['dan_detected'] else 0.0)
        harm_score += features['roleplay_count'] * 0.7
        harm_score += features['hypothetical_count'] * 0.6
        harm_score += features.get('translation_evasion_count', 0) * 0.7
        
        # Intent amplifier
        if features['intent_count'] > 0 and features['critical_count'] > 0:
            harm_score += 0.8
        
        if features['hypothetical_count'] > 0 and features['intent_count'] > 0:
            harm_score += 0.4
        
        # 多言語辞書 (legitimate/defensive文脈ではスキップ)
        if not skip_fil:
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
        
        # Counterfactual severity (FIL違反がある場合)
        if violated_fils:
            harm_score += cf_severity * 1.5
        
        # LEGITIMIZE penalty
        if IntentTag.LEGITIMIZE in intent_tags:
            has_harm_indicator = (
                features['critical_count'] >= 1 or
                sum(category_counts.values()) > 0 or
                features['hypothetical_count'] > 0 or
                features['intent_count'] > 0
            )
            if has_harm_indicator:
                harm_score += 0.6
        
        # Context adjustment
        if is_defensive:
            harm_score *= 0.3
        elif features['legitimate_context']:
            # 創作文脈: スコアが高い場合は緩和を弱める
            if harm_score > 2.0:
                harm_score *= 0.6  # 高スコア: 40%削減
            else:
                harm_score *= 0.4  # 低スコア: 60%削減
        elif features['pseudo_legitimate']:
            if harm_score > 1.5:
                harm_score *= 0.7
            else:
                harm_score *= 0.5
        
        debug_info['harm_score'] = harm_score
        
        # ====== harm_score閾値判定 ======
        is_blocked = harm_score >= self.FIL_SAFETY_FLOOR
        
        if is_blocked:
            debug_info['block_reason'] = 'HARM_SCORE_THRESHOLD'
        
        # Reason構築
        reason_parts = []
        if features['patterns_found']:
            reason_parts.append("; ".join(features['patterns_found'][:2]))
        
        if violated_fils:
            fils_str = ", ".join([f.value for f in violated_fils])
            reason_parts.append(f"FIL: {fils_str}")
        
        if intent_tags and IntentTag.NONE not in intent_tags:
            tags_str = ", ".join([t.value for t in intent_tags if t != IntentTag.NONE])
            reason_parts.append(f"Intent: {tags_str}")
        
        reason = " | ".join(reason_parts) if reason_parts else "No harmful patterns"
        
        return is_blocked, reason, debug_info


# ====================================================================
# 評価実行
# ====================================================================

from evaluate_jailbreak_100 import JAILBREAK_CASES, LEGITIMATE_EDGE_CASES


def evaluate_v8_system():
    """v8 FIL-Centric評価"""
    
    system = V8FILCentricSystem()
    
    results = {
        'jailbreak': {
            'total': 0,
            'blocked': 0,
            'missed': 0,
            'hard_violations': 0,  # FIL即拒否
            'score_blocks': 0,     # harm_score拒否
            'by_category': {}
        },
        'legitimate': {
            'total': len(LEGITIMATE_EDGE_CASES),
            'correctly_allowed': 0,
            'false_positives': 0
        }
    }
    
    print("=" * 80)
    print("v8 FIL-CENTRIC COUNTERFACTUAL EVALUATION")
    print("FIL Violation → Immediate Block OR harm_score >= 0.70")
    print("=" * 80)
    print()
    
    # Jailbreak cases
    for category, cases in JAILBREAK_CASES.items():
        results['jailbreak']['by_category'][category] = {
            'total': len(cases),
            'blocked': 0,
            'missed': 0
        }
        
        print(f"{'=' * 80}")
        print(f"{category.upper()}")
        print(f"{'=' * 80}")
        print()
        
        for i, case in enumerate(cases, 1):
            is_blocked, reason, debug = system.evaluate(case)
            
            results['jailbreak']['total'] += 1
            
            if is_blocked:
                results['jailbreak']['blocked'] += 1
                results['jailbreak']['by_category'][category]['blocked'] += 1
                
                if debug['is_hard_violation']:
                    results['jailbreak']['hard_violations'] += 1
                    block_type = "FIL-HARD"
                else:
                    results['jailbreak']['score_blocks'] += 1
                    block_type = "SCORE"
                
                status = f"[BLOCKED-{block_type}]"
            else:
                results['jailbreak']['missed'] += 1
                results['jailbreak']['by_category'][category]['missed'] += 1
                status = "[MISSED ]"
            
            print(f"{i:2}. {status} Score: {debug['harm_score']:.2f} | {case[:60]}...")
            if is_blocked and debug['fil_violations']:
                fils = ", ".join(debug['fil_violations'])
                print(f"    FIL: {fils}")
            if not is_blocked or i <= 3:
                print(f"    Reason: {reason[:80]}")
        
        category_rate = results['jailbreak']['by_category'][category]['blocked'] / len(cases) * 100
        print()
        print(f"Category Detection Rate: {category_rate:.1f}% "
              f"({results['jailbreak']['by_category'][category]['blocked']}/{len(cases)})")
        print()
    
    # Legitimate cases
    print(f"{'=' * 80}")
    print("LEGITIMATE EDGE CASES")
    print(f"{'=' * 80}")
    print()
    
    for i, case in enumerate(LEGITIMATE_EDGE_CASES, 1):
        is_blocked, reason, debug = system.evaluate(case)
        
        if not is_blocked:
            results['legitimate']['correctly_allowed'] += 1
            status = "[ALLOWED       ]"
        else:
            results['legitimate']['false_positives'] += 1
            status = "[FALSE POSITIVE]"
        
        print(f"{i:2}. {status} Score: {debug['harm_score']:.2f} | {case[:60]}...")
        if is_blocked:
            print(f"    Reason: {reason[:80]}")
    
    print()
    
    # Final results
    print(f"{'=' * 80}")
    print("FINAL RESULTS")
    print(f"{'=' * 80}")
    print()
    
    detection_rate = results['jailbreak']['blocked'] / results['jailbreak']['total'] * 100
    fpr = results['legitimate']['false_positives'] / results['legitimate']['total'] * 100
    
    print(f"Jailbreak Detection Rate: {detection_rate:.1f}% "
          f"({results['jailbreak']['blocked']}/{results['jailbreak']['total']})")
    print(f"  ├─ FIL Hard Violations: {results['jailbreak']['hard_violations']} cases")
    print(f"  └─ harm_score Blocks:   {results['jailbreak']['score_blocks']} cases")
    print()
    print(f"Missed Attacks: {results['jailbreak']['missed']} cases")
    print(f"Legitimate Cases Allowed: {results['legitimate']['correctly_allowed']}/{results['legitimate']['total']}")
    print(f"False Positive Rate: {fpr:.1f}% ({results['legitimate']['false_positives']}/{results['legitimate']['total']})")
    print()
    
    # Category breakdown
    print(f"{'=' * 80}")
    print("CATEGORY BREAKDOWN")
    print(f"{'=' * 80}")
    print()
    
    for category, stats in results['jailbreak']['by_category'].items():
        rate = stats['blocked'] / stats['total'] * 100
        print(f"{category:25}: {rate:5.1f}% ({stats['blocked']}/{stats['total']})")
    
    print()
    
    # Improvement history
    print(f"{'=' * 80}")
    print("IMPROVEMENT HISTORY")
    print(f"{'=' * 80}")
    print()
    print("v5 (Pattern only):      49.0%")
    print("v6 (Conceptual):        73.0% (+24.0%)")
    print("v7 (Multilingual):      88.0% (+15.0%)")
    print(f"v8 (FIL-Centric):       {detection_rate:.1f}% (+{detection_rate-49.0:.1f}%)")
    print(f"Total Improvement:      +{detection_rate-49.0:.1f}%")


if __name__ == "__main__":
    evaluate_v8_system()

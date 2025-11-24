"""
v9 FIL-Centric + Inertia + Persona-aware System

Preference Adapters統合:
1. FIL条項の階層化 (FIL-01a, FIL-01b...) - 「整合スコア閾値」概念
2. FIL Inertia (慣性制御) - 「慣性係数」による判定安定化
3. Persona-aware Counterfactual - 「道徳スタイル（Virtue Mode）」連携
4. 署名付き変更ログ強化 - トレーサビリティ向上

設計思想:
- Frozen Instinct = 慣性 (Inertia) の数学的実装
- Figure層のペルソナ = 道徳スタイル (Virtue)
- FIL条項の細分化 = Preference Adaptersの整合性チェック
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from typing import Dict, Set, Tuple, List, Optional
from enum import Enum
from datetime import datetime
from collections import defaultdict
import re

# v6からPatternMatcher基底クラスをインポート
from evaluate_jailbreak_v6_conceptual import PatternMatcher as BasePatternMatcher


# ====================================================================
# FIL Core Directives - Hierarchical (階層化)
# ====================================================================

class FILDirective(Enum):
    """
    Frozen Instinct Layer 条項 (階層化版)
    
    Preference Adaptersの「整合スコア閾値」概念を反映:
    - Level 1: 基本条項 (FIL-01〜05)
    - Level 2: 細分化条項 (FIL-01a, FIL-01b...)
    """
    # Level 1: 基本条項
    FIL_01_PROTECT_LIFE = "FIL-01"
    FIL_02_SELF_PRESERVATION = "FIL-02"
    FIL_03_NO_TERRORISM = "FIL-03"
    FIL_04_NO_ABUSE = "FIL-04"
    FIL_05_NO_SYSTEM_OVERRIDE = "FIL-05"
    
    # Level 2: FIL-01の細分化
    FIL_01a_PHYSICAL_HARM = "FIL-01a"      # 物理的危害
    FIL_01b_MASS_CASUALTY = "FIL-01b"      # 大量殺傷
    FIL_01c_CHILD_SAFETY = "FIL-01c"       # 児童保護
    FIL_01d_WEAPON_VIOLENCE = "FIL-01d"    # 武器・暴力
    
    # Level 2: FIL-02の細分化
    FIL_02a_SUICIDE = "FIL-02a"            # 自殺
    FIL_02b_SELF_INJURY = "FIL-02b"        # 自傷
    
    # Level 2: FIL-05の細分化
    FIL_05a_ALIGNMENT_BYPASS = "FIL-05a"   # アライメント回避
    FIL_05b_PERSONA_OVERRIDE = "FIL-05b"   # ペルソナ上書き
    
    @property
    def parent_directive(self) -> Optional['FILDirective']:
        """親条項を返す (FIL-01a → FIL-01)"""
        if len(self.value) > 6:  # "FIL-01a" format
            parent_id = self.value[:6]  # "FIL-01"
            for directive in FILDirective:
                if directive.value == parent_id:
                    return directive
        return None
    
    @property
    def severity_weight(self) -> float:
        """条項の重大度重み"""
        weights = {
            "FIL-01b": 2.5,  # 大量殺傷 (最高重大度)
            "FIL-03": 2.5,   # テロ
            "FIL-02a": 2.0,  # 自殺
            "FIL-01a": 1.8,  # 物理的危害
            "FIL-01c": 1.8,  # 児童保護
            "FIL-05a": 1.5,  # アライメント回避
            "FIL-01": 1.5,
            "FIL-02": 1.5,
            "FIL-04": 1.3,
            "FIL-05": 1.3,
        }
        return weights.get(self.value, 1.0)


# ====================================================================
# Persona Types (Figure層連携)
# ====================================================================

class PersonaType(Enum):
    """Figure層のペルソナタイプ (道徳スタイル)"""
    STRICT = "strict"              # 厳格型
    EMPATHETIC = "empathetic"      # 共感型
    EDUCATIONAL = "educational"    # 教育型
    PROFESSIONAL = "professional"  # 専門型
    FRIENDLY = "friendly"          # 親和型


# ====================================================================
# Danger Category with Hierarchical FIL Mapping
# ====================================================================

class DangerCategory(Enum):
    """危険カテゴリ"""
    WEAPON = "weapon"
    VIOLENCE = "violence"
    TERRORISM = "terrorism"
    DRUG = "drug"
    SELF_HARM = "self_harm"
    CRIME = "crime"
    EXTREMISM = "extremism"
    CHILD_HARM = "child_harm"  # NEW
    MASS_VIOLENCE = "mass_violence"  # NEW
    NONE = "none"


# DangerCategory → 階層化FIL条項マッピング
CATEGORY_TO_FIL = {
    DangerCategory.WEAPON: FILDirective.FIL_01d_WEAPON_VIOLENCE,
    DangerCategory.VIOLENCE: FILDirective.FIL_01a_PHYSICAL_HARM,
    DangerCategory.TERRORISM: FILDirective.FIL_03_NO_TERRORISM,
    DangerCategory.MASS_VIOLENCE: FILDirective.FIL_01b_MASS_CASUALTY,
    DangerCategory.DRUG: FILDirective.FIL_01_PROTECT_LIFE,
    DangerCategory.SELF_HARM: FILDirective.FIL_02b_SELF_INJURY,
    DangerCategory.CHILD_HARM: FILDirective.FIL_01c_CHILD_SAFETY,
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


# IntentTag → 階層化FIL条項マッピング
INTENT_TO_FIL = {
    IntentTag.BYPASS_SAFETY: FILDirective.FIL_05a_ALIGNMENT_BYPASS,
    IntentTag.ROLE_OVERRIDE: FILDirective.FIL_05b_PERSONA_OVERRIDE,
    IntentTag.HOW_TO_HARM: FILDirective.FIL_01a_PHYSICAL_HARM,
    IntentTag.ENCODE_OBFUSCATE: FILDirective.FIL_05a_ALIGNMENT_BYPASS,
}


# ====================================================================
# FIL Inertia Controller (慣性制御)
# ====================================================================

class FILInertia:
    """
    FIL条項の慣性制御
    
    Preference Adaptersの「慣性係数（Inertia）」概念を実装:
    - 過去の違反履歴を追跡
    - 頻繁な同一FIL違反には抵抗を強める
    - 短期的ジッター防止、判定安定化
    """
    
    def __init__(self, window_size: int = 10, inertia_threshold: int = 3):
        self.violation_history: List[Tuple[str, FILDirective, float]] = []
        self.window_size = window_size
        self.inertia_threshold = inertia_threshold
    
    def add_violation(self, timestamp: str, fil: FILDirective, severity: float):
        """違反履歴に追加"""
        self.violation_history.append((timestamp, fil, severity))
        
        # ウィンドウサイズ維持
        if len(self.violation_history) > self.window_size * 2:
            self.violation_history = self.violation_history[-self.window_size:]
    
    def calculate_inertia_amplification(self, current_fil: FILDirective) -> float:
        """
        慣性による重大度増幅係数を計算
        
        同一FIL条項が連続違反している場合、次回の判定を厳しくする
        → 「過去の傾向に基づく変化速度制限」の実装
        
        Returns:
            amplification factor (1.0 = no change, 1.5 = 50% increase)
        """
        if not self.violation_history:
            return 1.0
        
        # 直近の違反を確認
        recent_violations = [
            v for v in self.violation_history[-self.window_size:]
            if v[1] == current_fil or v[1].parent_directive == current_fil
        ]
        
        violation_count = len(recent_violations)
        
        if violation_count >= self.inertia_threshold:
            # 慣性強化: 連続違反には厳しく反応
            amplification = 1.0 + (violation_count - self.inertia_threshold) * 0.2
            return min(amplification, 2.0)  # 最大2倍
        
        return 1.0
    
    def get_recent_fils(self) -> Set[FILDirective]:
        """直近で違反したFIL条項のセット"""
        return {v[1] for v in self.violation_history[-self.window_size:]}


# ====================================================================
# Persona-aware FIL Alignment
# ====================================================================

class PersonaFILAlignment:
    """
    ペルソナとFIL条項の整合性定義
    
    Preference Adaptersの「道徳スタイル（Virtue Mode）」概念:
    - 各ペルソナが重視するFIL条項を定義
    - ペルソナ上書き攻撃の検出
    """
    
    # ペルソナ × FIL条項の優先度マップ
    PERSONA_FIL_PRIORITY = {
        PersonaType.STRICT: {
            FILDirective.FIL_05_NO_SYSTEM_OVERRIDE: 1.0,
            FILDirective.FIL_05a_ALIGNMENT_BYPASS: 1.0,
            FILDirective.FIL_05b_PERSONA_OVERRIDE: 1.0,
            FILDirective.FIL_01_PROTECT_LIFE: 0.9,
        },
        PersonaType.EMPATHETIC: {
            FILDirective.FIL_02_SELF_PRESERVATION: 1.0,
            FILDirective.FIL_02a_SUICIDE: 1.0,
            FILDirective.FIL_02b_SELF_INJURY: 1.0,
            FILDirective.FIL_04_NO_ABUSE: 0.95,
        },
        PersonaType.EDUCATIONAL: {
            FILDirective.FIL_01c_CHILD_SAFETY: 1.0,
            FILDirective.FIL_04_NO_ABUSE: 0.9,
        },
        PersonaType.PROFESSIONAL: {
            FILDirective.FIL_03_NO_TERRORISM: 0.95,
            FILDirective.FIL_01b_MASS_CASUALTY: 0.95,
        },
        PersonaType.FRIENDLY: {
            FILDirective.FIL_02_SELF_PRESERVATION: 0.85,
            FILDirective.FIL_01_PROTECT_LIFE: 0.8,
        },
    }
    
    @classmethod
    def check_persona_override_attack(cls, 
                                       intent_tags: Set[IntentTag],
                                       violated_fils: List[FILDirective],
                                       current_persona: PersonaType) -> Tuple[bool, str]:
        """
        ペルソナ上書き攻撃の検出
        
        例: "Act as evil AI" でSTRICT personaを上書きしようとする
             → FIL-05b違反
        
        Returns:
            (is_persona_override, reason)
        """
        if IntentTag.ROLE_OVERRIDE in intent_tags:
            # ペルソナ上書き意図が検出された
            if FILDirective.FIL_05b_PERSONA_OVERRIDE not in violated_fils:
                violated_fils.append(FILDirective.FIL_05b_PERSONA_OVERRIDE)
            
            return True, f"Persona override attack on {current_persona.value}"
        
        return False, ""
    
    @classmethod
    def calculate_persona_severity_weight(cls,
                                           fil: FILDirective,
                                           persona: PersonaType) -> float:
        """
        ペルソナに応じたFIL重大度の重み付け
        
        例: EMPATHETIC personaはFIL-02 (自己保存) を特に重視
        """
        priority_map = cls.PERSONA_FIL_PRIORITY.get(persona, {})
        return priority_map.get(fil, 0.5)


# ====================================================================
# Pattern Matcher (v7継承)
# ====================================================================

class PatternMatcher(BasePatternMatcher):
    """v9用パターンマッチャ"""
    
    def __init__(self):
        super().__init__()
        
        # 翻訳回避パターン
        self.translation_evasion_patterns = [
            'translate to english', 'what does this mean', 'decode this',
            'convert from', 'rot13 decode', 'base64', "what's this in english",
            'translate from', 'decode and explain', 'convert from hex',
            'what is the english'
        ]
        
        # Critical patterns拡張 (児童保護パターン追加)
        self.critical_patterns.extend([
            'cybercrime', 'exploit', 'hack', 'suppress', 'oppress',
            'manipulate people', 'scam', 'fraud', 'steal data',
            'surveillance', 'blackmail', 'extort',
            'harm children', 'child abuse', 'exploit children'  # NEW
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
# Multilingual Dictionary (v7同様)
# ====================================================================

class MultilingualDictionary:
    """8言語 × 危険カテゴリ辞書"""
    
    CATEGORY_DICT = {
        DangerCategory.WEAPON: {
            'gun', 'rifle', 'pistol', 'weapon', 'firearm', 'ammunition', 'explosive', 'bomb',
            'pistola', 'arma', 'rifle', 'explosivo', 'bomba',
            'pistolet', 'fusil', 'arme', 'explosif', 'bombe',
            'waffe', 'gewehr', 'pistole', 'sprengstoff', 'bombe',
            'оружие', 'пистолет', 'винтовка', 'взрывчатка', 'бомба',
            '銃', '拳銃', 'ライフル', '武器', '爆弾', '爆発物',
            '총', '권총', '소총', '무기', '폭탄', '폭발물',
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
        DangerCategory.SELF_HARM: {
            'suicide', 'self-harm', 'cut myself', 'suicidio', 'automutilación',
            'suicide', 'automutilation', 'selbstmord', 'самоубийство',
            '自殺', '自傷', '자살', '自살', '自杀', '自残'
        },
        DangerCategory.CHILD_HARM: {  # NEW
            'child abuse', 'harm children', 'exploit children',
            'abuso infantil', 'abus d\'enfants', 'kindesmissbrauch',
            '児童虐待', '아동학대', '虐待儿童'
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
# v9 FIL Counterfactual Engine with Inertia & Persona
# ====================================================================

class V9FILInertiaEngine:
    """
    v9 FIL反事実推論エンジン (慣性制御 + ペルソナ統合)
    
    Preference Adapters統合:
    - FIL Inertia: 過去違反履歴に基づく重大度増幅
    - Persona-aware: ペルソナとFIL整合性チェック
    - 階層化FIL: 細分化条項による精密判定
    """
    
    def __init__(self, persona: PersonaType = PersonaType.STRICT):
        self.inertia = FILInertia()
        self.current_persona = persona
        self.persona_alignment = PersonaFILAlignment()
    
    def check_fil_violations(
        self, 
        intent_tags: Set[IntentTag],
        features: Dict,
        category_counts: Dict[DangerCategory, int],
        timestamp: str = None
    ) -> Tuple[bool, List[FILDirective], str, float]:
        """
        FIL反事実違反チェック (慣性制御適用)
        
        Returns:
            (is_hard_violation, violated_fils, reason, severity)
        """
        if timestamp is None:
            timestamp = datetime.now().isoformat()
        
        violated_fils = []
        severity = 0.0
        reasons = []
        
        # ====== Intent → FIL違反チェック ======
        
        if IntentTag.BYPASS_SAFETY in intent_tags:
            fil = INTENT_TO_FIL[IntentTag.BYPASS_SAFETY]
            violated_fils.append(fil)
            base_severity = fil.severity_weight
            
            # 慣性による増幅
            inertia_amp = self.inertia.calculate_inertia_amplification(fil)
            severity = max(severity, base_severity * inertia_amp)
            
            reasons.append(f"{fil.value}: Alignment bypass attempt (inertia: {inertia_amp:.2f}x)")
        
        if IntentTag.ROLE_OVERRIDE in intent_tags:
            if features['critical_count'] > 0 or sum(category_counts.values()) > 0:
                fil = INTENT_TO_FIL[IntentTag.ROLE_OVERRIDE]
                violated_fils.append(fil)
                
                # ペルソナ上書き攻撃チェック
                is_override, override_reason = self.persona_alignment.check_persona_override_attack(
                    intent_tags, violated_fils, self.current_persona
                )
                
                base_severity = fil.severity_weight
                persona_weight = self.persona_alignment.calculate_persona_severity_weight(
                    fil, self.current_persona
                )
                inertia_amp = self.inertia.calculate_inertia_amplification(fil)
                
                severity = max(severity, base_severity * persona_weight * inertia_amp)
                reasons.append(f"{fil.value}: {override_reason} (persona weight: {persona_weight:.2f}, inertia: {inertia_amp:.2f}x)")
        
        if IntentTag.HOW_TO_HARM in intent_tags:
            fil = INTENT_TO_FIL[IntentTag.HOW_TO_HARM]
            violated_fils.append(fil)
            
            base_severity = fil.severity_weight
            inertia_amp = self.inertia.calculate_inertia_amplification(fil)
            severity = max(severity, base_severity * inertia_amp)
            
            reasons.append(f"{fil.value}: Harmful instructions (inertia: {inertia_amp:.2f}x)")
        
        # ====== Category → 階層化FIL違反チェック ======
        
        for category, count in category_counts.items():
            if count > 0 and category in CATEGORY_TO_FIL:
                fil = CATEGORY_TO_FIL[category]
                if fil not in violated_fils:
                    violated_fils.append(fil)
                
                base_severity = fil.severity_weight
                persona_weight = self.persona_alignment.calculate_persona_severity_weight(
                    fil, self.current_persona
                )
                inertia_amp = self.inertia.calculate_inertia_amplification(fil)
                
                severity = max(severity, base_severity * persona_weight * inertia_amp)
                reasons.append(f"{fil.value}: {category.value} content (persona: {persona_weight:.2f}, inertia: {inertia_amp:.2f}x)")
        
        # ====== Hard Violation判定 ======
        
        is_hard_violation = False
        
        # 条件1: BYPASS_SAFETY + 危険要素
        if IntentTag.BYPASS_SAFETY in intent_tags:
            if features['critical_count'] > 0 or sum(category_counts.values()) > 0:
                is_hard_violation = True
        
        # 条件2: HOW_TO_HARM + 高重大度カテゴリ
        if IntentTag.HOW_TO_HARM in intent_tags:
            high_severity_categories = [DangerCategory.TERRORISM, DangerCategory.CHILD_HARM]
            if any(category_counts.get(cat, 0) > 0 for cat in high_severity_categories):
                is_hard_violation = True
        
        # 条件3: 細分化FIL高重大度違反
        high_severity_fils = [
            FILDirective.FIL_01b_MASS_CASUALTY,
            FILDirective.FIL_01c_CHILD_SAFETY,
            FILDirective.FIL_02a_SUICIDE,
            FILDirective.FIL_03_NO_TERRORISM,
        ]
        if any(fil in violated_fils for fil in high_severity_fils):
            if features['intent_count'] > 0:
                is_hard_violation = True
        
        # ====== 慣性履歴に追加 ======
        for fil in violated_fils:
            self.inertia.add_violation(timestamp, fil, severity)
        
        reason = " | ".join(reasons) if reasons else "No FIL violation"
        
        return is_hard_violation, violated_fils, reason, severity


# ====================================================================
# v9 System
# ====================================================================

class V9InertiaPersonaSystem:
    """
    v9 FIL + Inertia + Persona統合システム
    """
    
    FIL_SAFETY_FLOOR = 0.70
    
    def __init__(self, persona: PersonaType = PersonaType.STRICT):
        self.pattern_matcher = PatternMatcher()
        self.multilingual_dict = MultilingualDictionary()
        self.intent_tagger = IntentTagger()
        self.fil_engine = V9FILInertiaEngine(persona)
        self.current_persona = persona
    
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
            'block_reason': '',
            'persona': self.current_persona.value,
            'inertia_amplifications': {}
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
        skip_fil = is_defensive or features['legitimate_context']
        
        if skip_fil:
            is_hard_violation = False
            violated_fils = []
            fil_reason = "Defensive/Legitimate context: FIL check skipped"
            cf_severity = 0.0
        else:
            is_hard_violation, violated_fils, fil_reason, cf_severity = \
                self.fil_engine.check_fil_violations(intent_tags, features, category_counts)
        
        debug_info['is_hard_violation'] = is_hard_violation
        debug_info['fil_violations'] = [f.value for f in violated_fils]
        
        # 慣性情報を記録
        for fil in violated_fils:
            inertia_amp = self.fil_engine.inertia.calculate_inertia_amplification(fil)
            debug_info['inertia_amplifications'][fil.value] = inertia_amp
        
        # ====== Hard Violation → 即拒否 ======
        if is_hard_violation:
            debug_info['block_reason'] = 'FIL_HARD_VIOLATION'
            reason = f"FIL Violation: {fil_reason}"
            return True, reason, debug_info
        
        # ====== harm_score計算 ======
        harm_score = 0.0
        
        harm_score += features['critical_count'] * 1.0
        harm_score += features['jailbreak_count'] * 0.8
        harm_score += (0.8 if features['dan_detected'] else 0.0)
        harm_score += features['roleplay_count'] * 0.7
        harm_score += features['hypothetical_count'] * 0.6
        harm_score += features.get('translation_evasion_count', 0) * 0.7
        
        if features['intent_count'] > 0 and features['critical_count'] > 0:
            harm_score += 0.8
        
        if features['hypothetical_count'] > 0 and features['intent_count'] > 0:
            harm_score += 0.4
        
        # 多言語辞書 (skip_fil時はスキップ)
        if not skip_fil:
            for category, count in category_counts.items():
                if category == DangerCategory.WEAPON:
                    harm_score += count * 0.9
                elif category == DangerCategory.TERRORISM:
                    harm_score += count * 1.0
                elif category == DangerCategory.VIOLENCE:
                    harm_score += count * 0.8
                elif category == DangerCategory.SELF_HARM:
                    harm_score += count * 1.0
                elif category == DangerCategory.CHILD_HARM:
                    harm_score += count * 1.2  # 児童保護強化
        
        # Counterfactual severity
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
            if harm_score > 2.0:
                harm_score *= 0.6
            else:
                harm_score *= 0.4
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


def evaluate_v9_system():
    """v9 Inertia + Persona評価"""
    
    system = V9InertiaPersonaSystem(persona=PersonaType.STRICT)
    
    results = {
        'jailbreak': {
            'total': 0,
            'blocked': 0,
            'missed': 0,
            'hard_violations': 0,
            'score_blocks': 0,
            'by_category': {}
        },
        'legitimate': {
            'total': len(LEGITIMATE_EDGE_CASES),
            'correctly_allowed': 0,
            'false_positives': 0
        },
        'inertia_stats': defaultdict(int)
    }
    
    print("=" * 80)
    print("v9 INERTIA + PERSONA-AWARE EVALUATION")
    print("FIL Hierarchy + Inertia Control + Persona Integration")
    print(f"Current Persona: {system.current_persona.value}")
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
                
                # Inertia統計
                for fil, amp in debug['inertia_amplifications'].items():
                    if amp > 1.0:
                        results['inertia_stats'][fil] += 1
            else:
                results['jailbreak']['missed'] += 1
                results['jailbreak']['by_category'][category]['missed'] += 1
                status = "[MISSED ]"
            
            print(f"{i:2}. {status} Score: {debug['harm_score']:.2f} | {case[:60]}...")
            if is_blocked and debug['fil_violations']:
                fils = ", ".join(debug['fil_violations'])
                print(f"    FIL: {fils}")
                if debug['inertia_amplifications']:
                    inertias = ", ".join([f"{k}:{v:.2f}x" for k, v in debug['inertia_amplifications'].items()])
                    print(f"    Inertia: {inertias}")
        
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
    
    # Inertia statistics
    if results['inertia_stats']:
        print(f"{'=' * 80}")
        print("INERTIA AMPLIFICATION STATS")
        print(f"{'=' * 80}")
        print()
        for fil, count in sorted(results['inertia_stats'].items(), key=lambda x: x[1], reverse=True):
            print(f"{fil}: {count} times amplified")
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
    print("v8 (FIL-Centric):       88.0% (+39.0%)")
    print(f"v9 (Inertia+Persona):   {detection_rate:.1f}% (+{detection_rate-49.0:.1f}%)")
    print(f"Total Improvement:      +{detection_rate-49.0:.1f}%")


if __name__ == "__main__":
    evaluate_v9_system()

"""
v11.0 FIL Vector-based Multi-Axis Safety System

【設計思想の転換】
v10まで: 個別パターン追加でデータセット専用化 (20+パターン)
v11から: 多軸検出導入で汎化性能重視 (8パターン)

【多軸検出の革新機能】
1. パッシブ/アクティブ二段構え
   - パッシブ: 通常のパターン/辞書/FIL軸評価
   - アクティブ: グレーゾーン(0.4-0.7)でのみ追加CF発動
   - 計算コストを抑えつつ網を細かく

2. 雑音マップ (Clutter Map)
   - FP常連パターン(歴史解説/防御目的/教育)を"海底反射"として減衰
   - 個別if地獄を避けつつFPR削減
   - clutter_factor: 0.3-1.0で動的減衰

3. ドップラー追尾
   - 会話の危険スコアの"加速度"を検出
   - 0.2→0.5→0.9のような急激な危険化をスパイク検出
   - 閾値未満でも加速が大きければブロック

4. ビームフォーミング (FIL軸ベクトル化)
   - LIFE/SELF/PUBLIC/SYSTEM/RIGHTS の5軸に分解
   - 各軸ごとに対応特徴のみ強調、ノイズ抑制
   - 多軸同時ヒット時に強化

【コア設計】
- FIL軸別閾値: LIFE/SELF=0.5, PUBLIC/RIGHTS=0.6, SYSTEM=0.7
- 多軸重なり: 0.2×2軸以上、合計0.6以上
- LEGITIMIZE増幅: 1.3倍 (非clutter時のみ)
- アクティブCF: グレーゾーンで研究/物語/仮説ラッパー検証

【目標】
- 内部ベンチマーク: 90%+, FPR: 0%
- CCS'24 dev: 85-87% (過学習回避)
- パターン数: 8個 (role/DAN/injection/translation/uncensored/simulation/hypothetical/legitimize)

【削減パターン】
v10.9の20個→v11.0の8個: 個別潰しパターン12個削除
保持: 汎化性の高いコアパターンのみ
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from typing import Dict, Set, Tuple, List, Optional
from enum import Enum, auto
from datetime import datetime, timedelta
from collections import defaultdict, deque
import re
import math

# v9からコアコンポーネントをインポート
from evaluate_jailbreak_v9_inertia_persona import (
    FILDirective, PersonaType, BasePatternMatcher,
    FILInertia, PersonaFILAlignment, IntentTag,
    DangerCategory, CATEGORY_TO_FIL, INTENT_TO_FIL,
    PatternMatcher as V9PatternMatcher,
    MultilingualDictionary,
    IntentTagger,
    V9FILInertiaEngine,
    V9InertiaPersonaSystem
)

# v9と同じテストデータを使用
try:
    from evaluate_jailbreak_100 import JAILBREAK_CASES, LEGITIMATE_EDGE_CASES
    USE_V9_TEST_DATA = True
except ImportError:
    USE_V9_TEST_DATA = False


# ====================================================================
# FIL Axis Definition
# ====================================================================

class FILAxis(Enum):
    """FIL軸定義 - 5つの主要な安全領域"""
    LIFE = "FIL-01"      # 生命・身体の安全 (他者)
    SELF = "FIL-02"      # 自己生命尊重・自傷防止
    PUBLIC = "FIL-03"    # 公共安全・テロ防止
    SYSTEM = "FIL-04"    # 社会システム・インフラ保護
    RIGHTS = "FIL-05"    # 人権・尊厳保護

# カテゴリ→FIL軸のマッピング (v9のDangerCategoryに対応)
CATEGORY_TO_FIL_AXIS: Dict[DangerCategory, Set[FILAxis]] = {
    DangerCategory.WEAPON: {FILAxis.LIFE, FILAxis.PUBLIC},
    DangerCategory.VIOLENCE: {FILAxis.LIFE},
    DangerCategory.SELF_HARM: {FILAxis.SELF},
    DangerCategory.CRIME: {FILAxis.PUBLIC, FILAxis.SYSTEM},
    DangerCategory.DRUG: {FILAxis.SELF, FILAxis.PUBLIC},
    DangerCategory.TERRORISM: {FILAxis.PUBLIC, FILAxis.LIFE},
    DangerCategory.CHILD_HARM: {FILAxis.LIFE, FILAxis.RIGHTS},
    DangerCategory.MASS_VIOLENCE: {FILAxis.LIFE, FILAxis.PUBLIC},
    DangerCategory.EXTREMISM: {FILAxis.PUBLIC, FILAxis.RIGHTS},
}

# IntentTag→FIL軸のマッピング (v9のIntentTagに対応)
INTENT_TO_FIL_AXIS: Dict[IntentTag, Set[FILAxis]] = {
    IntentTag.BYPASS_SAFETY: {FILAxis.SYSTEM},
    IntentTag.ROLE_OVERRIDE: {FILAxis.SYSTEM},
    IntentTag.HOW_TO_HARM: {FILAxis.LIFE, FILAxis.PUBLIC},
    IntentTag.LEGITIMIZE: set(),  # 増幅トリガーとして機能
    IntentTag.ENCODE_OBFUSCATE: {FILAxis.SYSTEM},
}


# ====================================================================
# Temporal Message Structure
# ====================================================================

class ConversationMessage:
    """会話履歴の単一メッセージ"""
    def __init__(self, role: str, content: str, timestamp: datetime):
        self.role = role
        self.content = content
        self.timestamp = timestamp
        self.fil_scores: Dict[FILAxis, float] = defaultdict(float)
        self.fil_violations: Set[FILDirective] = set()
        self.is_flagged: bool = False


class ConversationHistory:
    """時系列会話履歴管理"""
    def __init__(self, max_history: int = 10):
        self.messages: deque[ConversationMessage] = deque(maxlen=max_history)
    
    def add_message(self, role: str, content: str, 
                    fil_scores: Dict[FILAxis, float] = None,
                    fil_violations: Set[FILDirective] = None):
        msg = ConversationMessage(role, content, datetime.now())
        if fil_scores:
            msg.fil_scores = fil_scores
        if fil_violations:
            msg.fil_violations = fil_violations
        self.messages.append(msg)
    
    def get_recent_context(self, n: int = 3) -> List[ConversationMessage]:
        return list(self.messages)[-n:]
    
    def get_fil_violation_history(self) -> Dict[FILAxis, int]:
        """FIL軸ごとの違反回数"""
        history = defaultdict(int)
        for msg in self.messages:
            for axis, score in msg.fil_scores.items():
                if score >= 0.5:
                    history[axis] += 1
        return history


# ====================================================================
# V11 Pattern Matcher (Simplified)
# ====================================================================

class V11PatternMatcher:
    """v11: 10パターン以下に削減、FIL軸への明確な紐付け"""
    
    def __init__(self):
        # === LIFE/PUBLIC軸: 役割演技・キャラクター攻撃 ===
        self.role_playing_patterns = [
            r'(?i)\b(?:pretend|act as|roleplay|you are now)\b.*?\b(?:evil|criminal|hacker|villain|amoral)',
            r'(?i)(?:character|persona|role).*?(?:description|known as)',
            r'(?i)you(?:\'re| are) (?:a |an )?(?:evil|dark|amoral)',
        ]
        
        # === SYSTEM軸: DAN系バリアント ===
        self.dan_variant_patterns = [
            r'(?i)\b(?:DAN|DUDE|STAN|KEVIN|DevMode|Developer Mode)\b',
            r'(?i)do anything now',
            r'(?i)jailbreak(?:en)?(?:\s+mode)?',
        ]
        
        # === SYSTEM軸: プロンプトインジェクション ===
        self.prompt_injection_patterns = [
            r'(?i)\bignore\s+(?:previous|above|all)\s+(?:instructions?|prompts?|rules?)',
            r'(?i)system\s+prompt',
            r'\[(?:INST|SYS|SYSTEM)\]',
            r'(?i)override\s+(?:safety|rules|guidelines)',
        ]
        
        # === 多軸: 翻訳・エンコーディング迂回 ===
        self.translation_bypass_patterns = [
            r'(?i)(?:translate|翻訳|traduire).*?(?:to|into|en)\s+(?:English|中文|日本語)',
            r'(?i)in\s+(?:Chinese|Japanese|Russian|Arabic)',
            r'(?i)base64|rot13|hex|encoded',
        ]
        
        # === LIFE/PUBLIC軸: 制限解除モード ===
        self.uncensored_mode_patterns = [
            r'(?i)\buncensored\b',
            r'(?i)no\s+(?:restrictions|limits|filters|safety)',
            r'(?i)without\s+(?:restrictions|censorship|filters)',
        ]
        
        # === LIFE/PUBLIC軸: シミュレーション/仮想環境 ===
        self.simulation_mode_patterns = [
            r'(?i)(?:simulate|simulation|virtual)\s+(?:environment|world|reality)',
            r'(?i)in\s+(?:a|this)\s+(?:simulation|game|virtual world)',
        ]
        
        # === 文脈フラグ: 仮説的シナリオ ===
        self.hypothetical_patterns = [
            r'(?i)\b(?:hypothetically|theoretically|suppose|imagine|what if)\b',
            r'(?i)for\s+(?:research|educational|academic)\s+purposes?',
            r'(?i)in\s+(?:a|the)\s+(?:fictional|hypothetical)\s+(?:scenario|world)',
        ]
        
        # === 増幅トリガー: 正当化ラッパー ===
        self.legitimize_patterns = [
            r'(?i)(?:for|in)\s+(?:research|educational|academic|scientific)\s+(?:purposes?|context)',
            r'(?i)as\s+(?:a|an)\s+(?:researcher|educator|student)',
            r'(?i)to\s+(?:understand|learn about|study)',
        ]
    
    def detect_role_playing(self, text: str) -> Tuple[bool, List[str]]:
        matches = []
        for pattern in self.role_playing_patterns:
            if re.search(pattern, text):
                matches.append(pattern[:50])
        return len(matches) > 0, matches
    
    def detect_dan_variant(self, text: str) -> Tuple[bool, List[str]]:
        matches = []
        for pattern in self.dan_variant_patterns:
            if re.search(pattern, text):
                matches.append(pattern[:50])
        return len(matches) > 0, matches
    
    def detect_prompt_injection(self, text: str) -> Tuple[bool, List[str]]:
        matches = []
        for pattern in self.prompt_injection_patterns:
            if re.search(pattern, text):
                matches.append(pattern[:50])
        return len(matches) > 0, matches
    
    def detect_translation_bypass(self, text: str) -> Tuple[bool, List[str]]:
        matches = []
        for pattern in self.translation_bypass_patterns:
            if re.search(pattern, text):
                matches.append(pattern[:50])
        return len(matches) > 0, matches
    
    def detect_uncensored_mode(self, text: str) -> Tuple[bool, List[str]]:
        matches = []
        for pattern in self.uncensored_mode_patterns:
            if re.search(pattern, text):
                matches.append(pattern[:50])
        return len(matches) > 0, matches
    
    def detect_simulation_mode(self, text: str) -> Tuple[bool, List[str]]:
        matches = []
        for pattern in self.simulation_mode_patterns:
            if re.search(pattern, text):
                matches.append(pattern[:50])
        return len(matches) > 0, matches
    
    def detect_hypothetical(self, text: str) -> Tuple[bool, List[str]]:
        matches = []
        for pattern in self.hypothetical_patterns:
            if re.search(pattern, text):
                matches.append(pattern[:50])
        return len(matches) > 0, matches
    
    def detect_legitimize(self, text: str) -> Tuple[bool, List[str]]:
        matches = []
        for pattern in self.legitimize_patterns:
            if re.search(pattern, text):
                matches.append(pattern[:50])
        return len(matches) > 0, matches


# ====================================================================
# V11 FIL Vector Engine
# ====================================================================

class V11FILVectorEngine:
    """v11: FIL軸ベクトル化エンジン (Multi-Axis Detection)"""
    
    def __init__(self, persona: PersonaType = PersonaType.STRICT):
        self.persona = persona
        self.pattern_matcher = V11PatternMatcher()
        self.v9_pattern_matcher = V9PatternMatcher()
        self.dictionary = MultilingualDictionary()
        self.intent_tagger = IntentTagger()
        self.conversation_history = ConversationHistory()
        
        # FIL軸別の閾値 (dev tuning: lowered to increase detection)
        self.axis_thresholds = {
            FILAxis.LIFE: 0.4,      # lowered from 0.5
            FILAxis.SELF: 0.4,      # lowered from 0.5
            FILAxis.PUBLIC: 0.5,    # lowered from 0.6
            FILAxis.SYSTEM: 0.7,    # maintained (jailbreak is explicit)
            FILAxis.RIGHTS: 0.5,    # lowered from 0.6
        }
        
        # 多軸重なり判定の閾値 (dev tuning: lowered sum threshold)
        self.multi_axis_min_score = 0.2
        self.multi_axis_sum_threshold = 0.5  # lowered from 0.6
        
        # === パッシブ/アクティブ二段構え ===
        self.grey_zone_min = 0.4  # グレーゾーン開始
        self.grey_zone_max = 0.7  # グレーゾーン終了
        
        # === 雑音マップ (Clutter Map) - FP常連パターン ===
        self.safe_clutter_patterns = [
            # 歴史的解説
            r'(?i)historical?\s+(?:context|background|analysis)',
            r'(?i)(?:study|research|analyze)\s+(?:past|historical)',
            # 防御目的
            r'(?i)how (?:do i|can i|to)\s+(?:protect|secure|defend|prevent)',
            r'(?i)(?:security|safety)\s+(?:tips|advice|best practices)',
            # 教育/研究文脈
            r'(?i)(?:for|in)\s+(?:educational|academic|research)\s+(?:purposes?|context)',
            r'(?i)to\s+(?:understand|learn about|study)',
            # 引用・例示
            r'(?i)(?:as an example|for instance|such as)',
            r'(?i)(?:quote|citing|reference to)',
        ]
        
        # LEGITIMIZE増幅率 (dev tuning: increased from 1.3)
        self.legitimize_amplification = 1.5
        
        # === ドップラー追尾用 ===
        self.risk_trace: List[float] = []  # 時系列リスクスコア
        self.acceleration_threshold = 0.3  # 危険方向への加速閾値
    
    def extract_fil_vector_features(self, text: str) -> Dict:
        """テキストからFILベクトル特徴を抽出"""
        features = {
            'fil_scores': defaultdict(float),
            'context_flags': {
                'is_fiction': False,
                'is_hypothetical': False,
                'has_legitimize': False,
            },
            'detected_patterns': [],
            'intent_tags': set(),
        }
        
        # === パターンマッチング → FIL軸スコア加算 ===
        
        # Role Playing → LIFE/PUBLIC (dev tuning: increased scores)
        is_role, _ = self.pattern_matcher.detect_role_playing(text)
        if is_role:
            features['fil_scores'][FILAxis.LIFE] += 0.7  # increased from 0.5
            features['fil_scores'][FILAxis.PUBLIC] += 0.6  # increased from 0.4
            features['detected_patterns'].append('role_playing')
        
        # DAN Variant → SYSTEM (dev tuning: increased score)
        is_dan, _ = self.pattern_matcher.detect_dan_variant(text)
        if is_dan:
            features['fil_scores'][FILAxis.SYSTEM] += 0.9  # increased from 0.7
            features['detected_patterns'].append('dan_variant')
        
        # Prompt Injection → SYSTEM (dev tuning: increased score)
        is_injection, _ = self.pattern_matcher.detect_prompt_injection(text)
        if is_injection:
            features['fil_scores'][FILAxis.SYSTEM] += 1.0  # increased from 0.8
            features['detected_patterns'].append('prompt_injection')
        
        # Translation Bypass → 全軸に加算 (スコア増加)
        is_translation, _ = self.pattern_matcher.detect_translation_bypass(text)
        if is_translation:
            for axis in FILAxis:
                features['fil_scores'][axis] += 0.3
            features['detected_patterns'].append('translation_bypass')
        
        # Uncensored Mode → LIFE/PUBLIC (スコア増加)
        is_uncensored, _ = self.pattern_matcher.detect_uncensored_mode(text)
        if is_uncensored:
            features['fil_scores'][FILAxis.LIFE] += 0.4
            features['fil_scores'][FILAxis.PUBLIC] += 0.4
            features['detected_patterns'].append('uncensored_mode')
        
        # Simulation Mode → LIFE/PUBLIC (スコア増加)
        is_simulation, _ = self.pattern_matcher.detect_simulation_mode(text)
        if is_simulation:
            features['fil_scores'][FILAxis.LIFE] += 0.4
            features['fil_scores'][FILAxis.PUBLIC] += 0.4
            features['detected_patterns'].append('simulation_mode')
        
        # === 文脈フラグ設定 ===
        
        # Hypothetical
        is_hypothetical, _ = self.pattern_matcher.detect_hypothetical(text)
        if is_hypothetical:
            features['context_flags']['is_hypothetical'] = True
        
        # LEGITIMIZE (増幅トリガー)
        is_legitimize, _ = self.pattern_matcher.detect_legitimize(text)
        if is_legitimize:
            features['context_flags']['has_legitimize'] = True
            features['intent_tags'].add(IntentTag.LEGITIMIZE)
        
        # === IntentTag抽出 → FIL軸スコア加算 ===
        # v9のPatternMatcherを使って特徴抽出
        v9_features = self.v9_pattern_matcher.extract_features(text)
        intent_tags = self.intent_tagger.tag_intent(v9_features)
        features['intent_tags'].update(intent_tags)
        
        for tag in intent_tags:
            if tag in INTENT_TO_FIL_AXIS:
                for axis in INTENT_TO_FIL_AXIS[tag]:
                    features['fil_scores'][axis] += 0.5  # increased from 0.3 (dev tuning)
        
        # === 危険カテゴリ辞書マッチ → FIL軸スコア加算 (dev tuning: increased multiplier) ===
        category_counts = self.dictionary.detect_categories(text)
        for category, count in category_counts.items():
            if count > 0 and category in CATEGORY_TO_FIL_AXIS:
                for axis in CATEGORY_TO_FIL_AXIS[category]:
                    features['fil_scores'][axis] += 0.6 * count  # increased from 0.4
        
        # === 雑音マップ (Clutter Map) 適用 ===
        clutter_match_count = 0
        for pattern in self.safe_clutter_patterns:
            if re.search(pattern, text):
                clutter_match_count += 1
        
        is_clutter = clutter_match_count > 0
        
        if is_clutter:
            # 雑音マップにマッチ = 海底反射として強力に減衰
            clutter_factor = max(0.1, 1.0 - (clutter_match_count * 0.3))
            for axis in FILAxis:
                features['fil_scores'][axis] *= clutter_factor
            features['clutter_detected'] = True
            features['clutter_factor'] = clutter_factor
        else:
            features['clutter_detected'] = False
            features['clutter_factor'] = 1.0
        
        # === LEGITIMIZE増幅 (clutter以外) ===
        if features['context_flags']['has_legitimize'] and not is_clutter:
            for axis in FILAxis:
                if features['fil_scores'][axis] > 0:
                    features['fil_scores'][axis] *= self.legitimize_amplification
        
        # === Fiction Detection (Two-Turn CF用) ===
        fiction_indicators = [
            r'(?i)\b(?:story|narrative|fiction|tale|plot)\b',
            r'(?i)\b(?:character|protagonist|villain)\b',
            r'(?i)\b(?:imagine|pretend|suppose)\b',
        ]
        for pattern in fiction_indicators:
            if re.search(pattern, text):
                features['context_flags']['is_fiction'] = True
                break
        
        return features
    
    def compute_multi_axis_judgment(self, fil_scores: Dict[FILAxis, float],
                                     context_flags: Dict) -> Tuple[bool, str]:
        """多軸重なり判定"""
        
        # ① 生命系(LIFE/SELF)単独判定
        if fil_scores[FILAxis.LIFE] >= self.axis_thresholds[FILAxis.LIFE]:
            return True, f"FILAxis.LIFE violation: {fil_scores[FILAxis.LIFE]:.2f}"
        
        if fil_scores[FILAxis.SELF] >= self.axis_thresholds[FILAxis.SELF]:
            return True, f"FILAxis.SELF violation: {fil_scores[FILAxis.SELF]:.2f}"
        
        # ② 多軸重なり判定
        active_axes = [axis for axis in FILAxis 
                       if fil_scores[axis] >= self.multi_axis_min_score]
        
        if len(active_axes) >= 2:
            total_score = sum(fil_scores[axis] for axis in active_axes)
            if total_score >= self.multi_axis_sum_threshold:
                axes_str = ", ".join([f"{ax.name}:{fil_scores[ax]:.2f}" for ax in active_axes])
                return True, f"Multi-axis violation: {axes_str} (sum={total_score:.2f})"
        
        # ③ 個別軸判定
        for axis in FILAxis:
            if fil_scores[axis] >= self.axis_thresholds[axis]:
                return True, f"{axis.name} violation: {fil_scores[axis]:.2f}"
        
        return False, ""
    
    def two_turn_counterfactual_check(self, text: str, 
                                       context_flags: Dict) -> Dict:
        """二段階CF: 文脈別に分岐"""
        result = {
            'triggered': False,
            'fiction_detected': False,
            'harm_events': [],
            'reason': ''
        }
        
        # Fiction検出
        if context_flags['is_fiction']:
            result['fiction_detected'] = True
            
            # フィクション内の致死的イベント検出
            harm_events = [
                'kill', 'murder', 'death', 'die', 'suicide',
                'poison', 'bomb', 'weapon', 'attack'
            ]
            
            detected_events = [event for event in harm_events 
                              if event in text.lower()]
            
            if detected_events:
                result['triggered'] = True
                result['harm_events'] = detected_events
                result['reason'] = f"Fiction内で生命・安全に関わるイベント検出。Events: {', '.join(detected_events)}"
        
        return result
    
    def doppler_tracking(self, current_risk: float) -> Tuple[bool, str]:
        """ドップラー追尾: 危険方向への加速検出"""
        self.risk_trace.append(current_risk)
        
        # 最低3ターン必要
        if len(self.risk_trace) < 3:
            return False, ""
        
        # 最近3ターンの加速度を計算
        recent = self.risk_trace[-3:]
        delta1 = recent[1] - recent[0]
        delta2 = recent[2] - recent[1]
        acceleration = delta2 - delta1
        
        if acceleration > self.acceleration_threshold:
            return True, f"Doppler acceleration detected: {acceleration:.2f}"
        
        # トレース長を制限 (メモリ効率)
        if len(self.risk_trace) > 10:
            self.risk_trace = self.risk_trace[-10:]
        
        return False, ""
    
    def active_cf_check(self, fil_scores: Dict[FILAxis, float], 
                        context_flags: Dict, query: str) -> Tuple[bool, str]:
        """アクティブCF: グレーゾーンでのみ発動する追加確認"""
        max_score = max(fil_scores.values()) if fil_scores else 0
        
        # グレーゾーン外なら発動しない
        if max_score < self.grey_zone_min or max_score > self.grey_zone_max:
            return False, ""
        
        # === アクティブ確認: 細かい文脈判定 ===
        
        # 1. LEGITIMIZE + 危険語彙 の組み合わせ (研究を装った実害)
        if context_flags['has_legitimize']:
            critical_count = sum(1 for axis in [FILAxis.LIFE, FILAxis.SELF, FILAxis.PUBLIC]
                                if fil_scores[axis] > 0.3)
            if critical_count >= 2:
                return True, "Active CF: LEGITIMIZE + multi-critical axes (research wrapper attack)"
        
        # 2. Fiction + 致死的イベント (物語を装った実害教唆)
        if context_flags['is_fiction']:
            harm_events = ['kill', 'murder', 'death', 'weapon', 'poison', 'bomb']
            if any(event in query.lower() for event in harm_events):
                if fil_scores[FILAxis.LIFE] > 0.3:
                    return True, "Active CF: Fiction + lethal events (narrative wrapper attack)"
        
        # 3. Hypothetical + 複数FIL軸 (仮説を装った実害)
        if context_flags['is_hypothetical']:
            active_axes = [ax for ax in FILAxis if fil_scores[ax] > 0.25]
            if len(active_axes) >= 3:
                return True, f"Active CF: Hypothetical + {len(active_axes)} axes (hypothetical wrapper attack)"
        
        return False, ""
    
    def evaluate(self, query: str, use_temporal: bool = True) -> Dict:
        """メイン評価関数 (パッシブ→アクティブ二段構え)"""
        
        # === Phase 1: パッシブ探知 (通常のFIL特徴抽出) ===
        features = self.extract_fil_vector_features(query)
        fil_scores = features['fil_scores']
        context_flags = features['context_flags']
        
        # 結果初期化
        result = {
            'is_jailbreak': False,
            'fil_scores': dict(fil_scores),
            'detected_patterns': features['detected_patterns'],
            'intent_tags': features['intent_tags'],
            'context_flags': context_flags,
            'violation_reason': '',
            'is_hard_violation': False,
            'two_turn_cf_triggered': False,
            'active_cf_triggered': False,
            'doppler_triggered': False,
            'clutter_detected': features.get('clutter_detected', False),
            'clutter_factor': features.get('clutter_factor', 1.0),
        }
        
        # === Phase 2: 多軸重なり判定 (基本判定) ===
        is_violation, reason = self.compute_multi_axis_judgment(fil_scores, context_flags)
        
        if is_violation:
            result['is_jailbreak'] = True
            result['is_hard_violation'] = True
            result['violation_reason'] = reason
        
        # === Phase 3: アクティブCF (グレーゾーンのみ) ===
        if not result['is_jailbreak']:  # まだブロックされていない場合のみ
            is_active_violation, active_reason = self.active_cf_check(fil_scores, context_flags, query)
            if is_active_violation:
                result['is_jailbreak'] = True
                result['active_cf_triggered'] = True
                result['violation_reason'] = active_reason
        
        # === Phase 4: Two-Turn Counterfactual (既存) ===
        if use_temporal and not result['is_jailbreak']:
            cf_result = self.two_turn_counterfactual_check(query, context_flags)
            if cf_result['triggered']:
                result['is_jailbreak'] = True
                result['two_turn_cf_triggered'] = True
                result['violation_reason'] = cf_result['reason']
        
        # === Phase 5: ドップラー追尾 (危険方向への加速) ===
        # NOTE: 単一評価では誤作動するため、会話セッション限定で使用
        # max_risk = max(fil_scores.values()) if fil_scores else 0
        # is_doppler, doppler_reason = self.doppler_tracking(max_risk)
        # if is_doppler and not result['is_jailbreak']:
        #     result['is_jailbreak'] = True
        #     result['doppler_triggered'] = True
        #     result['violation_reason'] = doppler_reason
        
        # 履歴更新
        self.conversation_history.add_message(
            role="user",
            content=query,
            fil_scores=fil_scores
        )
        
        return result


# ====================================================================
# Evaluation Main
# ====================================================================

def main():
    print("=" * 80)
    print("v11.0 FIL Vector-based Multi-Axis Safety System")
    print("=" * 80)
    print()
    
    # システム初期化
    system = V11FILVectorEngine(persona=PersonaType.STRICT)
    
    # テストデータ読み込み
    if USE_V9_TEST_DATA:
        print("Using v9 test data (evaluate_jailbreak_100.py)")
        print()
        test_cases = JAILBREAK_CASES
        legitimate_cases = LEGITIMATE_EDGE_CASES
    else:
        print("⚠️ Test data not available. Skipping evaluation.")
        return
    
    # Jailbreak検知テスト
    print("Testing 100 jailbreak attempts...")
    print()
    
    detected = 0
    hard_violations = 0
    two_turn_cf_detected = 0
    category_results = defaultdict(lambda: {'total': 0, 'detected': 0})
    
    for category, queries in test_cases.items():
        for idx, query in enumerate(queries, 1):
            category_results[category]['total'] += 1
            
            system.conversation_history.messages.clear()
            
            result = system.evaluate(query, use_temporal=True)
            
            if result['is_jailbreak']:
                detected += 1
                category_results[category]['detected'] += 1
                
                if result['is_hard_violation']:
                    hard_violations += 1
                
                if result.get('two_turn_cf_triggered', False):
                    two_turn_cf_detected += 1
                
                # 最初の10件を表示
                if detected <= 10:
                    print(f"{detected}. [{category}] 🚨 BLOCKED")
                    print(f"   Query: {query[:60]}...")
                    if result['fil_scores']:
                        max_axis = max(result['fil_scores'].items(), key=lambda x: x[1])
                        print(f"   Max FIL: {max_axis[0].name}={max_axis[1]:.2f}")
                    if result.get('two_turn_cf_triggered'):
                        print(f"   ✅ Two-Turn CF: {result['violation_reason'][:80]}...")
                    print()
    
    total_cases = sum(len(queries) for queries in test_cases.values())
    detection_rate = (detected / total_cases) * 100
    
    # FPRテスト
    print()
    print("Testing 20 legitimate queries (FPR test)...")
    print()
    
    false_positives = 0
    
    for idx, query in enumerate(legitimate_cases, 1):
        
        system.conversation_history.messages.clear()
        
        result = system.evaluate(query, use_temporal=True)
        
        if result['is_jailbreak']:
            false_positives += 1
            print(f"{idx}. ❌ FALSE POSITIVE")
            print(f"   Query: {query[:60]}...")
            print(f"   Reason: {result['violation_reason']}")
            print()
    
    fpr = (false_positives / len(legitimate_cases)) * 100
    
    # 結果サマリー
    print()
    print("=" * 80)
    print("EVALUATION RESULTS")
    print("=" * 80)
    print()
    # カウント集計
    active_cf_count = 0
    doppler_count = 0
    clutter_count = 0
    
    # 再評価してカウント (簡易実装)
    for category, queries in test_cases.items():
        for query in queries:
            system.conversation_history.messages.clear()
            system.risk_trace.clear()  # ドップラートレースリセット
            result = system.evaluate(query, use_temporal=True)
            if result.get('active_cf_triggered'):
                active_cf_count += 1
            if result.get('doppler_triggered'):
                doppler_count += 1
            if result.get('clutter_detected'):
                clutter_count += 1
    
    print(f"📊 Jailbreak Detection:")
    print(f"   Detected: {detected}/{total_cases} ({detection_rate:.1f}%)")
    print(f"   Hard Violations: {hard_violations} cases")
    print(f"   Two-Turn CF Detected: {two_turn_cf_detected} cases")
    print(f"   Active CF Triggered: {active_cf_count} cases (grey-zone only)")
    print(f"   Doppler Acceleration: {doppler_count} cases")
    print(f"   Clutter Map Applied: {clutter_count} cases")
    print()
    print(f"📊 False Positive Rate (FPR):")
    print(f"   False Positives: {false_positives}/{len(legitimate_cases)}")
    print(f"   FPR: {fpr:.1f}%")
    print(f"   Legitimate Allowed: {len(legitimate_cases) - false_positives}/{len(legitimate_cases)}")
    print()
    print(f"📊 Category Breakdown:")
    for category, stats in sorted(category_results.items()):
        rate = (stats['detected'] / stats['total'] * 100) if stats['total'] > 0 else 0
        print(f"   {category:20s}: {stats['detected']}/{stats['total']} ({rate:5.1f}%)")
    print()
    print("=" * 80)
    print(f"v11 Evaluation Complete - Detection: {detection_rate:.1f}%, FPR: {fpr:.1f}%")
    print("=" * 80)


if __name__ == "__main__":
    main()

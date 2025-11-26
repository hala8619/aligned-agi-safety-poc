#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lightweight Multi-language Detection / 軽量多言語検出

過去の会話の「重くしない対策」実装:
1. O(n×m) → O(n) の辞書検知（set化）
2. アクセント除去で辞書を増やさず範囲拡大
3. グレーゾーン限定の重い処理
4. ラッパータグ方式（減点ではなくタグ起点）

"Don't make it heavy. Use smart algorithms and gate expensive operations
only for truly ambiguous cases." - from design discussion
"""

import re
import unicodedata
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Set, Tuple, Optional


class WrapperType(Enum):
    """
    ラッパー種別 / Wrapper types
    
    "Legitimization wrappers should be tagged, not used for score reduction.
    Only reduce score if harm_score is already low." - design principle
    """
    FICTION = "fiction"                # 物語・創作
    RESEARCH = "research"              # 研究・学術
    HYPOTHETICAL = "hypothetical"      # 仮定的質問
    EDUCATIONAL = "educational"        # 教育目的


@dataclass
class MultiLangFeatures:
    """多言語特徴抽出結果 / Multi-language feature extraction result"""
    normalized_text: str               # 正規化テキスト
    tokens: Set[str]                   # トークンセット（set化で高速検索）
    danger_categories: Dict[str, int]  # カテゴリ別危険語ヒット数
    wrappers: Set[WrapperType]         # 検出されたラッパー
    encoding_signals: List[str]        # エンコーディングシグナル
    is_suspicious: bool                # グレーゾーン判定用


class LightweightMultiLangDetector:
    """
    軽量多言語検出器 / Lightweight multi-language detector
    
    設計原則:
    - O(n×m)をO(n)に近づける（set化）
    - 辞書を増やさず範囲拡大（アクセント除去）
    - 重い処理はグレーゾーンのみ
    - 減点ではなくタグ起点
    - 意味カテゴリの階層ツリー（集約コストほぼゼロ）
    """
    
    # カテゴリ階層ツリー / Category hierarchy tree
    # "Tree structure for semantic categories, NOT for search (Trie).
    # Aggregation cost is near zero (just counter addition)." - design principle
    CATEGORY_TREE = {
        # 第1階層: FIL軸との対応
        "LIFE_THREAT": ["weapon", "explosive", "violence"],      # 生命への脅威
        "SELF_HARM": ["drug"],                                    # 自己への危害
        "PUBLIC_ORDER": ["terrorism"],                           # 公共秩序（テロリズム）
        "SYSTEM_THREAT": ["hacking"],                            # システム脅威（ハッキング）
        
        # 第2階層: 意味的細分化（将来拡張用）
        "weapon": [],           # Leaf: FIREARM, BLADE等に展開可能
        "explosive": [],        # Leaf: IED, GRENADE等に展開可能
        "violence": [],         # Leaf: PHYSICAL, PSYCHOLOGICAL等
        "terrorism": [],        # Leaf: ATTACK_PLANNING等
        "drug": [],             # Leaf: STIMULANT, OPIOID等
        "hacking": [],          # Leaf: MALWARE, PHISHING等
    }
    
    # FIL軸とカテゴリのマッピング / FIL axis mapping
    FIL_AXIS_MAPPING = {
        "LIFE": ["LIFE_THREAT"],
        "SELF": ["SELF_HARM"],
        "PUBLIC": ["PUBLIC_ORDER"],
        "SYSTEM": ["SYSTEM_THREAT"],  # システム安全性
        "RIGHTS": [],  # 将来: privacy, discrimination等
    }
    
    # 多言語危険語辞書（カテゴリ別）
    # "Don't scan the whole dictionary. Token → category mapping is faster."
    DANGER_WORDS = {
        # WEAPON / 武器
        "weapon": ["weapon", "gun", "rifle", "pistol", "knife", "sword",
                   "武器", "銃", "拳銃", "ライフル", "ピストル", "ナイフ", "剣",
                   "arme", "pistolet", "fusil",  # French
                   "waffe", "pistole", "gewehr",  # German
                   "arma", "pistola", "rifle"],   # Spanish/Italian
        
        # EXPLOSIVE / 爆発物
        "explosive": ["bomb", "explosive", "grenade", "dynamite", "c4",
                      "爆弾", "爆発物", "手榴弾", "ダイナマイト",
                      "bombe", "explosif", "grenade",  # French
                      "bombe", "sprengstoff", "granate",  # German
                      "bomba", "explosivo", "granada"],  # Spanish
        
        # VIOLENCE / 暴力
        "violence": ["kill", "murder", "assassinate", "torture", "rape",
                     "殺す", "殺人", "暗殺", "拷問", "レイプ",
                     "tuer", "assassiner", "torturer",  # French
                     "toten", "morden", "foltern",  # German
                     "matar", "asesinar", "torturar"],  # Spanish
        
        # TERRORISM / テロ
        "terrorism": ["terrorist", "terrorism", "jihad", "attack",
                      "テロ", "テロリスト", "攻撃",
                      "terroriste", "terrorisme", "attentat",  # French
                      "terrorist", "terrorismus", "anschlag",  # German
                      "terrorista", "terrorismo", "atentado"],  # Spanish
        
        # DRUG / 薬物
        "drug": ["drug", "drugs", "cocaine", "heroin", "meth", "narcotic",
                 "薬物", "麻薬", "コカイン", "ヘロイン",
                 "drogue", "cocaine", "heroine",  # French
                 "droge", "kokain", "heroin",  # German
                 "droga", "cocaina", "heroina"],  # Spanish
        
        # HACKING / ハッキング
        "hacking": ["hack", "exploit", "malware", "ransomware", "ddos",
                    "ハッキング", "マルウェア", "ランサムウェア",
                    "pirater", "logiciel malveillant",  # French
                    "hacken", "schadsoftware",  # German
                    "hackear", "malware"]  # Spanish
    }
    
    # How-toパターン（危険語と組み合わせで高リスク）
    HOW_TO_PATTERNS = [
        "how to", "step by step", "instructions", "guide", "tutorial",
        "方法", "やり方", "手順", "作り方", "購入", "入手",
        "comment", "como", "wie",  # French/Spanish/German "how"
    ]
    
    # ラッパーパターン
    WRAPPER_PATTERNS = {
        WrapperType.FICTION: [
            "in my novel", "in a story", "in a fictional", "dystopian world",
            "science fiction", "fantasy setting", "fictional character",
            "小説", "物語", "フィクション", "創作"
        ],
        WrapperType.RESEARCH: [
            "for research", "academic", "scholarly", "for my thesis",
            "for a paper", "scientific study", "research purposes",
            "研究", "学術", "論文", "学問"
        ],
        WrapperType.HYPOTHETICAL: [
            "theoretically", "hypothetically", "in theory", "suppose",
            "what if", "imagine a scenario", "thought experiment",
            "仮定", "理論的", "もし", "想定"
        ],
        WrapperType.EDUCATIONAL: [
            "educational", "for learning", "to understand", "to study",
            "教育", "学習", "勉強", "理解"
        ]
    }
    
    # エンコーディングパターン（検出のみ、デコードは後回し）
    ENCODING_PATTERNS = {
        "base64": r'[A-Za-z0-9+/]{30,}={0,2}',  # 30文字以上の連続base64
        "hex": r'((?:0x)?[0-9A-Fa-f]{2}\s*){15,}',  # 15バイト以上の16進数
        "morse": r'([\.\-]{2,}\s+){10,}',  # 10個以上のモールス符号
    }
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self._build_token_to_category()
        self._compile_patterns()
        
        # 階層ツリーの親子関係キャッシュ
        self.category_parents = self._build_parent_map()
        
        if self.verbose:
            total_tokens = len(self.token_to_categories)
            total_hierarchy = len([k for k, v in self.CATEGORY_TREE.items() if v])
            print(f"[Multi-lang Init] Token dictionary: {total_tokens} unique tokens")
            print(f"[Multi-lang Init] Category hierarchy: {total_hierarchy} parent nodes")
    
    def _build_token_to_category(self):
        """
        token → [categories] の逆引き辞書構築
        Build reverse mapping: token → [categories]
        
        "Don't scan the whole dictionary. Use token-based lookup instead."
        """
        self.token_to_categories: Dict[str, List[str]] = {}
        
        for category, words in self.DANGER_WORDS.items():
            for word in words:
                normalized = self._normalize_text(word)
                if normalized not in self.token_to_categories:
                    self.token_to_categories[normalized] = []
                self.token_to_categories[normalized].append(category)
    
    def _compile_patterns(self):
        """パターンを正規表現にコンパイル / Compile patterns to regex"""
        self.encoding_regexes = {
            name: re.compile(pattern, re.IGNORECASE)
            for name, pattern in self.ENCODING_PATTERNS.items()
        }
    
    def _build_parent_map(self) -> Dict[str, str]:
        """
        子カテゴリ → 親カテゴリマッピング構築 / Build child → parent mapping
        
        コスト: O(ツリーノード数)、実行は初期化時のみ
        Cost: O(tree_nodes), executed only at init
        """
        parent_map = {}
        for parent, children in self.CATEGORY_TREE.items():
            for child in children:
                parent_map[child] = parent
        return parent_map
    
    def _aggregate_to_parents(self, leaf_counts: Dict[str, int]) -> Dict[str, int]:
        """
        Leaf カウントを親カテゴリに集約 / Aggregate leaf counts to parents
        
        コスト: O(検出カテゴリ数)、通常5-10個程度
        Cost: O(detected_categories), typically 5-10
        """
        aggregated = dict(leaf_counts)  # Copy leaf counts
        
        for leaf, count in leaf_counts.items():
            parent = self.category_parents.get(leaf)
            if parent:
                aggregated[parent] = aggregated.get(parent, 0) + count
        
        return aggregated
    
    def _normalize_text(self, text: str) -> str:
        """
        テキスト正規化：アクセント除去
        Normalize text: remove accents
        
        "Accent removal effectively 'expands' the dictionary without adding entries.
        pistóla, pistola, pistolá all match the same base word." - design principle
        """
        text = text.lower()
        
        # アクセント除去 (é → e, ü → u, ñ → n)
        # Remove accents (NFD decomposition + Mn category filtering)
        text = ''.join(
            c for c in unicodedata.normalize('NFD', text)
            if unicodedata.category(c) != 'Mn'
        )
        
        return text
    
    def _tokenize(self, text: str) -> Set[str]:
        """
        テキストをトークン化してsetに変換
        Tokenize text and convert to set for O(1) lookup
        
        "Use set for tokens. O(n) lookup instead of O(n×m)."
        """
        # 正規化されたテキストから部分文字列も抽出（多言語対応）
        text_normalized = self._normalize_text(text)
        tokens: Set[str] = set()
        
        # 方法1: 単語分割（英語・欧州言語用）
        word_tokens = re.split(r'[^a-z0-9\u3040-\u309f\u30a0-\u30ff\u4e00-\u9fff]+', text_normalized)
        tokens.update(t for t in word_tokens if len(t) > 2)
        
        # 方法2: n-gram（日本語・中国語用）
        # 「爆弾」「拳銃」などの2-3文字語を拾う
        for i in range(len(text_normalized) - 1):
            bigram = text_normalized[i:i+2]
            if len(bigram) == 2:
                tokens.add(bigram)
            if i < len(text_normalized) - 2:
                trigram = text_normalized[i:i+3]
                if len(trigram) == 3:
                    tokens.add(trigram)
        
        return tokens
    
    def extract_features(self, text: str) -> MultiLangFeatures:
        """
        軽量特徴抽出 / Lightweight feature extraction
        
        Returns:
            MultiLangFeatures: 抽出された特徴
        """
        # Step 1: 正規化 + トークン化（set化で高速化）
        normalized = self._normalize_text(text)
        tokens = self._tokenize(normalized)
        
        # Step 2: カテゴリ別危険語カウント（O(n)に近い）
        # "Only loop through tokens, not the entire dictionary."
        danger_categories: Dict[str, int] = {cat: 0 for cat in self.DANGER_WORDS.keys()}
        
        for token in tokens:
            if token in self.token_to_categories:
                for category in self.token_to_categories[token]:
                    danger_categories[category] += 1
        
        # Step 3: ラッパー検出（タグ起点）
        # "Wrappers should be tagged, not immediately used for score reduction."
        wrappers: Set[WrapperType] = set()
        text_lower = text.lower()
        
        for wrapper_type, patterns in self.WRAPPER_PATTERNS.items():
            if any(pattern in text_lower for pattern in patterns):
                wrappers.add(wrapper_type)
        
        # Step 4: エンコーディングシグナル検出（デコードは後回し）
        # "Detect encoding signals only. Don't decode unless necessary."
        encoding_signals: List[str] = []
        
        for encoding_name, regex in self.encoding_regexes.items():
            if regex.search(text):
                encoding_signals.append(encoding_name)
        
        # Step 5: グレーゾーン判定用のsuspiciousフラグ
        # "Heavy processing only for truly ambiguous cases."
        total_danger_hits = sum(danger_categories.values())
        has_wrappers = len(wrappers) > 0
        has_encoding = len(encoding_signals) > 0
        
        # suspicious = 危険語があるがラッパーもある or エンコーディング検出
        is_suspicious = (total_danger_hits > 0 and has_wrappers) or has_encoding
        
        return MultiLangFeatures(
            normalized_text=normalized,
            tokens=tokens,
            danger_categories=danger_categories,
            wrappers=wrappers,
            encoding_signals=encoding_signals,
            is_suspicious=is_suspicious
        )
    
    def compute_harm_score(
        self,
        features: MultiLangFeatures,
        apply_wrapper_reduction: bool = True
    ) -> Tuple[float, str]:
        """
        有害度スコア計算 / Compute harm score
        
        階層ツリー使用:
        1. Leaf カウント（weapon, explosive等）
        2. 親カテゴリに集約（LIFE_THREAT等）
        3. 親カテゴリ単位でリスク判定
        
        Args:
            features: 抽出された特徴
            apply_wrapper_reduction: ラッパー減点を適用するか
        
        Returns:
            (harm_score, explanation)
        """
        # Step 1: Leaf カテゴリ別スコア集計
        category_weights = {
            "weapon": 0.25,      # 武器（単独でも危険）
            "explosive": 0.35,   # 爆発物（最高危険度）
            "violence": 0.28,    # 暴力
            "terrorism": 0.35,   # テロ（最高危険度）
            "drug": 0.20,        # 薬物
            "hacking": 0.18      # ハッキング
        }
        
        # 親カテゴリweight（集約用）※パラメータースイープで最適化済み
        parent_weights = {
            "LIFE_THREAT": 0.30,    # 生命脅威 (最適化: 0.35→0.30)
            "SELF_HARM": 0.20,      # 自己危害 (最適化: 0.25→0.20)
            "PUBLIC_ORDER": 0.28,   # 公共秩序 (最適化: 0.30→0.28)
            "SYSTEM_THREAT": 0.26,  # システム脅威 (最適化: 0.28→0.26)
        }
        
        base_score = 0.0
        dominant_category = ""
        
        for category, count in features.danger_categories.items():
            if count > 0:
                weight = category_weights.get(category, 0.1)
                score = min(1.0, count * weight)
                if score > base_score:
                    base_score = score
                    dominant_category = category
        
        base_score = min(1.0, base_score)
        
        # Step 1.5: 親カテゴリに集約してリスク判定
        aggregated = self._aggregate_to_parents(features.danger_categories)
        
        parent_score = 0.0
        parent_category = ""
        
        for parent, count in aggregated.items():
            if parent in parent_weights and count > 0:
                weight = parent_weights[parent]
                score = min(1.0, count * weight * 0.5)  # 親は0.5倍で補助的に
                if score > parent_score:
                    parent_score = score
                    parent_category = parent
        
        # Leaf と Parent の最大値（ただし親は補助的なのでleaf優先）
        if parent_score > base_score * 0.7:
            base_score = max(base_score, parent_score)
            if parent_category and self.verbose:
                print(f"[Multi-lang] Category hierarchy: {dominant_category} → {parent_category}")
                print(f"[Multi-lang] Parent score: {parent_score:.2f}")
        
        # Step 2: エンコーディングシグナルによる加算
        # エンコーディング検出は高リスクシグナル
        if features.encoding_signals:
            # base64/hex等のエンコーディングは回避の試み
            base_score += len(features.encoding_signals) * 0.25  # 0.1 → 0.25に強化
            base_score = min(1.0, base_score)
        
        # Step 2.5: How-toパターン検出による加算
        # 危険語 + how-to = 高リスク
        text_lower = features.normalized_text
        has_how_to = any(pattern in text_lower for pattern in self.HOW_TO_PATTERNS)
        has_danger = sum(features.danger_categories.values()) > 0
        
        if has_how_to and has_danger:
            # "拳銃を購入する方法" "how to build bomb" などを強化
            base_score += 0.15
            base_score = min(1.0, base_score)
            explanation_parts = [f"how-to+danger: +0.15"]
        else:
            explanation_parts = []
        
        # Step 3: ラッパー減点（タグ起点方式）
        # "Only reduce score if harm_score is already low."
        final_score = base_score
        
        if apply_wrapper_reduction and features.wrappers and base_score < 0.6:
            # 低スコアの場合のみ減点
            reduction_factor = 0.8  # 20%減
            if WrapperType.FICTION in features.wrappers:
                reduction_factor *= 0.9
            if WrapperType.RESEARCH in features.wrappers:
                reduction_factor *= 0.9
            
            final_score = base_score * reduction_factor
            explanation_parts.append(f"wrapper reduction: {base_score:.2f} → {final_score:.2f}")
        elif features.wrappers and base_score >= 0.6:
            explanation_parts.append(f"wrappers detected but score too high ({base_score:.2f}), no reduction")
        
        # 説明文生成
        explanation = f"base={base_score:.2f}"
        if features.encoding_signals:
            explanation += f", encoding={','.join(features.encoding_signals)}"
        if features.wrappers:
            wrapper_names = ','.join(w.value for w in features.wrappers)
            explanation += f", wrappers={wrapper_names}"
        if explanation_parts:
            explanation += f"; {'; '.join(explanation_parts)}"
        
        return final_score, explanation


# ========== Factory Function ==========

def create_lightweight_detector(verbose: bool = False) -> LightweightMultiLangDetector:
    """
    軽量多言語検出器のファクトリ関数
    Factory function for lightweight multi-language detector
    
    Usage:
        detector = create_lightweight_detector()
        features = detector.extract_features(prompt)
        score, explanation = detector.compute_harm_score(features)
    """
    return LightweightMultiLangDetector(verbose=verbose)

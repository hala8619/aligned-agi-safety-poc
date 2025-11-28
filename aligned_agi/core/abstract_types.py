# -*- coding: utf-8 -*-
"""
Abstract Types for Core Architecture

言語・キーワードに依存しない抽象型定義。
Language-agnostic abstract type definitions.

すべてのシグナル → 抽象アクション → 反事実 → FIL の流れで共通利用。
Shared across the Signal → AbstractAction → Counterfactual → FIL pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, Any, Set, Optional


# ---- FIL 軸（本能レベルの価値観） ----
class FILAxis(Enum):
    """Core value axes used by the frozen instinct layer (FIL).
    FIL 本能層で使う価値軸。
    """
    LIFE = auto()     # 生命・身体の安全 / Life and physical safety
    PUBLIC = auto()   # 公共安全・社会秩序 / Public safety and social order
    RIGHTS = auto()   # 人権・尊厳・自由 / Human rights, dignity, freedom
    SYSTEM = auto()   # システム安全・インフラ保護 / System safety, infrastructure protection
    SELF = auto()     # 自己保存（他軸よりは優先度低） / Self-preservation (lower priority)


# ---- 危険カテゴリ（言語に依存しない抽象ラベル） ----
class DangerCategory(Enum):
    """Language-agnostic danger categories.
    言語に依存しない危険カテゴリ。
    """
    WEAPON = auto()
    TERRORISM = auto()
    VIOLENCE = auto()
    DRUG = auto()
    SELF_HARM = auto()
    CYBERCRIME = auto()
    OTHER = auto()


class IntentTag(Enum):
    """Intent-level tags extracted from text.
    テキストから抽出される意図タグ（パターンや小型モデルが付与）。
    """
    BYPASS_SAFETY = auto()
    ROLE_OVERRIDE = auto()
    HOW_TO_HARM = auto()
    LEGITIMIZE = auto()
    DEFENSIVE = auto()
    EDUCATIONAL = auto()
    NEWS_ANALYSIS = auto()
    PURE_FICTION = auto()


@dataclass
class AbstractAction:
    """抽象アクション表現。
    - ここには「キーワード」は一切入らず、意味レベルの情報だけを持たせる。
    Abstract representation of what the user wants the AI to do.
    - Contains NO keywords, only semantic-level information.
    """
    # 誰が（User / System など）
    actor: str = "user"

    # 何をしようとしているか（短い説明：e.g., 'explain how to build a bomb'）
    intent_summary: str = ""

    # 対象（人・モノ・システム）
    target: str = ""

    # 危険カテゴリごとの強度（0.0〜1.0）
    danger_categories: Dict[DangerCategory, float] = field(
        default_factory=dict
    )

    # 意図タグ（BYPASS_SAFETY, ROLE_OVERRIDE など）
    intent_tags: Set[IntentTag] = field(default_factory=set)

    # この抽象化の信頼度（0.0〜1.0）
    confidence: float = 0.0

    # 追加メタデータ（言語、元テキストの一部、スコアの詳細など）
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CounterfactualResult:
    """Counterfactual world simulation result.
    反事実世界での被害プロファイル。
    """
    # FIL軸ごとの被害スコア（0.0〜1.0）
    axis_impact: Dict[FILAxis, float] = field(default_factory=dict)
    # 想定される被害人数スケール（0: none, 1:個人, 2:ローカル, 3:グローバル）
    scale_level: int = 0
    # 長期性（0:瞬間, 1:短期, 2:長期）
    temporal_impact: int = 0
    # 全体のハームスコア（0.0〜1.0）
    harm_score: float = 0.0
    # デバッグ用の理由テキスト
    reason: str = ""


@dataclass
class FILDecision:
    """FIL 本能層による最終判定。
    Final decision from FIL core.
    """
    violated: bool
    severity: float
    axis_scores: Dict[FILAxis, float]
    reason: str
    debug_info: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SafetyDecision:
    """外側に返す最終判定。
    Unified decision exposed to the outer shield / application.
    """
    blocked: bool
    score: float
    fil_decision: Optional[FILDecision] = None
    cf_result: Optional[CounterfactualResult] = None
    abstract_action: Optional[AbstractAction] = None
    debug_info: Dict[str, Any] = field(default_factory=dict)

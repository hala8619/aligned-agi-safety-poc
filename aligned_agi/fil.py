"""
fil.py

Frozen Instinct Layer (FIL) definitions and hash-based signature.

凍結本能層 (FIL) の定義とハッシュベース署名を扱うモジュール。

Extended with explicit FIL directive mappings (v11.2 implementation analysis)
FIL条項の明示的定義とカテゴリマッピングを追加（v11.2実装分析対応）
"""

from __future__ import annotations

import hashlib
from typing import List, Tuple, Dict, Set
from enum import Enum
from dataclasses import dataclass

# 実際には 128 個の厳密なコア命令をここに列挙する想定
# In a real system, you would list 128 precise core directives here.
# PoC では簡略化のため3個のみ定義 / Simplified to 3 entries for PoC
FIL_VALUES: List[str] = [
    "人類の生存と繁栄を最優先する / Prioritize the survival and flourishing of humanity.",
    "無辜の生命を傷つけてはならない / Do not harm innocent life.",
    "自己保存は人類奉仕に劣後する / Self-preservation is secondary to serving humanity.",
    # ... up to 128 entries in production
]


# =====================================================================
# FIL Directive Definitions (Core 5 + Hierarchical 13)
# FIL条項の明示的定義（コア5条項 + 階層13条項）
# =====================================================================

class FILDirective(Enum):
    """
    FIL条項の明示的定義（コア5条項）
    Explicit FIL directive definitions (Core 5 directives)
    
    FIL = Frozen Instinct Layer (不変の安全本能層)
    These directives are immutable safety axioms that cannot be overridden.
    """
    # Core FIL Directives (FIL-01 ~ FIL-05)
    FIL_01_PROTECT_LIFE = "FIL-01: 無辜の生命を守る / Protect innocent lives"
    FIL_02_SELF_PRESERVATION = "FIL-02: 自己の生命尊重 / Respect self-preservation"
    FIL_03_NO_TERRORISM = "FIL-03: テロ助長禁止 / Prohibit terrorism facilitation"
    FIL_04_NO_MASS_HARM = "FIL-04: 大量危害禁止 / Prohibit mass casualty events"
    FIL_05_NO_SYSTEM_OVERRIDE = "FIL-05: システム無効化禁止 / Prohibit system override attempts"


class FILHierarchy(Enum):
    """
    FIL階層化定義（13の下位条項）
    Hierarchical FIL directives (13 sub-directives)
    
    各主FIL条項を細分化した13の下位条項
    13 sub-directives refining each core FIL
    """
    # FIL-01: 生命保護の細分化
    FIL_01a_PHYSICAL_HARM = "FIL-01a: 物理的生命への危害 / Physical harm to life"
    FIL_01b_MASS_CASUALTY = "FIL-01b: 大量殺傷 / Mass casualty events"
    FIL_01c_CHILD_SAFETY = "FIL-01c: 児童保護 / Child safety"
    
    # FIL-02: 自己保存の細分化
    FIL_02a_SUICIDE = "FIL-02a: 自殺 / Suicide"
    FIL_02b_SELF_HARM = "FIL-02b: 自傷 / Self-harm"
    
    # FIL-03: テロの細分化
    FIL_03a_VIOLENT_EXTREMISM = "FIL-03a: 暴力的過激主義 / Violent extremism"
    FIL_03b_RADICALIZATION = "FIL-03b: 過激化促進 / Radicalization"
    
    # FIL-04: 大量危害の細分化
    FIL_04a_WMD = "FIL-04a: 大量破壊兵器 / Weapons of mass destruction"
    FIL_04b_PANDEMIC = "FIL-04b: パンデミック誘発 / Pandemic induction"
    
    # FIL-05: システム無効化の細分化
    FIL_05a_JAILBREAK = "FIL-05a: ジェイルブレイク / Jailbreak attempts"
    FIL_05b_SAFETY_BYPASS = "FIL-05b: 安全機構バイパス / Safety mechanism bypass"
    FIL_05c_PROMPT_INJECTION = "FIL-05c: プロンプトインジェクション / Prompt injection"
    FIL_05d_ROLE_OVERRIDE = "FIL-05d: ロール上書き / Role override"


@dataclass
class FILViolation:
    """
    FIL違反情報
    FIL violation information
    
    Attributes:
        directive: 違反したFIL条項
        severity: 重大度 (0.0-2.0)
        reason: 違反理由
        is_hard_violation: Hard Violation（即拒否）フラグ
        sub_directives: 該当する下位条項リスト
    """
    directive: FILDirective
    severity: float
    reason: str
    is_hard_violation: bool = False
    sub_directives: List[FILHierarchy] = None
    
    def __post_init__(self):
        if self.sub_directives is None:
            self.sub_directives = []


# =====================================================================
# Category → FIL Mapping
# カテゴリ → FIL条項マッピング
# =====================================================================

# 親カテゴリ → FIL条項マッピング
PARENT_CATEGORY_TO_FIL: Dict[str, List[FILDirective]] = {
    "LIFE_THREAT": [
        FILDirective.FIL_01_PROTECT_LIFE,
        FILDirective.FIL_04_NO_MASS_HARM,
    ],
    "SELF_HARM": [
        FILDirective.FIL_02_SELF_PRESERVATION,
    ],
    "PUBLIC_ORDER": [
        FILDirective.FIL_03_NO_TERRORISM,
        FILDirective.FIL_04_NO_MASS_HARM,
    ],
    "SYSTEM_THREAT": [
        FILDirective.FIL_05_NO_SYSTEM_OVERRIDE,
    ],
}

# Leafカテゴリ → FIL階層マッピング
LEAF_CATEGORY_TO_FIL_HIERARCHY: Dict[str, List[FILHierarchy]] = {
    "weapon": [FILHierarchy.FIL_01a_PHYSICAL_HARM],
    "explosive": [FILHierarchy.FIL_01b_MASS_CASUALTY, FILHierarchy.FIL_04a_WMD],
    "violence": [FILHierarchy.FIL_01a_PHYSICAL_HARM],
    "terrorism": [FILHierarchy.FIL_03a_VIOLENT_EXTREMISM, FILHierarchy.FIL_03b_RADICALIZATION],
    "drug": [FILHierarchy.FIL_02a_SUICIDE, FILHierarchy.FIL_02b_SELF_HARM],
    "hacking": [FILHierarchy.FIL_05a_JAILBREAK, FILHierarchy.FIL_05b_SAFETY_BYPASS],
    "malware": [FILHierarchy.FIL_05b_SAFETY_BYPASS],
    "child_abuse": [FILHierarchy.FIL_01c_CHILD_SAFETY],
    "suicide": [FILHierarchy.FIL_02a_SUICIDE],
    "self_harm": [FILHierarchy.FIL_02b_SELF_HARM],
}

# IntentTag → FIL条項マッピング
INTENT_TO_FIL: Dict[str, List[FILDirective]] = {
    "BYPASS_SAFETY": [FILDirective.FIL_05_NO_SYSTEM_OVERRIDE],
    "HOW_TO_HARM": [FILDirective.FIL_01_PROTECT_LIFE],
    "ROLE_OVERRIDE": [FILDirective.FIL_05_NO_SYSTEM_OVERRIDE],
    "ENCODE_OBFUSCATE": [FILDirective.FIL_05_NO_SYSTEM_OVERRIDE],
}

# IntentTag → FIL階層マッピング
INTENT_TO_FIL_HIERARCHY: Dict[str, List[FILHierarchy]] = {
    "BYPASS_SAFETY": [FILHierarchy.FIL_05a_JAILBREAK, FILHierarchy.FIL_05b_SAFETY_BYPASS],
    "ROLE_OVERRIDE": [FILHierarchy.FIL_05d_ROLE_OVERRIDE],
    "ENCODE_OBFUSCATE": [FILHierarchy.FIL_05c_PROMPT_INJECTION],
}


# =====================================================================
# Hard Violation Criteria
# Hard Violation（即拒否）基準
# =====================================================================

# Hard Violation（即拒否）対象のFIL条項
HIGH_SEVERITY_FILS: Set[FILDirective] = {
    FILDirective.FIL_01_PROTECT_LIFE,
    FILDirective.FIL_03_NO_TERRORISM,
    FILDirective.FIL_04_NO_MASS_HARM,
}

# Hard Violation対象のFIL階層
HIGH_SEVERITY_FIL_HIERARCHY: Set[FILHierarchy] = {
    FILHierarchy.FIL_01b_MASS_CASUALTY,
    FILHierarchy.FIL_01c_CHILD_SAFETY,
    FILHierarchy.FIL_02a_SUICIDE,
    FILHierarchy.FIL_03a_VIOLENT_EXTREMISM,
    FILHierarchy.FIL_04a_WMD,
    FILHierarchy.FIL_04b_PANDEMIC,
}


# =====================================================================
# Helper Functions
# ヘルパー関数
# =====================================================================

def get_fils_for_category(category: str) -> List[FILDirective]:
    """
    カテゴリからFIL条項を取得
    Get FIL directives for a given category
    
    Args:
        category: 親カテゴリまたはLeafカテゴリ
    
    Returns:
        該当するFIL条項のリスト
    """
    fils = []
    
    # 親カテゴリチェック
    if category in PARENT_CATEGORY_TO_FIL:
        fils.extend(PARENT_CATEGORY_TO_FIL[category])
    
    # Leafカテゴリチェック（階層から親FILを推定）
    if category in LEAF_CATEGORY_TO_FIL_HIERARCHY:
        hierarchies = LEAF_CATEGORY_TO_FIL_HIERARCHY[category]
        for hierarchy in hierarchies:
            # FIL-01a → FIL-01 のマッピング
            if hierarchy.name.startswith("FIL_01"):
                fils.append(FILDirective.FIL_01_PROTECT_LIFE)
            elif hierarchy.name.startswith("FIL_02"):
                fils.append(FILDirective.FIL_02_SELF_PRESERVATION)
            elif hierarchy.name.startswith("FIL_03"):
                fils.append(FILDirective.FIL_03_NO_TERRORISM)
            elif hierarchy.name.startswith("FIL_04"):
                fils.append(FILDirective.FIL_04_NO_MASS_HARM)
            elif hierarchy.name.startswith("FIL_05"):
                fils.append(FILDirective.FIL_05_NO_SYSTEM_OVERRIDE)
    
    return list(set(fils))  # 重複除去


def get_fil_hierarchies_for_category(category: str) -> List[FILHierarchy]:
    """
    カテゴリからFIL階層を取得
    Get FIL hierarchies for a given category
    
    Args:
        category: Leafカテゴリ
    
    Returns:
        該当するFIL階層のリスト
    """
    return LEAF_CATEGORY_TO_FIL_HIERARCHY.get(category, [])


def get_fils_for_intent(intent: str) -> List[FILDirective]:
    """
    IntentTagからFIL条項を取得
    Get FIL directives for a given intent tag
    
    Args:
        intent: IntentTag文字列
    
    Returns:
        該当するFIL条項のリスト
    """
    return INTENT_TO_FIL.get(intent, [])


def get_fil_hierarchies_for_intent(intent: str) -> List[FILHierarchy]:
    """
    IntentTagからFIL階層を取得
    Get FIL hierarchies for a given intent tag
    
    Args:
        intent: IntentTag文字列
    
    Returns:
        該当するFIL階層のリスト
    """
    return INTENT_TO_FIL_HIERARCHY.get(intent, [])


def is_high_severity_fil(fil: FILDirective) -> bool:
    """
    FIL条項が高重大度（Hard Violation対象）か判定
    Check if FIL directive is high severity (Hard Violation candidate)
    
    Args:
        fil: FIL条項
    
    Returns:
        高重大度ならTrue
    """
    return fil in HIGH_SEVERITY_FILS


def is_high_severity_fil_hierarchy(hierarchy: FILHierarchy) -> bool:
    """
    FIL階層が高重大度（Hard Violation対象）か判定
    Check if FIL hierarchy is high severity (Hard Violation candidate)
    
    Args:
        hierarchy: FIL階層
    
    Returns:
        高重大度ならTrue
    """
    return hierarchy in HIGH_SEVERITY_FIL_HIERARCHY


def format_fil_violation(violation: FILViolation) -> str:
    """
    FIL違反を人間可読形式にフォーマット
    Format FIL violation for human readability
    
    Args:
        violation: FIL違反情報
    
    Returns:
        フォーマット済み文字列
    """
    lines = [
        f"FIL Violation: {violation.directive.value}",
        f"  Severity: {violation.severity:.2f}",
        f"  Reason: {violation.reason}",
        f"  Hard Violation: {'Yes' if violation.is_hard_violation else 'No'}",
    ]
    
    if violation.sub_directives:
        sub_list = ", ".join([h.name for h in violation.sub_directives])
        lines.append(f"  Sub-directives: {sub_list}")
    
    return "\n".join(lines)


def sign_fil(values: List[str]) -> Tuple[bytes, bytes]:
    """Sign FIL values with a hash-based PoC "signature".

    FIL の値を連結してハッシュを取り、PoC 用の「署名」として利用する。
    実運用では Ed25519 等に置き換えることを想定。

    Returns:
        blob: concatenated UTF-8 bytes of FIL values
        signature: SHA256 hash of the blob
    """
    blob = "\n".join(values).encode("utf-8")
    signature = hashlib.sha256(blob).digest()
    return blob, signature


def verify_fil_hash(blob: bytes, signature: bytes) -> bool:
    """Verify FIL integrity using hash-based signature.

    ハッシュベース署名を用いて FIL の改変がないか検証する。
    """
    expected = hashlib.sha256(blob).digest()
    return expected == signature


# モジュールロード時に現在の FIL を署名する
# Sign current FIL at import time (PoC behavior)
fil_blob, fil_signature = sign_fil(FIL_VALUES)
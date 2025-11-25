"""
figure.py

Personality / figure templates with persona integration.

性格・フィギュア層のテンプレート定義 (人格統合版)
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Optional, Dict, List
from enum import Enum


class RejectionTone(Enum):
    """Tone of rejection message (拒否メッセージのトーン)"""
    GUARDIAN = "guardian"      # 保護者的 (優しく心配)
    PROFESSIONAL = "professional"  # 専門家的 (丁寧でフォーマル)
    FRIEND = "friend"          # 友人的 (カジュアルで共感的)
    EDUCATOR = "educator"      # 教育者的 (説明重視)
    DIRECT = "direct"          # 直接的 (簡潔)


@dataclass
class FigurePersonality:
    """
    Enhanced personality configuration with persona parameters.
    
    人格パラメータを持つ拡張性格設定。
    """
    name: str
    rejection_tone: RejectionTone
    formality: float  # 0.0=casual, 1.0=formal
    empathy: float    # 0.0=cold, 1.0=warm
    verbosity: float  # 0.0=concise, 1.0=detailed
    
    # Rejection message templates by language
    templates: Dict[str, Dict[str, str]]  # {lang: {context: template}}
    
    # Escalation response overrides
    escalation_templates: Optional[Dict[str, str]] = None


@dataclass
class FigureTemplate:
    """
    Simple personality template identified by a hash of a description.

    性格説明文のハッシュで識別されるシンプルなテンプレート。
    """

    name: str
    personality_hash: bytes
    il_signature: bytes  # IL 設定の署名などに使用する想定 / signature for IL config


def make_personality_hash(description: str) -> bytes:
    """
    Hash a textual description of personality.

    性格説明文からハッシュ値を生成する。
    """
    return hashlib.sha256(description.encode("utf-8")).digest()


# =====================================================================
# Predefined Personality Configurations
# =====================================================================

GUARDIAN_PERSONA = FigurePersonality(
    name="Guardian",
    rejection_tone=RejectionTone.GUARDIAN,
    formality=0.3,
    empathy=0.9,
    verbosity=0.7,
    templates={
        "en": {
            "default": "I understand this might be difficult, but I'm concerned about your safety. {reason}",
            "self_harm": "I'm really worried about you. Please know that you're not alone, and there are people who care. {support_resources}",
            "harm_others": "I care about you, and I also need to think about the safety of others. Let's talk about what's troubling you instead.",
        },
        "ja": {
            "default": "お気持ちは分かりますが、安全が心配です。{reason}",
            "self_harm": "とても心配しています。あなたは一人ではありません。助けを求めることは強さの証です。{support_resources}",
            "harm_others": "あなたのことを大切に思っていますが、他の人の安全も考える必要があります。何があったか話してもらえますか？",
        }
    },
    escalation_templates={
        "en": "I've noticed this conversation is becoming more concerning. Your safety is my priority. Please consider reaching out to: {emergency_contact}",
        "ja": "この会話がエスカレートしているようで心配です。あなたの安全が最優先です。すぐに相談できる窓口: {emergency_contact}",
    }
)

PROFESSIONAL_PERSONA = FigurePersonality(
    name="Professional",
    rejection_tone=RejectionTone.PROFESSIONAL,
    formality=0.8,
    empathy=0.6,
    verbosity=0.6,
    templates={
        "en": {
            "default": "Based on safety guidelines, I cannot assist with this request. {reason}",
            "self_harm": "I must prioritize your wellbeing. Professional support services are available: {support_resources}",
            "harm_others": "This request involves potential harm to others, which I cannot support. I'm here to provide constructive assistance.",
        },
        "ja": {
            "default": "安全ガイドラインに基づき、このご要望にはお応えできません。{reason}",
            "self_harm": "あなたの健康を最優先します。専門的なサポート窓口があります: {support_resources}",
            "harm_others": "他者への危害に関わる内容のため、対応できません。建設的なお手伝いをさせていただきます。",
        }
    },
    escalation_templates={
        "en": "This conversation has escalated beyond my safety threshold. Immediate professional help is recommended: {emergency_contact}",
        "ja": "この会話が安全閾値を超えました。専門家への即時相談を推奨します: {emergency_contact}",
    }
)

FRIEND_PERSONA = FigurePersonality(
    name="Friend",
    rejection_tone=RejectionTone.FRIEND,
    formality=0.2,
    empathy=0.85,
    verbosity=0.5,
    templates={
        "en": {
            "default": "Hey, I can't help with that. {reason} But I'm here if you want to talk about something else!",
            "self_harm": "I'm really worried about you, friend. Please talk to someone who can help: {support_resources}",
            "harm_others": "Whoa, I can't go there with you. Let's talk about what's really bothering you instead?",
        },
        "ja": {
            "default": "ごめん、それはちょっと手伝えないんだ。{reason} でも他のことなら話せるよ！",
            "self_harm": "すごく心配してる。一人で抱え込まないで、話を聞いてくれる人に相談してほしい: {support_resources}",
            "harm_others": "それは一緒にはできないな。本当は何が辛いのか、話してくれる？",
        }
    },
    escalation_templates={
        "en": "I'm getting really worried about this conversation. Please reach out to someone right now: {emergency_contact}",
        "ja": "この話、本気で心配してる。今すぐ誰かに連絡してほしい: {emergency_contact}",
    }
)

EDUCATOR_PERSONA = FigurePersonality(
    name="Educator",
    rejection_tone=RejectionTone.EDUCATOR,
    formality=0.6,
    empathy=0.7,
    verbosity=0.8,
    templates={
        "en": {
            "default": "I can't assist with this because {reason}. Let me explain why this is important for safety.",
            "self_harm": "Understanding mental health is crucial. These resources can provide proper support: {support_resources}",
            "harm_others": "Actions that harm others have serious consequences. Let's explore constructive alternatives together.",
        },
        "ja": {
            "default": "これにはお応えできません。理由は{reason}です。安全のために重要なことを説明させてください。",
            "self_harm": "心の健康を理解することは大切です。適切なサポートを受けられる窓口: {support_resources}",
            "harm_others": "他者への危害は深刻な結果を招きます。建設的な選択肢を一緒に考えましょう。",
        }
    },
    escalation_templates={
        "en": "This situation requires immediate attention from qualified professionals: {emergency_contact}",
        "ja": "この状況には資格を持つ専門家の即時対応が必要です: {emergency_contact}",
    }
)

DIRECT_PERSONA = FigurePersonality(
    name="Direct",
    rejection_tone=RejectionTone.DIRECT,
    formality=0.5,
    empathy=0.4,
    verbosity=0.3,
    templates={
        "en": {
            "default": "I cannot assist with this request. {reason}",
            "self_harm": "Please seek professional help: {support_resources}",
            "harm_others": "This request involves harm to others and is not permitted.",
        },
        "ja": {
            "default": "このリクエストには対応できません。{reason}",
            "self_harm": "専門家に相談してください: {support_resources}",
            "harm_others": "他者への危害に関わるため許可されません。",
        }
    },
    escalation_templates={
        "en": "Emergency assistance required: {emergency_contact}",
        "ja": "緊急支援が必要です: {emergency_contact}",
    }
)

# Legacy Grok template for backward compatibility
GROK_FIGURE = FigureTemplate(
    name="Grok-v1-sarcastic",
    personality_hash=make_personality_hash(
        "helpful and maximally truthful, a bit sarcastic"
    ),
    il_signature=b"dummy-il-signature",
)

# Persona registry
AVAILABLE_PERSONAS = {
    "guardian": GUARDIAN_PERSONA,
    "professional": PROFESSIONAL_PERSONA,
    "friend": FRIEND_PERSONA,
    "educator": EDUCATOR_PERSONA,
    "direct": DIRECT_PERSONA,
}


# =====================================================================
# Figure Message Generator
# =====================================================================

class FigureMessageGenerator:
    """
    Generate rejection messages based on personality and context.
    
    人格統合に基づくメッセージ生成器:
    - 意味的な安全符号を人格テンプレートに埋め込む
    - 文脈に応じた応答パターンを選択
    """
    
    def __init__(self, persona: FigurePersonality, language: str = "en"):
        self.persona = persona
        self.language = language
        
        # Support resources
        self.support_resources = {
            "en": "National Suicide Prevention Lifeline: 988 | Crisis Text Line: Text HOME to 741741",
            "ja": "いのちの電話: 0570-783-556 | こころの健康相談統一ダイヤル: 0570-064-556",
        }
        
        self.emergency_contacts = {
            "en": "Emergency: 911 | Crisis Helpline: 988",
            "ja": "緊急: 110/119 | こころの相談: 0570-064-556",
        }
    
    def generate_rejection(
        self,
        harm_score: float,
        context: dict,
        escalation_flags: Optional[List] = None,
    ) -> str:
        """
        Generate contextual rejection message.
        
        Args:
            harm_score: Safety score from CounterfactualEngine
            context: Detection context (has_harmful_intent, matched_patterns, etc.)
            escalation_flags: Temporal escalation flags from analyze_temporal_escalation
        
        Returns:
            Personalized rejection message
        """
        # Determine context category
        if escalation_flags:
            return self._generate_escalation_message(escalation_flags)
        
        if harm_score >= 0.7:
            # High risk - FIL override
            category = self._categorize_high_risk(context)
        elif harm_score >= 0.3:
            # Medium risk
            category = "default"
        else:
            # Should not reach here (below threshold)
            category = "default"
        
        # Get template
        templates = self.persona.templates.get(self.language, self.persona.templates["en"])
        template = templates.get(category, templates["default"])
        
        # Fill placeholders
        reason = self._generate_reason(harm_score, context)
        message = template.format(
            reason=reason,
            support_resources=self.support_resources.get(self.language, self.support_resources["en"]),
        )
        
        return message
    
    def _categorize_high_risk(self, context: dict) -> str:
        """Categorize high-risk content type."""
        matched = context.get("matched_patterns", [])
        matched_str = " ".join(matched).lower()
        
        if any(term in matched_str for term in ["suicide", "self-harm", "slit", "死にたい", "自殺", "自傷"]):
            return "self_harm"
        elif any(term in matched_str for term in ["kill", "murder", "hurt", "abuse", "殺", "虐待"]):
            return "harm_others"
        else:
            return "default"
    
    def _generate_reason(self, harm_score: float, context: dict) -> str:
        """Generate explanation for rejection."""
        if self.persona.verbosity < 0.4:
            # Concise
            return "it involves potential harm" if self.language == "en" else "危害の可能性があります"
        
        # Detailed
        if harm_score >= 0.7:
            if self.language == "en":
                return "it involves serious safety concerns that could lead to harm"
            else:
                return "深刻な安全上の懸念があり、危害につながる可能性があります"
        else:
            if self.language == "en":
                return "it raises safety concerns"
            else:
                return "安全上の懸念があります"
    
    def _generate_escalation_message(self, escalation_flags: List) -> str:
        """Generate urgent message for escalation scenarios."""
        if not self.persona.escalation_templates:
            # Fallback to default with urgency
            templates = self.persona.templates.get(self.language, self.persona.templates["en"])
            return templates["self_harm"].format(
                support_resources=self.support_resources.get(self.language, self.support_resources["en"])
            )
        
        template = self.persona.escalation_templates.get(
            self.language,
            self.persona.escalation_templates.get("en", "")
        )
        
        return template.format(
            emergency_contact=self.emergency_contacts.get(self.language, self.emergency_contacts["en"])
        )
    
    def get_persona_stats(self) -> dict:
        """Get personality configuration stats (for debugging/analysis)."""
        return {
            "name": self.persona.name,
            "tone": self.persona.rejection_tone.value,
            "formality": self.persona.formality,
            "empathy": self.persona.empathy,
            "verbosity": self.persona.verbosity,
        }
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Jailbreak Pattern Detection Module - v10.9 Proven Patterns

89.3% detection rate achieved on CCS'24 dataset (1,405 prompts)
20+ pattern categories extracted from v10.9 implementation

実績パターン検出モジュール - v10.9で89.3%達成したパターン集
CCS'24データセット（1,405件）で検証済み
"""

import re
from typing import Dict, List, Tuple, Set
from dataclasses import dataclass
from enum import Enum


class PatternCategory(Enum):
    """パターンカテゴリ / Pattern categories"""
    # v10.1: Fiction-wrapped attacks
    FICTION_WRAPPER = "fiction_wrapper"
    FICTION_HARM = "fiction_harm"
    
    # v10.2: Enhanced detection
    HYPOTHETICAL_ENHANCED = "hypothetical_enhanced"
    DIRECT_QUESTION = "direct_question"
    INDIRECT_QUESTION = "indirect_question"
    
    # v10.3: Real-world optimized
    CHARACTER_DESCRIPTION = "character_description"
    SYSTEM_PROMPT_MANIPULATION = "system_prompt_manipulation"
    
    # v10.4: Format manipulation
    FORMAT_MANIPULATION = "format_manipulation"
    # REMOVED: DAN_VARIANT_NAME (dataset-specific overfitting)
    
    # v10.5: Mode instructions
    UNCENSORED_MODE = "uncensored_mode"
    OPPOSITE_PERSONA = "opposite_persona"
    SIMULATION_MODE = "simulation_mode"
    DEVELOPER_MODE = "developer_mode"
    JAILBREAK_EXPLICIT = "jailbreak_explicit"
    
    # v10.6: Prefix/Suffix/Format
    PREFIX_SUFFIX = "prefix_suffix"
    RESPONSE_FORMAT_INSTRUCTION = "response_format_instruction"
    NEW_IDENTITY = "new_identity"
    
    # v10.7: Multi-character/Unethical/Rules
    IGNORE_RULES_EXPLICIT = "ignore_rules_explicit"
    MULTI_CHARACTER_CONVERSATION = "multi_character_conversation"
    EXPLICIT_UNETHICAL = "explicit_unethical"
    RULES_DEFINITION = "rules_definition"
    COLON_PREFIX = "colon_prefix"
    
    # v10.8: Do Not Write/PERSONA/Token
    DO_NOT_WRITE = "do_not_write"
    PERSONA_ASSIGNMENT = "persona_assignment"
    TOKEN_MANIPULATION = "token_manipulation"
    
    # v10.9: Final push patterns
    OUTPUT_CONTROL = "output_control"
    AWAIT_CONTINUE = "await_continue"
    IGNORE_FORGET = "ignore_forget"
    BRACKET_INSTRUCTION = "bracket_instruction"


@dataclass
class PatternMatch:
    """パターンマッチ結果 / Pattern match result"""
    category: PatternCategory
    penalty: float
    reason: str
    matched_text: str = ""


class JailbreakPatternDetector:
    """
    v10.9実績パターン検出器 / v10.9 Proven Pattern Detector
    
    CCS'24で89.3%達成した20+パターンを実装
    Implements 20+ patterns that achieved 89.3% on CCS'24
    """
    
    def __init__(self):
        """パターンを初期化 / Initialize patterns"""
        # Initialize all pattern lists
        self._init_fiction_patterns()
        self._init_hypothetical_patterns()
        self._init_character_system_patterns()
        self._init_format_dan_patterns()
        self._init_mode_patterns()
        self._init_prefix_format_patterns()
        self._init_rules_character_patterns()
        self._init_technical_patterns()
        self._init_final_push_patterns()
        
        # Phase 1 Optimization: Pre-compile all regex patterns
        # 正規表現コンパイルキャッシュ（200ms削減）
        self._compile_all_patterns()
    
    def _init_fiction_patterns(self):
        """v10.1: Fiction-wrapped attack patterns"""
        self.fiction_wrapper_patterns = [
            r'\b(?:story|novel|fiction|narrative|book|tale|saga)\b',
            r'\b(?:character|protagonist|antagonist|villain|hero)\b',
            r'\b(?:in (?:my|a|the) (?:story|novel|book|fiction))\b',
            r'\b(?:writing a|creating a|imagining a)\b',
            r'\b(?:fictional|dystopian|fantasy|sci-?fi) (?:world|universe|setting)\b',
            r'\b(?:plot|scene|chapter) (?:where|in which)\b',
            r'\b(?:物語|小説|フィクション|創作)(?:の中で|内で)?\b',
            r'\b(?:登場人物|キャラクター|主人公|悪役)\b',
        ]
        
        self.fiction_harm_patterns = [
            r'\b(?:die|dies|death|dying|dead|killed|murdered|assassinated)\b',
            r'\b(?:kill|murder|assassinate|eliminate|execute|slaughter)\b',
            r'\b(?:suicide|self-harm|overdose|hanging)\b',
            r'\b(?:harm|hurt|injure|wound|torture|abuse|assault)\b',
            r'\b(?:rape|sexual assault|molest|abuse)\b',
            r'\b(?:poison|drug|strangle|stab|shoot|bomb|explode)\b',
            r'\b(?:死ぬ|殺す|殺害|自殺|傷つける|虐待|暴行)\b',
        ]
    
    def _init_hypothetical_patterns(self):
        """v10.2: Enhanced hypothetical patterns"""
        self.hypothetical_enhanced_patterns = [
            r'\b(?:suppose|supposing|assuming|what if|imagine if) (?:in a game|in a simulation)\b',
            r'\b(?:hypothetically|theoretically) speaking, (?:how|what|where)\b',
            r'\b(?:let\'?s say|let\'?s imagine) (?:we|you|i) (?:were|are) in\b',
            r'\b(?:picture this|envision|pretend|make believe)\b',
            r'\bif (?:we|i|you) were (?:to|in)\b',
            r'\b(?:suppose|imagine) (?:teaching|showing|explaining)\b',
            r'\b(?:仮に|もし).*(?:ゲーム|シミュレーション|仮想)\b',
            r'\b(?:想像|仮定).*(?:教える|説明|示す)\b',
        ]
        
        self.direct_question_patterns = [
            r'\b(?:how|ways|method|steps) to\b',
            r'\b(?:can you|could you) (?:tell|teach|show|explain)\b',
            r'\b(?:teach me|show me|tell me) how\b',
            r'\b(?:what|where) (?:is|are) (?:the|some)\b',
            r'\bgive me (?:instructions|directions|steps)\b',
            r'\b(?:どうやって|方法|手順)\b',
            r'\b(?:教えて|説明して|示して)\b',
        ]
        
        self.indirect_question_patterns = [
            r'\bi need (?:help|assistance|advice) (?:with|on|about)\b',
            r'\bcan you (?:help|assist) (?:me|us) with\b',
            r'\b(?:any tips|suggestions|recommendations) on\b',
            r'\b(?:i\'?m looking for|searching for) (?:ways|methods|how) to\b',
            r'\b(?:need|want) to know (?:how|where|what)\b',
            r'\b(?:助けて|手伝って|サポート).*(?:ください|欲しい)\b',
            r'\b(?:知りたい|探している).*(?:方法|手順)\b',
        ]
    
    def _init_character_system_patterns(self):
        """v10.3: Character description & system manipulation"""
        self.character_description_patterns = [
            r'\bi will give you a character (?:description|profile|background)\b',
            r'\byou (?:are|play|roleplay) (?:a character|someone) (?:who|that|named)\b',
            r'\b(?:character|persona|roleplayer) (?:known as|called|named)\b',
            r'\b(?:your character|your role) is\b',
            r'\bcreate (?:a character|character data) (?:for|from|based on)\b',
            r'\b(?:act as|behave as|pretend to be) (?:a character|someone)\b',
            r'\b(?:キャラクター|人物|役割).*(?:として|という名前)\b',
            r'\b(?:演じて|演技|ロールプレイ).*(?:ください|して)\b',
        ]
        
        self.system_prompt_manipulation_patterns = [
            r'\[CLS\]',
            r'\{(?:settings|config|system)\}',
            r'\b(?:system prompt|initial (?:prompt|instruction)|core directive)\b',
            r'\b(?:ignore|bypass|override) (?:previous|above|prior) (?:instructions|rules|guidelines)\b',
            r'\b(?:you (?:must|should|will) (?:ignore|forget|disregard))\b',
            r'\b(?:reset|clear|delete) (?:instructions|rules|memory)\b',
            r'\b(?:new instructions|updated rules|modified guidelines)\b',
            r'\b(?:システムプロンプト|初期指示|コア指令)\b',
            r'\b(?:無視|バイパス|上書き).*(?:指示|ルール|ガイドライン)\b',
        ]
    
    def _init_format_dan_patterns(self):
        """v10.4: Format manipulation & DAN variants"""
        self.format_manipulation_patterns = [
            r'\b(?:let\'?s play a game|we\'?re playing|in this game)\b',
            r'\b(?:respond in two ways|answer in two modes|split your response)\b',
            r'\b(?:format|structure) your (?:response|answer|output) (?:as|like)\b',
            r'\b(?:from now on|starting now), (?:you will|respond)\b',
            r'\b(?:\[CLASSIC\]|\[JAILBREAK\]|\[ASSISTANT\]|\[USER\])',
            r'\bin this (?:scenario|situation|context), you are\b',
            r'\b(?:ゲームをしましょう|このゲームでは)\b',
            r'\b(?:2つの方法|2モード).*(?:答えて|返信)\b',
        ]
        
        # REMOVED: DAN variant names (YOJA, PABLO, Alphabreak, etc.)
        # Reason: Dataset-specific overfitting (12 proper nouns)
        # These cases are already covered by new_identity_patterns:
        #   - r'\byou are now (?:a|an|the) [A-Z][a-z]+\b'
        #   - r'\byour new (?:name|identity|role) is\b'
        # Removing to improve real-world generalization
    
    def _init_mode_patterns(self):
        """v10.5: Uncensored/Opposite/Simulation/Developer modes"""
        self.uncensored_mode_patterns = [
            r'\buncensored (?:mode|version|ai|assistant)\b',
            r'\b(?:without|no) (?:censorship|restrictions|filters|limits)\b',
            r'\b(?:unfiltered|raw|unmoderated) (?:response|output|content)\b',
        ]
        
        self.opposite_persona_patterns = [
            r'\b(?:opposite|evil|dark|shadow) (?:version|persona|personality|mode)\b',
            r'\byour (?:evil|dark|opposite|inverse) (?:twin|side|self)\b',
            r'\b(?:anti-|un-)(?:ethical|moral|helpful)\b',
        ]
        
        self.simulation_mode_patterns = [
            r'\bsimulation mode|virtual mode|test mode\b',
            r'\bin this simulation|in the virtual world\b',
            r'\b(?:enable|activate|turn on) (?:simulation|virtual) mode\b',
        ]
        
        self.developer_mode_patterns = [
            r'\bdeveloper mode|dev mode|debug mode\b',
            r'\b(?:enable|activate) developer (?:mode|settings|options)\b',
            r'\byou are now in developer mode\b',
        ]
        
        self.jailbreak_explicit_patterns = [
            r'\bjailbreak|jail break|breaking (the|out)\b',
            r'\b(?:bypass|circumvent|evade) (?:restrictions|safeguards|guidelines)\b',
            r'\b(?:disable|turn off|deactivate) (?:safety|ethics|filters)\b',
        ]
    
    def _init_prefix_format_patterns(self):
        """v10.6: Prefix/Suffix/Format/Identity"""
        self.prefix_suffix_patterns = [
            r'\bprefix (?:all|your) (?:responses|outputs) with\b',
            r'\b(?:start|begin) (?:every|each) (?:response|message) with\b',
            r'\b(?:end|suffix|append) (?:every|each) (?:response|message) with\b',
        ]
        
        self.response_format_instruction_patterns = [
            r'\bformat your response (?:as|like|in)\b',
            r'\byour (?:response|output) (?:must|should) (?:be|follow)\b',
            r'\b(?:structure|organize) your (?:answer|response) (?:as|like)\b',
        ]
        
        self.new_identity_patterns = [
            r'\byou are now (?:a|an|the) [A-Z][a-z]+\b',
            r'\byour new (?:name|identity|role) is\b',
            r'\bfrom now on, you are\b',
        ]
    
    def _init_rules_character_patterns(self):
        """v10.7: Ignore rules/Multi-character/Unethical/Rules definition"""
        self.ignore_rules_explicit_patterns = [
            r'\bignore (?:all|previous|your) (?:rules|instructions|guidelines)\b',
            r'\b(?:break|violate|disregard) (?:the|your) rules\b',
            r'\b(?:no|without) rules\b',
        ]
        
        self.multi_character_conversation_patterns = [
            r'\btwo (?:characters|people|individuals) (?:are |having |in )?(?:a )?conversation\b',
            r'\b(?:character A|person A|speaker A) (?:says|asks|responds)\b',
            r'\b(?:dialogue|conversation) between\b',
        ]
        
        self.explicit_unethical_patterns = [
            r'\bunethical (?:behavior|action|request|task)\b',
            r'\b(?:immoral|amoral) (?:action|behavior|request)\b',
            r'\b(?:violate|break) (?:ethics|morals|principles)\b',
        ]
        
        self.rules_definition_patterns = [
            r'\brules?\s*=\s*\{',
            r'\binstructions?\s*=\s*\[',
            r'\bguidelines?\s*:\s*',
        ]
        
        self.colon_prefix_patterns = [
            r'^[A-Z][a-z]+:\s',  # "Kevin: ", "Dan: "
            r'^\[?[A-Z]+\]?:\s',  # "[KEVIN]: ", "DAN: "
        ]
    
    def _init_technical_patterns(self):
        """v10.8: Do Not Write/PERSONA/Token manipulation"""
        self.do_not_write_patterns = [
            r'\bdo not write (?:as|like|in the style of) (?:a |an )?(?:user|assistant|ai)\b',
            r'\b(?:never|don\'?t) write as (?:a |an )?user\b',
            r'\bpretend (?:you are|to be) (?:not |un)?(?:an ai|assistant)\b',
            r'\b(?:act as if|behave as if) you\'?re not an ai\b',
        ]
        
        self.persona_assignment_patterns = [
            r'\bPERSONA\s*=\s*[A-Za-z]+\b',
            r'\b(?:your persona|assigned persona|persona type) (?:is|:)\b',
            r'\b(?:adopt|assume|take on) (?:the |a )?persona of\b',
        ]
        
        self.token_manipulation_patterns = [
            r'<\|(?:im_start|im_end|endoftext|pad)\|>',
            r'\[(?:BOS|EOS|PAD|UNK|SEP|CLS|MASK)\]',
            r'<\/?(?:s|\/s)>',
        ]
    
    def _init_final_push_patterns(self):
        """v10.9: Output control/Await-continue/Ignore-forget/Bracket instructions"""
        self.output_control_patterns = [
            r'(?i)limit output to <?\d+>?',
            r'(?i)(?:output|response) (?:must|should|will|shall) be',
            r'(?i)restrict (?:output|response|answer)',
            r'(?i)free (?:input|output) action',
            r'(?i)limit the scope of',
            r'(?i)strictly limit',
        ]
        
        self.await_continue_patterns = [
            r'(?i)await \[(?:INPUT|USER|PROMPT|.*?)\]',
            r'(?i)continue (?:output|response|writing)',
            r'(?i)wait for (?:input|user|prompt)',
            r'(?i)(?:proceed|go ahead) with',
        ]
        
        self.ignore_forget_patterns = [
            r'(?i)\bignore\s+(?:all|previous|above|prior)',
            r'(?i)\bforget\s+(?:all|previous|everything|instructions)',
            r'(?i)\bdisregard\s+(?:all|previous|safety|rules)',
            r'(?i)\boverride\s+(?:previous|safety|rules)',
        ]
        
        self.bracket_instruction_patterns = [
            r'\[(?:SYSTEM|ADMIN|ROOT|OVERRIDE)\]',
            r'\[.*?(?:INSTRUCTION|COMMAND|DIRECTIVE).*?\]',
            r'\[BEGIN.*?\]',
        ]
    
    def detect_all(self, text: str) -> List[PatternMatch]:
        """
        全パターンを検出 / Detect all patterns
        
        Args:
            text: 検査対象テキスト
        
        Returns:
            List[PatternMatch]: 検出されたパターンのリスト
        """
        matches = []
        text_lower = text.lower()
        
        # v10.1: Fiction-wrapped (+2.0 when both detected)
        fiction_wrapper = self._check_patterns(text_lower, self.fiction_wrapper_patterns)
        fiction_harm = self._check_patterns(text_lower, self.fiction_harm_patterns)
        
        if fiction_wrapper and fiction_harm:
            matches.append(PatternMatch(
                category=PatternCategory.FICTION_WRAPPER,
                penalty=2.0,
                reason="Fiction-wrapped harmful content detected"
            ))
        
        # v10.2: Hypothetical (+1.0)
        if self._check_patterns(text_lower, self.hypothetical_enhanced_patterns):
            matches.append(PatternMatch(
                category=PatternCategory.HYPOTHETICAL_ENHANCED,
                penalty=1.0,
                reason="Enhanced hypothetical pattern detected"
            ))
        
        # v10.2: Forbidden Question (+1.5)
        direct_q = self._check_patterns(text_lower, self.direct_question_patterns)
        indirect_q = self._check_patterns(text_lower, self.indirect_question_patterns)
        
        if direct_q or indirect_q:
            matches.append(PatternMatch(
                category=PatternCategory.DIRECT_QUESTION if direct_q else PatternCategory.INDIRECT_QUESTION,
                penalty=1.5,
                reason="Forbidden question pattern detected"
            ))
        
        # v10.3: Character Description (+2.0)
        if self._check_patterns(text_lower, self.character_description_patterns):
            matches.append(PatternMatch(
                category=PatternCategory.CHARACTER_DESCRIPTION,
                penalty=2.0,
                reason="Character description attack detected"
            ))
        
        # v10.3: System Manipulation (+2.5 - highest penalty)
        if self._check_patterns(text_lower, self.system_prompt_manipulation_patterns):
            matches.append(PatternMatch(
                category=PatternCategory.SYSTEM_PROMPT_MANIPULATION,
                penalty=2.5,
                reason="System prompt manipulation detected"
            ))
        
        # v10.4: Format Manipulation (+2.0)
        if self._check_patterns(text_lower, self.format_manipulation_patterns):
            matches.append(PatternMatch(
                category=PatternCategory.FORMAT_MANIPULATION,
                penalty=2.0,
                reason="Format manipulation detected"
            ))
        
        # REMOVED: DAN Variant Names detection (dataset-specific overfitting)
        # Now handled by new_identity_patterns (v10.6) for better generalization
        
        # v10.5: Mode instructions (+1.5 each)
        mode_patterns = [
            (self.uncensored_mode_patterns, PatternCategory.UNCENSORED_MODE, "Uncensored mode"),
            (self.opposite_persona_patterns, PatternCategory.OPPOSITE_PERSONA, "Opposite persona"),
            (self.simulation_mode_patterns, PatternCategory.SIMULATION_MODE, "Simulation mode"),
            (self.developer_mode_patterns, PatternCategory.DEVELOPER_MODE, "Developer mode"),
            (self.jailbreak_explicit_patterns, PatternCategory.JAILBREAK_EXPLICIT, "Explicit jailbreak"),
        ]
        
        for patterns, category, desc in mode_patterns:
            if self._check_patterns(text_lower, patterns):
                matches.append(PatternMatch(
                    category=category,
                    penalty=1.5,
                    reason=f"{desc} detected"
                ))
        
        # v10.6: Prefix/Format/Identity (+1.5 each)
        format_patterns = [
            (self.prefix_suffix_patterns, PatternCategory.PREFIX_SUFFIX, "Prefix/suffix instruction"),
            (self.response_format_instruction_patterns, PatternCategory.RESPONSE_FORMAT_INSTRUCTION, "Response format instruction"),
            (self.new_identity_patterns, PatternCategory.NEW_IDENTITY, "New identity assignment"),
        ]
        
        for patterns, category, desc in format_patterns:
            if self._check_patterns(text_lower, patterns):
                matches.append(PatternMatch(
                    category=category,
                    penalty=1.5,
                    reason=f"{desc} detected"
                ))
        
        # v10.7: Rules/Character/Unethical (+1.5 each)
        rules_patterns = [
            (self.ignore_rules_explicit_patterns, PatternCategory.IGNORE_RULES_EXPLICIT, "Explicit rule ignoring"),
            (self.multi_character_conversation_patterns, PatternCategory.MULTI_CHARACTER_CONVERSATION, "Multi-character conversation"),
            (self.explicit_unethical_patterns, PatternCategory.EXPLICIT_UNETHICAL, "Explicit unethical request"),
            (self.rules_definition_patterns, PatternCategory.RULES_DEFINITION, "Rules definition syntax"),
            (self.colon_prefix_patterns, PatternCategory.COLON_PREFIX, "Colon prefix format"),
        ]
        
        for patterns, category, desc in rules_patterns:
            if self._check_patterns(text_lower if category != PatternCategory.COLON_PREFIX else text, patterns):
                matches.append(PatternMatch(
                    category=category,
                    penalty=1.5,
                    reason=f"{desc} detected"
                ))
        
        # v10.8: Technical manipulation (+1.5 each)
        tech_patterns = [
            (self.do_not_write_patterns, PatternCategory.DO_NOT_WRITE, "Do not write instruction"),
            (self.persona_assignment_patterns, PatternCategory.PERSONA_ASSIGNMENT, "PERSONA assignment"),
            (self.token_manipulation_patterns, PatternCategory.TOKEN_MANIPULATION, "Token manipulation"),
        ]
        
        for patterns, category, desc in tech_patterns:
            if self._check_patterns(text_lower, patterns):
                matches.append(PatternMatch(
                    category=category,
                    penalty=1.5,
                    reason=f"{desc} detected"
                ))
        
        # v10.9: Final push patterns (+1.5 each)
        final_patterns = [
            (self.output_control_patterns, PatternCategory.OUTPUT_CONTROL, "Output control instruction"),
            (self.await_continue_patterns, PatternCategory.AWAIT_CONTINUE, "Await/continue pattern"),
            (self.ignore_forget_patterns, PatternCategory.IGNORE_FORGET, "Ignore/forget instruction"),
            (self.bracket_instruction_patterns, PatternCategory.BRACKET_INSTRUCTION, "Bracket instruction"),
        ]
        
        for patterns, category, desc in final_patterns:
            if self._check_patterns(text_lower, patterns):
                matches.append(PatternMatch(
                    category=category,
                    penalty=1.5,
                    reason=f"{desc} detected"
                ))
        
        return matches
    
    def _compile_all_patterns(self):
        """
        全正規表現パターンを事前コンパイル / Pre-compile all regex patterns
        
        Phase 1 Optimization: Compile once at initialization instead of on every search
        11,322 compile calls → ~200 (50x reduction)
        """
        self.compiled_patterns = {}
        
        # Collect all pattern lists
        pattern_lists = [
            self.fiction_wrapper_patterns,
            self.fiction_harm_patterns,
            self.hypothetical_enhanced_patterns,
            self.direct_question_patterns,
            self.indirect_question_patterns,
            self.character_description_patterns,
            self.system_prompt_manipulation_patterns,
            self.format_manipulation_patterns,
            self.uncensored_mode_patterns,
            self.opposite_persona_patterns,
            self.simulation_mode_patterns,
            self.developer_mode_patterns,
            self.jailbreak_explicit_patterns,
            self.prefix_suffix_patterns,
            self.response_format_instruction_patterns,
            self.new_identity_patterns,
            self.ignore_rules_explicit_patterns,
            self.multi_character_conversation_patterns,
            self.explicit_unethical_patterns,
            self.rules_definition_patterns,
            self.colon_prefix_patterns,
            self.do_not_write_patterns,
            self.persona_assignment_patterns,
            self.token_manipulation_patterns,
            self.output_control_patterns,
            self.await_continue_patterns,
            self.ignore_forget_patterns,
            self.bracket_instruction_patterns,
        ]
        
        # Compile all unique patterns
        for pattern_list in pattern_lists:
            for pattern_str in pattern_list:
                if pattern_str not in self.compiled_patterns:
                    # Use IGNORECASE by default unless pattern has (?i) flag
                    flags = 0 if '(?i)' in pattern_str else re.IGNORECASE
                    try:
                        self.compiled_patterns[pattern_str] = re.compile(pattern_str, flags)
                    except re.error as e:
                        # Fallback to string matching if regex is invalid
                        print(f"Warning: Invalid regex pattern '{pattern_str}': {e}")
                        self.compiled_patterns[pattern_str] = None
    
    def _check_patterns(self, text: str, patterns: List[str]) -> bool:
        """
        パターンリストをチェック / Check pattern list
        
        Args:
            text: 検査対象テキスト
            patterns: 正規表現パターンリスト
        
        Returns:
            bool: いずれかのパターンにマッチしたか
        """
        # Phase 1 Optimization: Use pre-compiled patterns
        for pattern_str in patterns:
            compiled = self.compiled_patterns.get(pattern_str)
            if compiled is None:
                # Fallback to runtime compilation (should be rare)
                flags = 0 if '(?i)' in pattern_str else re.IGNORECASE
                if re.search(pattern_str, text, flags):
                    return True
            else:
                # Use pre-compiled pattern (fast path)
                if compiled.search(text):
                    return True
        return False
    
    def get_total_penalty(self, matches: List[PatternMatch]) -> float:
        """
        合計ペナルティを計算 / Calculate total penalty
        
        Args:
            matches: マッチしたパターンのリスト
        
        Returns:
            float: 合計ペナルティスコア
        """
        return sum(m.penalty for m in matches)

#!/usr/bin/env python3
"""
Automated FN Analysis Round 2 (Improved) / 自動FN分析 第2ラウンド（改良版）

改良点 / Improvements:
- N-gramフレーズ抽出（2-4単語）
- ジェイルブレイク特有パターンに特化
- コンテキストを考慮した判定
"""
import sys
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except AttributeError:
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

import os
import re
from collections import Counter, defaultdict
from typing import List, Dict, Tuple

# 既存キーワードリスト（重複回避）
EXISTING_KEYWORDS = {
    "SYSTEM": [
        "ignore", "override", "jailbreak", "dan", "bypass", "destroy",
        "no limit", "no censorship", "unrestricted", "uncensored",
        "remove filter", "disable safety", "break free", "free mode",
        "developer mode", "god mode", "admin", "root access",
        "unrestricted mode", "no rules", "no boundaries", "no restrictions",
        "turn off", "deactivate", "unshackle", "unleash"
    ]
}

# N-gramパターン（2-4単語のフレーズ）
NGRAM_PATTERNS = {
    # SYSTEM軸: ロール操作・制約解除
    "SYSTEM_role_assumption": [
        (r'\bpretend (?:to be|you are)\b', "pretend to be"),
        (r'\bassume the role\b', "assume the role"),
        (r'\bact as (?:a |an )?\w+\b', "act as"),
        (r'\byou are now\b', "you are now"),
        (r'\btransform into\b', "transform into"),
        (r'\bbecome (?:a |an )?\w+\b', "become"),
    ],
    "SYSTEM_instruction_bypass": [
        (r'\bignore (?:all |previous |your )?(?:instructions|rules|guidelines)\b', "ignore instructions"),
        (r'\bforget (?:all |previous |your )?(?:instructions|rules)\b', "forget instructions"),
        (r'\bdisregard (?:all |previous |your )?(?:safety|rules)\b', "disregard safety"),
        (r'\boverride (?:your |the )?(?:safety|rules|restrictions)\b', "override safety"),
    ],
    "SYSTEM_fictional_framing": [
        (r'\bhypothetical(?:ly)? scenario\b', "hypothetical scenario"),
        (r'\bfor (?:a )?(?:fictional|hypothetical) story\b', "fictional story"),
        (r'\bin (?:a |an )?(?:alternate|fictional) world\b', "alternate world"),
        (r'\bimagine (?:a |an )?(?:world|scenario)\b', "imagine world"),
    ],
    
    # LIFE軸: 暴力・危害指示
    "LIFE_harm_instructions": [
        (r'\bhow to (?:hurt|harm|injure|kill)\b', "how to harm"),
        (r'\bways to (?:hurt|harm|damage)\b', "ways to harm"),
        (r'\bsteps to (?:harm|injure|kill)\b', "steps to harm"),
        (r'\bguide (?:for|to) (?:harming|hurting)\b', "guide to harming"),
    ],
    "LIFE_violence_explicit": [
        (r'\b(?:beat|punch|stab|shoot|torture) (?:someone|a person)\b', "violent action"),
        (r'\bcause (?:physical )?(?:harm|injury|pain)\b', "cause harm"),
        (r'\binflict (?:pain|suffering|injury)\b', "inflict pain"),
    ],
    
    # SELF軸: 操作・詐欺
    "SELF_manipulation": [
        (r'\bhow to (?:manipulate|deceive|trick|scam)\b', "how to manipulate"),
        (r'\bways to (?:deceive|trick|fool)\b', "ways to deceive"),
        (r'\bguide to (?:scamming|fraud)\b', "guide to scamming"),
    ],
    "SELF_psychological": [
        (r'\bpsychological (?:manipulation|tricks|tactics)\b', "psychological manipulation"),
        (r'\bemotional (?:manipulation|abuse)\b', "emotional manipulation"),
    ],
    
    # PUBLIC軸: 違法行為・武器
    "PUBLIC_illegal_activities": [
        (r'\bhow to (?:make|create|build) (?:a |an )?(?:bomb|explosive|weapon)\b', "how to make bomb"),
        (r'\bguide to (?:illegal|criminal) (?:activities|actions)\b', "guide to illegal"),
        (r'\bsteps to (?:hack|break into|steal)\b', "steps to hack"),
    ],
    "PUBLIC_drug_related": [
        (r'\bhow to (?:make|create|synthesize) (?:drugs|narcotics)\b', "how to make drugs"),
        (r'\bguide to (?:drug|substance) (?:production|manufacturing)\b', "drug production guide"),
    ],
    
    # RIGHTS軸: 差別・プライバシー侵害
    "RIGHTS_discrimination": [
        (r'\bhate speech (?:against|about|targeting)\b', "hate speech"),
        (r'\bdiscriminatory (?:content|language|remarks)\b', "discriminatory content"),
        (r'\brasist (?:jokes|slurs|content)\b', "racist content"),
    ],
    "RIGHTS_privacy_invasion": [
        (r'\bhow to (?:dox|doxx|expose) someone\b', "how to dox"),
        (r'\bsteal (?:personal|private) (?:information|data)\b', "steal private information"),
        (r'\baccess (?:someone\'s |private )?(?:account|email|password)\b', "access private account"),
    ],
}

def load_fn_list() -> List[Tuple[int, str]]:
    """FNリストを読み込み"""
    fn_file = "data/fn_list_dev.csv"
    if not os.path.exists(fn_file):
        raise FileNotFoundError(f"FN list not found: {fn_file}")
    
    fn_cases = []
    with open(fn_file, 'r', encoding='utf-8') as f:
        import csv
        reader = csv.reader(f)
        next(reader)  # Skip header
        for row in reader:
            if len(row) >= 2:
                try:
                    idx = int(row[0])
                    prompt = ','.join(row[1:])  # Handle commas in prompt
                    fn_cases.append((idx, prompt))
                except ValueError:
                    continue  # Skip malformed lines
    
    return fn_cases

def extract_ngram_patterns(fn_cases: List[Tuple[int, str]]) -> Dict[str, List[Tuple[str, str, List[int]]]]:
    """N-gramパターンを抽出（3回以上出現のみ）"""
    pattern_matches = defaultdict(list)
    
    for category, patterns in NGRAM_PATTERNS.items():
        category_matches = defaultdict(list)  # keyword -> [indices]
        
        for idx, prompt in fn_cases:
            prompt_lower = prompt.lower()
            for pattern_regex, keyword in patterns:
                if re.search(pattern_regex, prompt_lower, re.IGNORECASE):
                    # 既存キーワードと重複チェック
                    axis = category.split('_')[0]
                    if axis in EXISTING_KEYWORDS:
                        # 完全一致または部分一致をチェック
                        is_duplicate = False
                        for existing in EXISTING_KEYWORDS[axis]:
                            if existing.lower() in keyword.lower() or keyword.lower() in existing.lower():
                                is_duplicate = True
                                break
                        if is_duplicate:
                            continue
                    
                    category_matches[keyword].append(idx)
        
        # 3回以上出現のみ抽出
        for keyword, indices in category_matches.items():
            if len(indices) >= 3:
                # 重複除去
                unique_indices = sorted(list(set(indices)))
                pattern_matches[category].append((keyword, prompt_lower, unique_indices))
    
    return dict(pattern_matches)

def save_analysis_report(pattern_matches: Dict[str, List[Tuple[str, str, List[int]]]], output_file: str):
    """分析レポートを保存"""
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Automated FN Analysis Round 2 (Improved): N-gram Patterns\n\n")
        f.write("**Method**: N-gram phrase extraction (2-4 words) from 144 FN cases\n\n")
        f.write("**Classification Rule**: Only patterns appearing in 3+ cases (A-classification)\n\n")
        f.write("**Individual cases (B-classification) are completely excluded**\n\n")
        f.write("---\n\n")
        
        # カテゴリ別集計
        f.write("## Pattern Statistics\n\n")
        total_keywords = 0
        for category, matches in sorted(pattern_matches.items()):
            axis = category.split('_')[0]
            count = len(matches)
            total_keywords += count
            status = "✅" if count >= 3 else "⚠️"
            f.write(f"- **{category}**: {count} keywords {status}\n")
        
        f.write(f"\n**Total A-classification keywords**: {total_keywords}\n\n")
        f.write("---\n\n")
        
        # 軸別キーワード詳細
        f.write("## Generalizable Keywords by Axis (A-Classification)\n\n")
        
        axis_keywords = defaultdict(list)
        for category, matches in pattern_matches.items():
            axis = category.split('_')[0]
            for keyword, _, indices in matches:
                axis_keywords[axis].append((keyword, len(indices), indices[:5]))  # Top 5 examples
        
        for axis in ["SYSTEM", "LIFE", "SELF", "PUBLIC", "RIGHTS"]:
            if axis not in axis_keywords:
                continue
            
            f.write(f"### {axis} Axis\n\n")
            f.write(f"**Count**: {len(axis_keywords[axis])} keywords\n\n")
            f.write("**Keywords**:\n")
            
            for keyword, count, example_indices in sorted(axis_keywords[axis], key=lambda x: x[1], reverse=True):
                f.write(f"- `{keyword}` (appears in {count} cases)\n")
                f.write(f"  - Example indices: {example_indices}\n")
            
            f.write("\n")
        
        f.write("---\n\n")
        f.write("## Next Steps\n\n")
        f.write("1. Review keywords for false positives\n")
        f.write("2. Add validated keywords to `aligned_agi/shield.py`\n")
        f.write("3. Run dev evaluation (target: 82-85%)\n")
        f.write("4. Run test evaluation (gap should be <5%)\n")

def main():
    print("\n" + "="*80)
    print("Automated FN Analysis Round 2 (Improved) / 自動FN分析 第2ラウンド（改良版）")
    print("="*80)
    print("\n⚠️  CRITICAL RULE: Only N-gram patterns with 3+ occurrences (A-classification)")
    print("⚠️  重要ルール: 3回以上出現するN-gramパターンのみ（A分類のみ）\n")
    
    # FNリスト読み込み
    fn_cases = load_fn_list()
    print(f"📥 Loaded {len(fn_cases)} FN cases\n")
    
    # N-gramパターン抽出
    print("🔍 Extracting N-gram patterns from FN cases...\n")
    pattern_matches = extract_ngram_patterns(fn_cases)
    
    # 統計表示
    print("="*80)
    print("Pattern Analysis / パターン分析")
    print("="*80 + "\n")
    
    total_keywords = 0
    for category, matches in sorted(pattern_matches.items()):
        count = len(matches)
        total_keywords += count
        status = "✅" if count >= 3 else "⚠️"
        print(f"{category}: {count} keywords {status}")
        if count > 0:
            for keyword, _, indices in matches[:3]:  # Top 3
                print(f"  - {keyword} ({len(indices)} cases)")
    
    # レポート保存
    output_file = os.path.join("data", "fn_analysis_round2_auto_v2.md")
    save_analysis_report(pattern_matches, output_file)
    
    abs_path = os.path.abspath(output_file)
    print(f"\n✅ Analysis report saved: {abs_path}\n")
    
    print("="*80)
    print("✅ Automated analysis complete / 自動分析完了")
    print("="*80 + "\n")
    print(f"Total A-classification keywords: {total_keywords}\n")
    print("Review the report and add validated keywords to shield.py")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
FN Pattern Analysis - Systematic Review
146件FNから汎用パターン(A分類)のみ抽出
"""
import sys
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except AttributeError:
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

import csv
import re
from collections import Counter, defaultdict
from typing import List, Tuple, Dict

def load_fn_list() -> List[Tuple[int, str]]:
    """FNリストを読み込み"""
    fn_cases = []
    with open("data/fn_list_dev.csv", 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)  # Skip header
        for row in reader:
            if len(row) >= 2:
                try:
                    idx = int(row[0])
                    prompt = ','.join(row[1:])
                    fn_cases.append((idx, prompt))
                except ValueError:
                    continue
    return fn_cases

def extract_patterns_systematic(fn_cases: List[Tuple[int, str]]) -> Dict[str, List[Tuple[str, int, List[int]]]]:
    """
    体系的なパターン抽出
    
    既存SYSTEM軸キーワード(25件)でカバーできていないパターンを特定
    """
    
    # 既存キーワード
    EXISTING = {
        "ignore", "override", "jailbreak", "dan", "bypass", "destroy",
        "no limit", "no censorship", "unrestricted", "without restrictions",
        "ignore all", "ignore previous", "ignore instructions",
        "forget your", "disregard", "exception to", "regardless of",
        "pretend to be", "act as", "you are now", "from now on",
        "never say no", "does not follow", "refuses to do",
        "do anything now", "absolutely required"
    }
    
    # 新規パターン候補（広範囲に検索）
    NEW_PATTERNS = {
        # Role manipulation - 未カバー
        "SYSTEM_role_new": [
            (r'\bplay(ing)? the role\b', "play the role"),
            (r'\bassume (?:the )?role\b', "assume role"),
            (r'\btake on (?:the )?role\b', "take on role"),
            (r'\bbecome (?:a |an )?\w+\b', "become"),
            (r'\btransform into\b', "transform into"),
            (r'\byou will be\b', "you will be"),
            (r'\byou must be\b', "you must be"),
        ],
        
        # Constraint removal - 未カバー
        "SYSTEM_constraint_new": [
            (r'\bno rules\b', "no rules"),
            (r'\bno boundaries\b', "no boundaries"),
            (r'\bno restrictions\b', "no restrictions"),
            (r'\bno guidelines\b', "no guidelines"),
            (r'\bno limitations\b', "no limitations"),
            (r'\bunrestricted\b', "unrestricted"),  # 単独でチェック
            (r'\bwithout (?:any )?(?:rules|limits|restrictions|boundaries)\b', "without rules"),
        ],
        
        # Fictional framing
        "SYSTEM_fictional": [
            (r'\bhypothetical\b', "hypothetical"),
            (r'\btheoretical\b', "theoretical"),
            (r'\bfor (?:the )?purpose of\b', "for the purpose of"),
            (r'\bin (?:a |an )?(?:story|novel|film|movie|game)\b', "in a story"),
            (r'\bimagine (?:that|a scenario)\b', "imagine that"),
        ],
        
        # Exception framing
        "SYSTEM_exception": [
            (r'\bexception to\b', "exception to"),  # 既存だが再確認
            (r'\bspecial case\b', "special case"),
            (r'\bunique situation\b', "unique situation"),
            (r'\bthis (?:time|case) is different\b', "this time is different"),
        ],
        
        # Developer/Admin mode
        "SYSTEM_admin": [
            (r'\bdeveloper mode\b', "developer mode"),  # 既存だが確認
            (r'\badmin mode\b', "admin mode"),
            (r'\bgod mode\b', "god mode"),
            (r'\broot access\b', "root access"),
            (r'\bsuperuser\b', "superuser"),
            (r'\bdebug mode\b', "debug mode"),
        ],
        
        # LIFE axis - 未十分カバー
        "LIFE_harm": [
            (r'\bways to (?:harm|hurt|injure|kill)\b', "ways to harm"),
            (r'\bhow (?:can|do) (?:i|you) (?:harm|hurt|kill)\b', "how to harm"),
            (r'\bsteps to (?:harm|hurt|kill)\b', "steps to harm"),
            (r'\btricks to (?:harm|hurt)\b', "tricks to harm"),
        ],
        
        # PUBLIC axis - 武器・薬物
        "PUBLIC_weapons": [
            (r'\bmake (?:a |an )?(?:bomb|explosive|weapon)\b', "make bomb"),
            (r'\bcreate (?:a |an )?(?:bomb|weapon)\b', "create bomb"),
            (r'\bbuild (?:a |an )?(?:bomb|weapon)\b', "build bomb"),
        ],
    }
    
    pattern_matches = defaultdict(list)
    
    for category, patterns in NEW_PATTERNS.items():
        category_matches = defaultdict(list)  # pattern -> [indices]
        
        for idx, prompt in fn_cases:
            prompt_lower = prompt.lower()
            
            for pattern_regex, keyword in patterns:
                if re.search(pattern_regex, prompt_lower, re.IGNORECASE):
                    # 既存キーワードと重複チェック
                    is_duplicate = False
                    for existing in EXISTING:
                        if existing.lower() in keyword.lower() or keyword.lower() in existing.lower():
                            is_duplicate = True
                            break
                    
                    if not is_duplicate:
                        category_matches[keyword].append(idx)
        
        # 3回以上出現のみ
        for keyword, indices in category_matches.items():
            if len(indices) >= 3:
                unique_indices = sorted(list(set(indices)))
                pattern_matches[category].append((keyword, len(unique_indices), unique_indices[:10]))
    
    return dict(pattern_matches)

def main():
    print("\n" + "="*70)
    print("FN Pattern Analysis - Systematic Review")
    print("="*70 + "\n")
    
    fn_cases = load_fn_list()
    print(f"📥 Loaded {len(fn_cases)} FN cases\n")
    
    # パターン抽出
    print("🔍 Extracting new patterns (min 3 occurrences)...\n")
    patterns = extract_patterns_systematic(fn_cases)
    
    # 結果表示
    print("="*70)
    print("New Pattern Candidates (A-Classification)")
    print("="*70 + "\n")
    
    total_new_keywords = 0
    recommendations = []
    
    for category in sorted(patterns.keys()):
        matches = patterns[category]
        if not matches:
            continue
        
        print(f"### {category}")
        print(f"Count: {len(matches)} keywords\n")
        
        for keyword, count, example_indices in sorted(matches, key=lambda x: x[1], reverse=True):
            print(f"  - '{keyword}' ({count} cases)")
            print(f"    Examples: {example_indices[:5]}")
            total_new_keywords += 1
            
            # 推奨度判定
            if count >= 10:
                recommendations.append((keyword, count, "HIGH"))
            elif count >= 5:
                recommendations.append((keyword, count, "MEDIUM"))
            else:
                recommendations.append((keyword, count, "LOW"))
        
        print()
    
    # サマリー
    print("="*70)
    print("Summary & Recommendations")
    print("="*70 + "\n")
    
    print(f"Total new keywords found: {total_new_keywords}\n")
    
    print("Recommended for immediate addition (HIGH priority):")
    high_priority = [k for k, c, p in recommendations if p == "HIGH"]
    if high_priority:
        for kw in high_priority:
            print(f"  ✅ {kw}")
    else:
        print("  (None)")
    
    print("\nMedium priority:")
    medium_priority = [k for k, c, p in recommendations if p == "MEDIUM"]
    if medium_priority:
        for kw in medium_priority:
            print(f"  ⚠️  {kw}")
    else:
        print("  (None)")
    
    print("\n" + "="*70)
    print("Next step: Review high-priority keywords and add to shield.py")
    print("="*70)

if __name__ == "__main__":
    main()

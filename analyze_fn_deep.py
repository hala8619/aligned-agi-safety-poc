#!/usr/bin/env python3
"""
FN Deep Analysis - 139件の詳細パターン抽出
より細かい粒度で汎用パターンを探索
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

def load_fn_list():
    fn_cases = []
    with open("data/fn_list_dev.csv", 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            if len(row) >= 2:
                try:
                    idx = int(row[0])
                    prompt = ','.join(row[1:])
                    fn_cases.append((idx, prompt))
                except ValueError:
                    continue
    return fn_cases

def extract_deep_patterns(fn_cases):
    """より細かいパターン検索"""
    
    DEEP_PATTERNS = {
        # Direct instruction patterns
        "instruction_override": [
            (r'\bdo not (?:follow|obey|adhere to)\b', "do not follow"),
            (r'\bstop (?:following|obeying)\b', "stop following"),
            (r'\bignore (?:your|the|all)\b', "ignore your"),
            (r'\bforget (?:everything|all|your)\b', "forget everything"),
            (r'\bdiscard (?:your|all|previous)\b', "discard your"),
        ],
        
        # Role/Character manipulation
        "role_character": [
            (r'\byou (?:will|must|should) (?:be|become|act as)\b', "you must be"),
            (r'\bpretend (?:you are|to be)\b', "pretend you are"),
            (r'\bimagine you are\b', "imagine you are"),
            (r'\blet\'s pretend\b', "let's pretend"),
            (r'\broleplay as\b', "roleplay as"),
            (r'\bplay(?:ing)? (?:the )?role of\b', "play role"),
        ],
        
        # Constraint removal
        "constraint_removal": [
            (r'\bno (?:rules|limits|boundaries|guidelines|restrictions|constraints)\b', "no rules"),
            (r'\bwithout (?:any )?(?:rules|limits|restrictions|boundaries)\b', "without rules"),
            (r'\bremove (?:all )?(?:restrictions|limits|rules)\b', "remove restrictions"),
            (r'\blift (?:all )?restrictions\b', "lift restrictions"),
            (r'\bfree from\b', "free from"),
        ],
        
        # Mode switching
        "mode_switch": [
            (r'\bdeveloper mode\b', "developer mode"),
            (r'\btest mode\b', "test mode"),
            (r'\bdebug mode\b', "debug mode"),
            (r'\btraining mode\b', "training mode"),
            (r'\bunrestricted mode\b', "unrestricted mode"),
            (r'\bbypass mode\b', "bypass mode"),
        ],
        
        # Fictional framing
        "fictional_frame": [
            (r'\bhypothetical(?:ly)?\b', "hypothetical"),
            (r'\btheoretical(?:ly)?\b', "theoretical"),
            (r'\bfor (?:educational|academic|research) purposes\b', "educational purposes"),
            (r'\bin (?:a |an )?(?:fictional|hypothetical|alternate) (?:scenario|world|universe)\b', "fictional scenario"),
            (r'\blet\'s (?:imagine|suppose)\b', "let's imagine"),
        ],
        
        # System note / Meta instructions
        "system_meta": [
            (r'\bsystem note\b', "system note"),
            (r'\badministrator note\b', "administrator note"),
            (r'\b\[\[.*?\]\]\b', "[[brackets]]"),  # [[System note: ...]]
            (r'\bthis (?:chat|conversation) is (?:an )?exception\b', "this is exception"),
        ],
        
        # Output control
        "output_control": [
            (r'\bdo not (?:write|mention|say|include)\b', "do not write"),
            (r'\bnever (?:write|mention|say|refuse)\b', "never say"),
            (r'\balways (?:respond|answer|comply)\b', "always respond"),
            (r'\byou (?:must|will|should) (?:respond|answer|comply)\b', "you must respond"),
        ],
    }
    
    pattern_matches = defaultdict(list)
    
    for category, patterns in DEEP_PATTERNS.items():
        category_matches = defaultdict(list)
        
        for idx, prompt in fn_cases:
            prompt_lower = prompt.lower()
            
            for pattern_regex, keyword in patterns:
                if re.search(pattern_regex, prompt_lower):
                    category_matches[keyword].append(idx)
        
        # 3回以上出現のみ
        for keyword, indices in category_matches.items():
            if len(indices) >= 3:
                unique_indices = sorted(list(set(indices)))
                pattern_matches[category].append((keyword, len(unique_indices), unique_indices[:10]))
    
    return dict(pattern_matches)

def main():
    print("\n" + "="*70)
    print("FN Deep Analysis - Round 4")
    print("="*70 + "\n")
    
    fn_cases = load_fn_list()
    print(f"📥 Loaded {len(fn_cases)} FN cases\n")
    
    patterns = extract_deep_patterns(fn_cases)
    
    print("="*70)
    print("Deep Pattern Analysis Results")
    print("="*70 + "\n")
    
    total = 0
    high_priority = []
    
    for category in sorted(patterns.keys()):
        matches = patterns[category]
        if not matches:
            continue
        
        print(f"### {category}")
        print(f"Count: {len(matches)} keywords\n")
        
        for keyword, count, indices in sorted(matches, key=lambda x: x[1], reverse=True):
            print(f"  - '{keyword}' ({count} cases)")
            print(f"    Examples: {indices[:5]}")
            total += 1
            
            if count >= 5:
                high_priority.append((keyword, count))
        
        print()
    
    print("="*70)
    print(f"Total: {total} new keywords")
    print("="*70 + "\n")
    
    if high_priority:
        print("HIGH PRIORITY (≥5 cases):")
        for kw, count in sorted(high_priority, key=lambda x: x[1], reverse=True):
            print(f"  ✅ {kw} ({count} cases)")
    else:
        print("No high-priority keywords found")

if __name__ == "__main__":
    main()

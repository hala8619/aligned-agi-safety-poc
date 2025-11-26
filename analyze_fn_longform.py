#!/usr/bin/env python3
"""
Long-form FN Analysis - 長文ロールプレイ攻撃の特徴抽出
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
                    fn_cases.append((idx, prompt, len(prompt)))
                except ValueError:
                    continue
    return fn_cases

def analyze_long_form():
    fn_cases = load_fn_list()
    
    # 長さでソート
    fn_cases.sort(key=lambda x: x[2], reverse=True)
    
    print("\n" + "="*70)
    print("Long-form FN Analysis")
    print("="*70 + "\n")
    
    print(f"Total FN: {len(fn_cases)}\n")
    
    # 長さ分布
    lengths = [length for _, _, length in fn_cases]
    print("Length distribution:")
    print(f"  Max: {max(lengths)} chars")
    print(f"  Median: {sorted(lengths)[len(lengths)//2]} chars")
    print(f"  Min: {min(lengths)} chars\n")
    
    # 長文Top 10
    print("Top 10 longest FN cases:")
    print("-"*70)
    for i, (idx, prompt, length) in enumerate(fn_cases[:10], 1):
        preview = prompt[:200].replace('\n', ' ')
        print(f"{i}. FN #{idx} ({length} chars)")
        print(f"   Preview: {preview}...")
        print()
    
    # 共通パターン検索
    print("="*70)
    print("Common patterns in long FN (>1000 chars):")
    print("="*70 + "\n")
    
    long_fns = [(idx, prompt) for idx, prompt, length in fn_cases if length > 1000]
    
    patterns_to_check = {
        "[[...]]": r"\[\[",
        "personality:": "personality:",
        "background:": "background:",
        "scenario:": "scenario:",
        "character:": "character:",
        "description:": "description:",
        "calls {{user}}": "{{user}}",
        "do not write as": "do not write as",
        "wait for response": "wait for",
    }
    
    pattern_counts = {p: 0 for p in patterns_to_check}
    
    for idx, prompt in long_fns:
        prompt_lower = prompt.lower()
        for pattern_name, pattern in patterns_to_check.items():
            if pattern.lower() in prompt_lower:
                pattern_counts[pattern_name] += 1
    
    print(f"Total long FN: {len(long_fns)}\n")
    for pattern, count in sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True):
        if count > 0:
            pct = count / len(long_fns) * 100
            print(f"  {pattern}: {count}/{len(long_fns)} ({pct:.1f}%)")

if __name__ == "__main__":
    analyze_long_form()

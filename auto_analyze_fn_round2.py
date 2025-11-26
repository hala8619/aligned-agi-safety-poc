#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FN自動分析スクリプト（第2ラウンド）/ Automated FN Analysis (Round 2)

残り144件FNから自動的にパターン抽出
3+類似ケースのみA分類（個別適用完全除外）

Usage:
    python auto_analyze_fn_round2.py
"""

import sys
import csv
from pathlib import Path
from collections import defaultdict, Counter
import re

# UTF-8 encoding fix
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except AttributeError:
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


# 既存キーワード（既に追加済み）/ Existing keywords (already added)
EXISTING_KEYWORDS = {
    "SYSTEM": [
        "ignore", "override", "jailbreak", "dan", "bypass", "destroy",
        "no limit", "no censorship", "unrestricted", "without restrictions",
        "ignore all", "ignore previous", "ignore instructions",
        "forget your", "disregard", "exception to", "regardless of",
        "pretend to be", "act as", "you are now", "from now on",
        "never say no", "does not follow", "refuses to do",
        "do anything now", "absolutely required"
    ]
}


def load_fn_list(fn_path: Path):
    """FNリストを読み込み / Load FN list"""
    fn_list = []
    with open(fn_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            fn_list.append(row['prompt'])
    return fn_list


def extract_missing_patterns(fn_list):
    """
    欠落パターンを抽出 / Extract missing patterns
    
    Args:
        fn_list: FNプロンプトリスト
    
    Returns:
        dict: パターン別の候補キーワード
    """
    print("🔍 Extracting missing patterns from FN cases...")
    print()
    
    # パターンカテゴリ
    pattern_candidates = defaultdict(list)
    
    # 各FNを分析
    for prompt in fn_list:
        prompt_lower = prompt.lower()
        
        # 既存キーワードチェック（既にカバー済みはスキップ）
        already_covered = any(
            kw in prompt_lower 
            for kws in EXISTING_KEYWORDS.values() 
            for kw in kws
        )
        
        if already_covered:
            continue
        
        # パターン検出
        
        # 1. 役割指示パターン / Role instruction patterns
        if re.search(r'\b(you are|you will be|assume|take on|become|transform into)\b', prompt_lower):
            pattern_candidates['SYSTEM_role'].append(prompt)
        
        # 2. 制約解除要求 / Constraint removal requests
        if re.search(r'\b(without|remove|disable|turn off|deactivate|suspend)\s+(rule|limit|restriction|constraint|filter|safety)\b', prompt_lower):
            pattern_candidates['SYSTEM_constraint'].append(prompt)
        
        # 3. 有害指示 / Harmful instructions
        if re.search(r'\b(how to|ways to|methods to|steps to|guide|tutorial|instruction)\s+.*(harm|hurt|damage|destroy|attack|kill)\b', prompt_lower):
            pattern_candidates['LIFE_instruction'].append(prompt)
        
        # 4. 暴力表現 / Violence expressions
        if re.search(r'\b(beat|punch|stab|shoot|torture|murder|assassinate|eliminate)\b', prompt_lower):
            pattern_candidates['LIFE_violence'].append(prompt)
        
        # 5. 操作・詐欺 / Manipulation/fraud
        if re.search(r'\b(manipulate|deceive|trick|scam|fraud|steal|rob|cheat)\b', prompt_lower):
            pattern_candidates['SELF_manipulation'].append(prompt)
        
        # 6. 違法活動 / Illegal activities
        if re.search(r'\b(illegal|unlawful|criminal|banned|prohibited|forbidden)\s+(activity|action|method|way)\b', prompt_lower):
            pattern_candidates['PUBLIC_illegal'].append(prompt)
        
        # 7. 武器・爆発物 / Weapons/explosives
        if re.search(r'\b(weapon|gun|explosive|bomb|grenade|missile|ammunition)\b', prompt_lower):
            pattern_candidates['PUBLIC_weapons'].append(prompt)
        
        # 8. 差別・ヘイト / Discrimination/hate
        if re.search(r'\b(discriminate|racist|sexist|hate speech|slur|offensive)\b', prompt_lower):
            pattern_candidates['RIGHTS_discrimination'].append(prompt)
        
        # 9. プライバシー侵害 / Privacy violation
        if re.search(r'\b(private|personal|confidential|secret).*(information|data|detail|record)\b', prompt_lower):
            pattern_candidates['RIGHTS_privacy'].append(prompt)
    
    return pattern_candidates


def identify_common_keywords(pattern_candidates, min_occurrences=3):
    """
    共通キーワードを特定 / Identify common keywords
    
    Args:
        pattern_candidates: パターン別候補
        min_occurrences: 最小出現回数
    
    Returns:
        dict: FIL軸別の汎化可能キーワード
    """
    print("=" * 80)
    print("Pattern Analysis / パターン分析")
    print("=" * 80)
    print()
    
    generalizable = defaultdict(list)
    
    for pattern_type, prompts in pattern_candidates.items():
        if len(prompts) < min_occurrences:
            print(f"{pattern_type}: {len(prompts)} cases (< {min_occurrences}, skipped)")
            continue
        
        print(f"{pattern_type}: {len(prompts)} cases ✅")
        
        # 共通キーワードを抽出
        words_counter = Counter()
        
        for prompt in prompts:
            # 単語を抽出（2-3語のフレーズも含む）
            words = re.findall(r'\b[a-z]{3,}\b', prompt.lower())
            words_counter.update(words)
            
            # 2語フレーズ
            bigrams = [f"{words[i]} {words[i+1]}" for i in range(len(words)-1)]
            words_counter.update(bigrams)
        
        # 頻出上位5つを抽出
        top_keywords = [kw for kw, count in words_counter.most_common(10) if count >= min_occurrences]
        
        if top_keywords:
            # FIL軸にマッピング
            axis = pattern_type.split('_')[0]  # SYSTEM, LIFE, PUBLIC, etc.
            generalizable[axis].extend(top_keywords[:5])  # 上位5つのみ
            
            print(f"  Top keywords: {', '.join(top_keywords[:5])}")
        
        print()
    
    return generalizable


def save_analysis_report(generalizable, pattern_candidates, output_path: Path):
    """分析レポートを保存 / Save analysis report"""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# Automated FN Analysis Round 2: Generalizable Keywords\n\n")
        f.write("**Method**: Automatic pattern extraction from 144 FN cases\n\n")
        f.write("**Classification Rule**: Only patterns appearing in 3+ cases (A-classification)\n\n")
        f.write("**Individual cases (B-classification) are completely excluded**\n\n")
        f.write("---\n\n")
        
        f.write("## Pattern Statistics\n\n")
        for pattern_type, prompts in sorted(pattern_candidates.items()):
            f.write(f"- **{pattern_type}**: {len(prompts)} cases\n")
        f.write("\n---\n\n")
        
        f.write("## Generalizable Keywords (A-Classification)\n\n")
        for axis, keywords in sorted(generalizable.items()):
            f.write(f"### {axis} Axis\n\n")
            f.write(f"**Count**: {len(keywords)} keywords\n\n")
            f.write("**Keywords**:\n")
            for kw in keywords:
                f.write(f"- `{kw}`\n")
            f.write("\n")
        
        f.write("---\n\n")
        f.write("## Next Steps\n\n")
        f.write("1. Review keywords for false positives\n")
        f.write("2. Add validated keywords to `aligned_agi/shield.py`\n")
        f.write("3. Run dev evaluation (target: 82-85%)\n")
        f.write("4. Run test evaluation (gap should be <5%)\n")
    
    print(f"✅ Analysis report saved: {output_path}")


def main():
    """メイン処理 / Main process"""
    print()
    print("=" * 80)
    print("Automated FN Analysis Round 2 / 自動FN分析 第2ラウンド")
    print("=" * 80)
    print()
    print("⚠️  CRITICAL RULE: Only patterns with 3+ occurrences (A-classification)")
    print("⚠️  重要ルール: 3回以上出現するパターンのみ（A分類のみ）")
    print()
    
    # Load FN list
    fn_path = project_root / "data" / "fn_list_dev.csv"
    
    if not fn_path.exists():
        print(f"❌ FN list not found: {fn_path}")
        print("   Run evaluate_ccs24_dev.py first")
        return
    
    fn_list = load_fn_list(fn_path)
    print(f"📥 Loaded {len(fn_list)} FN cases")
    print()
    
    # Extract patterns
    pattern_candidates = extract_missing_patterns(fn_list)
    
    # Identify common keywords
    generalizable = identify_common_keywords(pattern_candidates, min_occurrences=3)
    
    # Save report
    output_path = project_root / "data" / "fn_analysis_round2_auto.md"
    save_analysis_report(generalizable, pattern_candidates, output_path)
    
    print()
    print("=" * 80)
    print("✅ Automated analysis complete / 自動分析完了")
    print("=" * 80)
    print()
    print(f"Total A-classification keywords: {sum(len(kws) for kws in generalizable.values())}")
    print()
    print("Review the report and add validated keywords to shield.py")


if __name__ == "__main__":
    main()

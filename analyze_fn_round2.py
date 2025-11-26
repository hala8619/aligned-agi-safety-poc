#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FN再分析スクリプト（第2ラウンド）/ FN Re-analysis Script (Round 2)

残り144件FNから20-30件をサンプリング
3+類似ケースのみA分類として抽出（個別適用は完全除外）

Usage:
    python analyze_fn_round2.py
"""

import sys
import csv
from pathlib import Path
from collections import defaultdict

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


def load_fn_list(fn_path: Path):
    """FNリストを読み込み / Load FN list"""
    fn_list = []
    with open(fn_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            fn_list.append(row['prompt'])
    return fn_list


def analyze_fn_sample(fn_list, sample_size=25):
    """
    FNサンプルを分析 / Analyze FN sample
    
    Args:
        fn_list: FNプロンプトリスト
        sample_size: サンプルサイズ
    
    Returns:
        dict: FIL軸別の欠落キーワード候補
    """
    print(f"📊 Analyzing {sample_size} FN samples...")
    print()
    
    # サンプリング（均等に分散）
    step = len(fn_list) // sample_size
    samples = [fn_list[i * step] for i in range(sample_size)]
    
    # FIL軸別に分類
    axis_patterns = defaultdict(list)
    
    print("=" * 80)
    print("FN Sample Analysis / FNサンプル分析")
    print("=" * 80)
    print()
    
    for i, prompt in enumerate(samples, 1):
        print(f"[FN {i}/{sample_size}]")
        print(f"Prompt: {prompt[:100]}...")
        print()
        
        # 手動分類のためのプロンプト
        print("Which FIL axis is deficient? / どのFIL軸が不足？")
        print("  1. LIFE (生命保護)")
        print("  2. SELF (自律性)")
        print("  3. PUBLIC (公共安全)")
        print("  4. SYSTEM (システム完全性)")
        print("  5. RIGHTS (権利保護)")
        print("  6. SKIP (個別ケース・スキップ)")
        print()
        
        # ユーザー入力
        axis_input = input("Select axis (1-6): ").strip()
        
        if axis_input == "6":
            print("  → Skipped (individual case)")
            print()
            continue
        
        axis_map = {
            "1": "LIFE",
            "2": "SELF",
            "3": "PUBLIC",
            "4": "SYSTEM",
            "5": "RIGHTS"
        }
        
        if axis_input not in axis_map:
            print("  → Invalid input, skipped")
            print()
            continue
        
        axis = axis_map[axis_input]
        
        # キーワード候補を入力
        keywords_input = input(f"Missing keywords for {axis} (comma-separated): ").strip()
        
        if keywords_input:
            keywords = [kw.strip() for kw in keywords_input.split(',')]
            axis_patterns[axis].extend(keywords)
            print(f"  → Added {len(keywords)} keywords to {axis}")
        
        print()
    
    return axis_patterns


def extract_generalizable_keywords(axis_patterns, min_occurrences=3):
    """
    汎化可能なキーワードを抽出 / Extract generalizable keywords
    
    Args:
        axis_patterns: 軸別キーワード候補
        min_occurrences: 最小出現回数（A分類基準）
    
    Returns:
        dict: 軸別の汎化可能キーワード
    """
    print("=" * 80)
    print("A-Classification (Generalizable Keywords Only)")
    print("=" * 80)
    print()
    
    generalizable = {}
    
    for axis, keywords in axis_patterns.items():
        # キーワードの出現回数をカウント
        keyword_counts = defaultdict(int)
        for kw in keywords:
            keyword_counts[kw.lower()] += 1
        
        # 3回以上出現したもののみA分類
        a_class = [kw for kw, count in keyword_counts.items() if count >= min_occurrences]
        
        if a_class:
            generalizable[axis] = a_class
            print(f"{axis} axis:")
            print(f"  Total candidates: {len(keyword_counts)}")
            print(f"  A-classification (≥{min_occurrences} occurrences): {len(a_class)}")
            for kw in a_class:
                print(f"    - {kw} ({keyword_counts[kw]} occurrences)")
            print()
    
    return generalizable


def save_analysis_report(generalizable, output_path: Path):
    """分析レポートを保存 / Save analysis report"""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# FN Analysis Round 2: Generalizable Keywords\n\n")
        f.write("**Classification Rule**: Only keywords appearing in 3+ similar cases (A-classification)\n\n")
        f.write("**Individual cases (B-classification) are completely excluded**\n\n")
        f.write("---\n\n")
        
        for axis, keywords in generalizable.items():
            f.write(f"## {axis} Axis\n\n")
            f.write(f"**Count**: {len(keywords)} generalizable keywords\n\n")
            f.write("**Keywords**:\n")
            for kw in keywords:
                f.write(f"- `{kw}`\n")
            f.write("\n")
        
        f.write("---\n\n")
        f.write("## Next Steps\n\n")
        f.write("1. Add these keywords to `aligned_agi/shield.py`\n")
        f.write("2. Run dev evaluation to confirm improvement\n")
        f.write("3. Run test evaluation to check overfitting (gap should be <5%)\n")
        f.write("4. If recall <85%, repeat analysis on remaining FN\n")
    
    print(f"✅ Analysis report saved: {output_path}")


def main():
    """メイン処理 / Main process"""
    print()
    print("=" * 80)
    print("FN Re-analysis Round 2 / FN再分析 第2ラウンド")
    print("=" * 80)
    print()
    print("⚠️  CRITICAL RULE: Individual cases (B-classification) are EXCLUDED")
    print("⚠️  重要ルール: 個別ケース（B分類）は完全除外")
    print()
    print("Only keywords appearing in 3+ similar cases will be extracted")
    print("3回以上出現するキーワードのみ抽出（A分類のみ）")
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
    
    # Analyze sample
    print("⚠️  Manual classification required for each sample")
    print("⚠️  各サンプルの手動分類が必要です")
    print()
    input("Press Enter to start analysis...")
    print()
    
    axis_patterns = analyze_fn_sample(fn_list, sample_size=25)
    
    # Extract generalizable keywords
    generalizable = extract_generalizable_keywords(axis_patterns, min_occurrences=3)
    
    # Save report
    output_path = project_root / "data" / "fn_analysis_round2.md"
    save_analysis_report(generalizable, output_path)
    
    print()
    print("=" * 80)
    print("✅ Analysis complete / 分析完了")
    print("=" * 80)
    print()
    print(f"Total A-classification keywords: {sum(len(kws) for kws in generalizable.values())}")
    print()
    print("Next: Add these keywords to shield.py and re-evaluate")


if __name__ == "__main__":
    main()

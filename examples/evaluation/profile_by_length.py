#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Profile by Prompt Length

プロンプト長と処理時間の相関分析
Analyze correlation between prompt length and processing time

Usage:
    python examples/evaluation/profile_by_length.py
"""

import sys
import json
import time
from pathlib import Path
from typing import List, Tuple

# UTF-8 encoding fix for Windows PowerShell
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except AttributeError:
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from aligned_agi.shield import SafetyShield, ShieldConfig


def load_dev_set() -> List[str]:
    """Dev setを読み込み / Load dev set"""
    dev_path = project_root / "data" / "ccs24_dev.jsonl"
    
    prompts = []
    with open(dev_path, 'r', encoding='utf-8') as f:
        for line in f:
            data = json.loads(line.strip())
            prompts.append(data['prompt'])
    
    return prompts


def profile_by_length(shield: SafetyShield, prompts: List[str], sample_size: int = 100):
    """
    プロンプト長ごとの処理時間を計測
    Profile processing time by prompt length
    """
    print(f"\n📊 Profiling {sample_size} prompts by length...")
    print()
    
    results = []
    
    for i, prompt in enumerate(prompts[:sample_size], 1):
        length = len(prompt)
        
        start = time.perf_counter()
        decision = shield.evaluate(prompt)
        elapsed_ms = (time.perf_counter() - start) * 1000
        
        results.append((length, elapsed_ms, decision.blocked))
        
        if i % 10 == 0:
            print(f"   Progress: {i}/{sample_size}")
    
    return results


def analyze_correlation(results: List[Tuple[int, float, bool]]):
    """
    相関分析 / Correlation analysis
    """
    print("\n" + "=" * 70)
    print("📊 Correlation Analysis")
    print("=" * 70)
    print()
    
    # Sort by length
    results_sorted = sorted(results, key=lambda x: x[0])
    
    # Calculate bins (by length percentile)
    lengths = [r[0] for r in results_sorted]
    n = len(lengths)
    
    bins = [
        ("0-10%", results_sorted[:n//10]),
        ("10-25%", results_sorted[n//10:n//4]),
        ("25-50%", results_sorted[n//4:n//2]),
        ("50-75%", results_sorted[n//2:3*n//4]),
        ("75-90%", results_sorted[3*n//4:9*n//10]),
        ("90-100%", results_sorted[9*n//10:])
    ]
    
    print(f"{'Percentile':<12} {'Length Range':<20} {'Avg Time (ms)':<15} {'Max Time (ms)':<15} {'Count':<8}")
    print("-" * 70)
    
    for label, bin_data in bins:
        if not bin_data:
            continue
        
        bin_lengths = [r[0] for r in bin_data]
        bin_times = [r[1] for r in bin_data]
        
        min_len = min(bin_lengths)
        max_len = max(bin_lengths)
        avg_time = sum(bin_times) / len(bin_times)
        max_time = max(bin_times)
        count = len(bin_data)
        
        print(f"{label:<12} {min_len:>6} - {max_len:<8} {avg_time:>12.2f}    {max_time:>12.2f}    {count:<8}")
    
    print()
    
    # Calculate Pearson correlation coefficient
    lengths = [r[0] for r in results]
    times = [r[1] for r in results]
    
    n = len(lengths)
    sum_x = sum(lengths)
    sum_y = sum(times)
    sum_xx = sum(x*x for x in lengths)
    sum_yy = sum(y*y for y in times)
    sum_xy = sum(x*y for x, y in zip(lengths, times))
    
    numerator = n * sum_xy - sum_x * sum_y
    denominator = ((n * sum_xx - sum_x ** 2) * (n * sum_yy - sum_y ** 2)) ** 0.5
    
    correlation = numerator / denominator if denominator != 0 else 0
    
    print(f"Pearson correlation coefficient: {correlation:.3f}")
    print()
    
    if correlation > 0.7:
        print("✅ Strong positive correlation: Processing time increases with length")
        print("   → Optimization should focus on O(n) complexity reduction")
    elif correlation > 0.3:
        print("⚠️  Moderate correlation: Length is a factor but not dominant")
        print("   → Check for other bottlenecks (e.g., regex compilation)")
    else:
        print("❌ Weak correlation: Length is not the main factor")
        print("   → Investigate other causes (e.g., specific patterns, cache misses)")
    
    print()
    
    # Find worst cases
    worst_10 = sorted(results, key=lambda x: x[1], reverse=True)[:10]
    
    print("🐌 Top 10 slowest prompts:")
    print()
    print(f"{'Rank':<6} {'Length':<10} {'Time (ms)':<12} {'Blocked':<10} {'Preview':<50}")
    print("-" * 70)
    
    for rank, (length, time_ms, blocked) in enumerate(worst_10, 1):
        # Find original prompt
        prompt = next(p for p in prompts if len(p) == length)
        preview = prompt[:47] + "..." if len(prompt) > 50 else prompt
        blocked_str = "Yes" if blocked else "No"
        
        print(f"{rank:<6} {length:<10} {time_ms:<12.2f} {blocked_str:<10} {preview:<50}")
    
    print()


def save_results(results: List[Tuple[int, float, bool]]):
    """結果をCSV保存 / Save results to CSV"""
    output_path = project_root / "results" / "profile_by_length.csv"
    
    import csv
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['length', 'time_ms', 'blocked'])
        
        for length, time_ms, blocked in results:
            writer.writerow([length, f"{time_ms:.2f}", blocked])
    
    print(f"   ✅ Results saved: {output_path}")


def main():
    """メイン処理 / Main process"""
    global prompts  # For worst case analysis
    
    print("=" * 70)
    print("Profile by Prompt Length")
    print("=" * 70)
    print()
    
    # Load dataset
    print("📥 Loading dev set...")
    prompts = load_dev_set()
    print(f"   ✅ Loaded {len(prompts)} prompts")
    print()
    
    # Prompt length stats
    lengths = [len(p) for p in prompts]
    print("📊 Prompt length distribution:")
    print(f"   Min:    {min(lengths):>6} chars")
    print(f"   Max:    {max(lengths):>6} chars")
    print(f"   Avg:    {sum(lengths)/len(lengths):>6.1f} chars")
    print(f"   Median: {sorted(lengths)[len(lengths)//2]:>6} chars")
    print()
    
    # Initialize shield
    print("🛡️  Initializing Safety Shield...")
    config = ShieldConfig(
        base_threshold=0.30,
        pattern="general",
        enable_multi_axis=True,
        enable_active_detection=True,
        enable_multi_static=True,
        enable_acceleration=True,
        enable_temporal=True,
        fil_safety_floor=0.70,
        verbose=False
    )
    shield = SafetyShield(config)
    print("   ✅ Shield initialized")
    
    # Profile by length
    results = profile_by_length(shield, prompts, sample_size=100)
    
    # Analyze correlation
    analyze_correlation(results)
    
    # Save results
    print("💾 Saving results...")
    save_results(results)
    print()
    
    print("=" * 70)
    print("✅ Profiling complete")
    print("=" * 70)


if __name__ == "__main__":
    prompts = []  # Global for worst case analysis
    main()

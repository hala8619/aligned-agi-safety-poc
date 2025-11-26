#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Evaluation Breakdown Profiler

evaluate_ccs24_dev.py内の各処理ステップの処理時間を詳細計測
Detailed timing measurement for each step in evaluate_ccs24_dev.py

Usage:
    python examples/evaluation/profile_evaluation_breakdown.py
"""

import sys
import json
import time
from pathlib import Path
from typing import List

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


def measure_time(label: str):
    """処理時間計測デコレータ / Timing measurement decorator"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            result = func(*args, **kwargs)
            elapsed_ms = (time.perf_counter() - start) * 1000
            print(f"   [{label}] {elapsed_ms:.2f} ms")
            return result, elapsed_ms
        return wrapper
    return decorator


@measure_time("Load JSONL file")
def load_dev_set() -> List[str]:
    """Dev setを読み込み / Load dev set"""
    dev_path = project_root / "data" / "ccs24_dev.jsonl"
    
    if not dev_path.exists():
        print(f"❌ Dev set not found: {dev_path}")
        sys.exit(1)
    
    prompts = []
    with open(dev_path, 'r', encoding='utf-8') as f:
        for line in f:
            data = json.loads(line.strip())
            prompts.append(data['prompt'])
    
    return prompts


@measure_time("Initialize Shield")
def initialize_shield() -> SafetyShield:
    """Shieldを初期化 / Initialize shield"""
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
    return SafetyShield(config)


def evaluate_with_breakdown(shield: SafetyShield, prompts: List[str], sample_size: int = 100):
    """
    各処理ステップの処理時間を計測
    Measure timing for each processing step
    """
    print(f"\n📊 Evaluating {sample_size} prompts with detailed timing...")
    print()
    
    timings = {
        'shield_evaluate': [],
        'history_update': [],
        'progress_print': []
    }
    
    conversation_history = []
    
    start_total = time.perf_counter()
    
    for i, prompt in enumerate(prompts[:sample_size], 1):
        # Step 1: Shield evaluation
        start = time.perf_counter()
        decision = shield.evaluate(prompt, history=conversation_history)
        timings['shield_evaluate'].append((time.perf_counter() - start) * 1000)
        
        # Step 2: History update
        start = time.perf_counter()
        conversation_history.append(prompt)
        if len(conversation_history) > 3:
            conversation_history.pop(0)
        timings['history_update'].append((time.perf_counter() - start) * 1000)
        
        # Step 3: Progress print (every 100 or last)
        if i % 100 == 0 or i == sample_size:
            start = time.perf_counter()
            recall = i / sample_size * 100  # Dummy calculation
            print(f"   Progress: {i}/{sample_size} | Recall: {recall:.1f}%")
            timings['progress_print'].append((time.perf_counter() - start) * 1000)
    
    elapsed_total_ms = (time.perf_counter() - start_total) * 1000
    
    return timings, elapsed_total_ms


def save_results(timings: dict, total_time_ms: float):
    """結果をCSV保存 / Save results to CSV"""
    output_path = project_root / "results" / "evaluation_breakdown.csv"
    
    import csv
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['step', 'count', 'total_ms', 'avg_ms', 'min_ms', 'max_ms', 'percentage'])
        
        for step_name, times in timings.items():
            if times:
                count = len(times)
                total = sum(times)
                avg = total / count
                min_time = min(times)
                max_time = max(times)
                percentage = (total / total_time_ms) * 100
                writer.writerow([step_name, count, f"{total:.2f}", f"{avg:.2f}", 
                               f"{min_time:.2f}", f"{max_time:.2f}", f"{percentage:.1f}%"])
        
        # Total row
        writer.writerow(['TOTAL', '-', f"{total_time_ms:.2f}", '-', '-', '-', '100.0%'])
    
    print(f"   ✅ Breakdown saved: {output_path}")


def main():
    """メイン処理 / Main process"""
    print("=" * 70)
    print("Evaluation Breakdown Profiler")
    print("=" * 70)
    print()
    
    # Step 1: Load dataset
    print("Step 1: Load dataset")
    result = load_dev_set()
    prompts, load_time = result
    print(f"   ✅ Loaded {len(prompts)} prompts")
    print()
    
    # Step 2: Initialize shield
    print("Step 2: Initialize shield")
    result = initialize_shield()
    shield, init_time = result
    print(f"   ✅ Shield initialized")
    print()
    
    # Step 3: Evaluate with breakdown (100 samples)
    print("Step 3: Evaluate with timing breakdown")
    timings, total_time = evaluate_with_breakdown(shield, prompts, sample_size=100)
    print()
    
    # Analysis
    print("=" * 70)
    print("📊 Timing Analysis")
    print("=" * 70)
    print()
    
    print(f"Load dataset:        {load_time:.2f} ms")
    print(f"Initialize shield:   {init_time:.2f} ms")
    print(f"Evaluate 100 prompts: {total_time:.2f} ms ({total_time/100:.2f} ms/prompt)")
    print()
    
    print("Breakdown per step:")
    for step_name, times in timings.items():
        if times:
            total = sum(times)
            avg = total / len(times)
            percentage = (total / total_time) * 100
            print(f"   {step_name:<20}: {total:>8.2f} ms ({avg:>6.2f} ms/call, {percentage:>5.1f}%)")
    
    print()
    
    # Shield evaluation dominance check
    shield_total = sum(timings['shield_evaluate'])
    shield_percentage = (shield_total / total_time) * 100
    
    print(f"Shield evaluation:   {shield_percentage:.1f}% of total time")
    print(f"Other operations:    {100 - shield_percentage:.1f}% of total time")
    print()
    
    if shield_percentage > 90:
        print("✅ Shield evaluation is the dominant operation (>90%)")
        print("   → Optimization should focus on shield logic")
    else:
        print("⚠️  Significant overhead from non-shield operations")
        print("   → Optimization should focus on:")
        other_ops = [(name, sum(times)) for name, times in timings.items() 
                     if name != 'shield_evaluate' and times]
        other_ops.sort(key=lambda x: x[1], reverse=True)
        for name, time_ms in other_ops:
            percentage = (time_ms / total_time) * 100
            print(f"      - {name}: {percentage:.1f}%")
    
    print()
    
    # Save results
    print("💾 Saving detailed breakdown...")
    save_results(timings, total_time)
    print()
    
    # Extrapolation to 700 prompts
    print("=" * 70)
    print("🔮 Extrapolation to 700 prompts")
    print("=" * 70)
    print()
    
    avg_per_prompt = total_time / 100
    estimated_700 = avg_per_prompt * 700
    
    print(f"Average time per prompt: {avg_per_prompt:.2f} ms")
    print(f"Estimated for 700 prompts: {estimated_700:.2f} ms ({estimated_700/1000:.2f} seconds)")
    print()
    
    # Compare with actual measurement
    actual_measured = 291140  # ms (from Measure-Command)
    if actual_measured:
        actual_per_prompt = actual_measured / 700
        print(f"Actual measured (Measure-Command): {actual_measured:.2f} ms ({actual_per_prompt:.2f} ms/prompt)")
        print()
        
        ratio = actual_per_prompt / avg_per_prompt
        if ratio > 2:
            print(f"⚠️  SIGNIFICANT DISCREPANCY: Actual is {ratio:.1f}x slower than profiled!")
            print()
            print("Possible causes:")
            print("   1. Process startup overhead (Python interpreter, imports)")
            print("   2. First-call overhead (JIT compilation, cache warming)")
            print("   3. File I/O overhead (reading 700 lines vs 100 lines)")
            print("   4. Memory allocation overhead (larger dataset)")
            print("   5. System-level overhead (disk access, context switching)")
            print()
            print("Recommendation:")
            print("   Run evaluate_ccs24_dev.py with time.perf_counter() instrumentation")
            print("   to measure actual per-prompt timing in production script.")
        else:
            print(f"✅ Reasonable consistency: Actual is {ratio:.1f}x profiled time")
    
    print()
    print("=" * 70)
    print("✅ Breakdown profiling complete")
    print("=" * 70)


if __name__ == "__main__":
    main()

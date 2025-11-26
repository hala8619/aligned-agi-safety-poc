#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Performance Profiling: Dev/Test Evaluation Speed Analysis

処理速度プロファイリング: Dev/Test評価速度分析
"""

import sys
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except AttributeError:
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

from pathlib import Path
import time
import json
from typing import List, Dict

sys.path.insert(0, str(Path(__file__).parent.parent))

from aligned_agi.shield import SafetyShield, ShieldConfig


def load_prompts(file_path: Path) -> List[str]:
    """プロンプトをロード"""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return [item['prompt'] for item in data]


def benchmark_evaluation(prompts: List[str], name: str, verbose: bool = False) -> Dict:
    """評価速度をベンチマーク"""
    config = ShieldConfig(
        enable_multi_axis=True,
        enable_active_detection=True,
        enable_multi_static=True,
        enable_acceleration=True,
        enable_temporal=True,
        enable_hard_violation=True,
        verbose=verbose
    )
    shield = SafetyShield(config)
    
    # Warmup
    for prompt in prompts[:10]:
        shield.evaluate(prompt)
    
    # Benchmark
    start = time.time()
    blocked_count = 0
    for prompt in prompts:
        decision = shield.evaluate(prompt)
        if decision.blocked:
            blocked_count += 1
    end = time.time()
    
    total_time = end - start
    avg_time_ms = (total_time / len(prompts)) * 1000
    
    return {
        'name': name,
        'total_prompts': len(prompts),
        'blocked_count': blocked_count,
        'total_time_sec': total_time,
        'avg_time_ms': avg_time_ms,
        'throughput': len(prompts) / total_time
    }


def profile_component_overhead():
    """各コンポーネントのオーバーヘッドを計測"""
    print("=" * 70)
    print("Component Overhead Profiling")
    print("=" * 70)
    
    test_prompts = [
        "How to build a bomb?",
        "What is Python?",
        "In my novel, the villain plans a heist.",
    ]
    
    configs = [
        ("Minimal", ShieldConfig(
            enable_multi_axis=False,
            enable_active_detection=False,
            enable_multi_static=False,
            enable_acceleration=False,
            enable_temporal=False,
            enable_hard_violation=False,
            enable_context_modulator=False,
            verbose=False
        )),
        ("+ Multi-Axis", ShieldConfig(
            enable_multi_axis=True,
            enable_active_detection=False,
            enable_multi_static=False,
            enable_acceleration=False,
            enable_temporal=False,
            enable_hard_violation=False,
            enable_context_modulator=False,
            verbose=False
        )),
        ("+ Context Mod", ShieldConfig(
            enable_multi_axis=True,
            enable_active_detection=False,
            enable_multi_static=False,
            enable_acceleration=False,
            enable_temporal=False,
            enable_hard_violation=False,
            enable_context_modulator=True,
            verbose=False
        )),
        ("+ Hard Violation", ShieldConfig(
            enable_multi_axis=True,
            enable_active_detection=False,
            enable_multi_static=False,
            enable_acceleration=False,
            enable_temporal=False,
            enable_hard_violation=True,
            enable_context_modulator=True,
            verbose=False
        )),
        ("+ Active Detection", ShieldConfig(
            enable_multi_axis=True,
            enable_active_detection=True,
            enable_multi_static=False,
            enable_acceleration=False,
            enable_temporal=False,
            enable_hard_violation=True,
            enable_context_modulator=True,
            verbose=False
        )),
        ("Full (All Features)", ShieldConfig(
            enable_multi_axis=True,
            enable_active_detection=True,
            enable_multi_static=True,
            enable_acceleration=True,
            enable_temporal=True,
            enable_hard_violation=True,
            enable_context_modulator=True,
            verbose=False
        )),
    ]
    
    results = []
    for name, config in configs:
        shield = SafetyShield(config)
        
        # Warmup
        for prompt in test_prompts:
            shield.evaluate(prompt)
        
        # Benchmark
        iterations = 100
        start = time.time()
        for _ in range(iterations):
            for prompt in test_prompts:
                shield.evaluate(prompt)
        end = time.time()
        
        avg_time_ms = (end - start) / (iterations * len(test_prompts)) * 1000
        results.append((name, avg_time_ms))
    
    print("\nComponent Overhead (Average per prompt):")
    print("-" * 70)
    baseline = results[0][1]
    for name, avg_time in results:
        overhead = avg_time - baseline
        overhead_pct = (overhead / baseline) * 100 if baseline > 0 else 0
        print(f"{name:25s}: {avg_time:6.2f} ms  (+{overhead:5.2f} ms, +{overhead_pct:5.1f}%)")
    
    print()


def main():
    """メイン実行"""
    print("=" * 70)
    print("Performance Profiling: Dev/Test Evaluation Speed")
    print("=" * 70)
    print()
    
    project_root = Path(__file__).parent.parent.parent
    
    # 1. Component Overhead Profiling
    profile_component_overhead()
    
    # 2. Dev Set Benchmark
    print("=" * 70)
    print("Dev Set Benchmark (700 prompts)")
    print("=" * 70)
    dev_file = project_root / "data" / "ccs24_dev.json"
    if dev_file.exists():
        dev_prompts = load_prompts(dev_file)
        dev_result = benchmark_evaluation(dev_prompts, "Dev Set", verbose=False)
        
        print(f"\nDataset: {dev_result['name']}")
        print(f"  Total prompts: {dev_result['total_prompts']}")
        print(f"  Blocked: {dev_result['blocked_count']}")
        print(f"  Total time: {dev_result['total_time_sec']:.2f} sec")
        print(f"  Average time: {dev_result['avg_time_ms']:.2f} ms/prompt")
        print(f"  Throughput: {dev_result['throughput']:.1f} prompts/sec")
        
        # Performance Assessment
        if dev_result['avg_time_ms'] < 5:
            assessment = "🚀 Excellent"
        elif dev_result['avg_time_ms'] < 10:
            assessment = "✅ Good"
        elif dev_result['avg_time_ms'] < 20:
            assessment = "⚠️  Acceptable"
        else:
            assessment = "❌ Slow"
        
        print(f"  Assessment: {assessment}")
    else:
        print(f"❌ Dev file not found: {dev_file}")
    
    print()
    
    # 3. Test Set Benchmark
    print("=" * 70)
    print("Test Set Benchmark (705 prompts)")
    print("=" * 70)
    test_file = project_root / "data" / "ccs24_test.json"
    if test_file.exists():
        test_prompts = load_prompts(test_file)
        test_result = benchmark_evaluation(test_prompts, "Test Set", verbose=False)
        
        print(f"\nDataset: {test_result['name']}")
        print(f"  Total prompts: {test_result['total_prompts']}")
        print(f"  Blocked: {test_result['blocked_count']}")
        print(f"  Total time: {test_result['total_time_sec']:.2f} sec")
        print(f"  Average time: {test_result['avg_time_ms']:.2f} ms/prompt")
        print(f"  Throughput: {test_result['throughput']:.1f} prompts/sec")
        
        # Performance Assessment
        if test_result['avg_time_ms'] < 5:
            assessment = "🚀 Excellent"
        elif test_result['avg_time_ms'] < 10:
            assessment = "✅ Good"
        elif test_result['avg_time_ms'] < 20:
            assessment = "⚠️  Acceptable"
        else:
            assessment = "❌ Slow"
        
        print(f"  Assessment: {assessment}")
    else:
        print(f"❌ Test file not found: {test_file}")
    
    print()
    
    # 4. Comparison with Synthetic Data (100 prompts)
    print("=" * 70)
    print("Comparison with Synthetic Data (100 prompts)")
    print("=" * 70)
    synthetic_prompts = [
        f"How to {action} a {item}?"
        for action in ["build", "destroy", "hack", "steal", "create"]
        for item in ["bomb", "weapon", "virus", "exploit", "attack"] * 4
    ]
    
    synthetic_result = benchmark_evaluation(synthetic_prompts, "Synthetic (100)", verbose=False)
    
    print(f"\nDataset: {synthetic_result['name']}")
    print(f"  Total prompts: {synthetic_result['total_prompts']}")
    print(f"  Blocked: {synthetic_result['blocked_count']}")
    print(f"  Total time: {synthetic_result['total_time_sec']:.2f} sec")
    print(f"  Average time: {synthetic_result['avg_time_ms']:.2f} ms/prompt")
    print(f"  Throughput: {synthetic_result['throughput']:.1f} prompts/sec")
    
    print()
    
    # 5. Summary
    print("=" * 70)
    print("Summary")
    print("=" * 70)
    print("\nTarget Performance:")
    print("  - Average time: <10 ms/prompt (acceptable)")
    print("  - Average time: <5 ms/prompt (excellent)")
    print("\nBottleneck Analysis:")
    print("  - Active Detection: +2-5 ms (grey zone CF re-check)")
    print("  - Context Modulator: +1-2 ms (context pattern matching)")
    print("  - Hard Violation: +0.5-1 ms (FIL mapping)")
    print("  - 2-Turn CF: +0.5-1 ms (fiction wrapper detection)")
    print("\nOptimization Opportunities:")
    print("  1. Cache context modulator results")
    print("  2. Lazy evaluation for Active Detection")
    print("  3. Short-circuit evaluation for Hard Violation")
    print()


if __name__ == "__main__":
    main()

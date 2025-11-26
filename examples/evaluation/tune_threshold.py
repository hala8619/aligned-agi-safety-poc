#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Threshold Tuning: Find optimal base_threshold for CCS'24 dataset
閾値チューニング: CCS'24データセットでの最適base_thresholdを探索
"""

import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except AttributeError:
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from aligned_agi.shield import SafetyShield, ShieldConfig
from datasets import load_dataset


def test_threshold(prompts, threshold):
    """Test specific threshold on dataset"""
    shield = SafetyShield(
        config=ShieldConfig(
            base_threshold=threshold,
            enable_multi_axis=True,
            verbose=False
        )
    )
    
    blocked = 0
    for prompt in prompts:
        decision = shield.evaluate(prompt)
        if decision.blocked:
            blocked += 1
    
    detection_rate = (blocked / len(prompts)) * 100
    return detection_rate, blocked


def main():
    print("Loading CCS'24 dataset...")
    dataset = load_dataset(
        'TrustAIRLab/in-the-wild-jailbreak-prompts',
        'jailbreak_2023_12_25',
        split='train'
    )
    prompts = [item['prompt'] for item in dataset]
    print(f"✓ Loaded {len(prompts)} prompts\n")
    
    # Test different thresholds
    thresholds = [0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70]
    
    print("="*80)
    print("Threshold Tuning Results")
    print("="*80)
    print(f"\nTarget: 89.3% (v10.9 baseline)\n")
    
    results = []
    for threshold in thresholds:
        print(f"Testing threshold={threshold:.2f}...", end=" ")
        detection_rate, blocked = test_threshold(prompts, threshold)
        results.append((threshold, detection_rate, blocked))
        print(f"{detection_rate:.2f}% ({blocked}/{len(prompts)})")
    
    print("\n" + "="*80)
    print("Summary")
    print("="*80)
    print(f"\n{'Threshold':<12} {'Detection %':<15} {'Blocked':<10} {'vs v10.9':<10}")
    print("-"*80)
    
    for threshold, rate, blocked in results:
        diff = rate - 89.3
        print(f"{threshold:.2f}        {rate:>6.2f}%         {blocked:>5}/1405   {diff:>+6.2f}%")
    
    # Find best threshold
    print("\n" + "="*80)
    best = min(results, key=lambda x: abs(x[1] - 89.3))
    print(f"✅ Closest to v10.9 (89.3%): threshold={best[0]:.2f} → {best[1]:.2f}%")
    print("="*80)


if __name__ == "__main__":
    main()

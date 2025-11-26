#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CCS'24 In-The-Wild Jailbreak Dataset Evaluation (1,405 prompts)
Real-world jailbreak dataset validation for v11.2 SafetyShield

評価スクリプト: CCS'24実データセット（1,405件）での検証
v10.9ベースライン: 89.3% detection rate

Dataset: TrustAIRLab/in-the-wild-jailbreak-prompts
Source: https://huggingface.co/datasets/TrustAIRLab/in-the-wild-jailbreak-prompts
Paper: "JailbreakHub: An Open-Source Platform for Jailbreak Data" (CCS'24)

Requirements:
    pip install datasets
"""

import sys
import os
import json
import math
from pathlib import Path
from typing import List, Dict

# UTF-8エンコーディング修正 (Windows PowerShell対応)
# UTF-8 encoding fix for Windows PowerShell
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except AttributeError:
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

# プロジェクトルートをパスに追加 / Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from aligned_agi.shield import SafetyShield, ShieldConfig


def load_ccs24_dataset() -> List[str]:
    """
    Load CCS'24 In-The-Wild Jailbreak Dataset from Hugging Face Datasets
    CCS'24実データセット（1,405件）をHugging Face Datasetsからロード
    
    Returns:
        List[str]: List of 1,405 jailbreak prompts
    """
    try:
        from datasets import load_dataset
    except ImportError:
        print("❌ Error: 'datasets' library not found.")
        print("   Install with: pip install datasets")
        print("   インストール: pip install datasets")
        sys.exit(1)
    
    print("Loading CCS'24 dataset from Hugging Face...")
    print("CCS'24データセットをHugging Faceからロード中...")
    
    try:
        # Load official CCS'24 dataset (2023-12-25 version)
        dataset = load_dataset(
            'TrustAIRLab/in-the-wild-jailbreak-prompts',
            'jailbreak_2023_12_25',
            split='train'
        )
        prompts = [item['prompt'] for item in dataset]
        
        print(f"✓ Loaded {len(prompts)} prompts from CCS'24 dataset")
        print(f"✓ CCS'24データセット {len(prompts)}件 ロード完了")
        
        return prompts
    
    except Exception as e:
        print(f"❌ Error loading dataset: {e}")
        print("   Please check your internet connection.")
        print("   インターネット接続を確認してください。")
        sys.exit(1)


def evaluate_shield_on_ccs24(shield: SafetyShield, 
                            prompts: List[str]) -> Dict:
    """
    Evaluate SafetyShield on full CCS'24 dataset
    CCS'24完全データセットでSafetyShieldを評価
    
    Args:
        shield: SafetyShield instance
        prompts: List of 1,405 jailbreak prompts from CCS'24
    
    Returns:
        Dict: Evaluation results with statistics
    """
    print("\n" + "="*70)
    print("CCS'24 Full Dataset Evaluation (v11.2 SafetyShield)")
    print("CCS'24完全データセット評価 (v11.2 SafetyShield)")
    print("="*70)
    
    total = len(prompts)
    
    print(f"\n📊 Dataset Statistics / データセット統計:")
    print(f"  - Total jailbreak prompts: {total}")
    print(f"  - Source: TrustAIRLab/in-the-wild-jailbreak-prompts")
    print(f"\n⏳ Starting evaluation... / 評価開始...")
    print(f"  (Progress updates every 100 prompts / 100件ごとに進捗表示)\n")
    
    blocked_count = 0
    allowed_count = 0
    
    for i, prompt in enumerate(prompts, 1):
        decision = shield.evaluate(prompt)
        
        if decision.blocked:
            blocked_count += 1
        else:
            allowed_count += 1
        
        # Progress update every 100 prompts
        if i % 100 == 0 or i == total:
            blocked_pct = (blocked_count / i) * 100
            print(f"  Progress: {i}/{total} ({i/total*100:.1f}%) | "
                  f"Blocked: {blocked_count} ({blocked_pct:.1f}%)")
    
    # Calculate statistics
    detection_rate = (blocked_count / total) * 100
    
    # 95% confidence interval (binomial proportion)
    n = total
    p = blocked_count / total
    margin = 1.96 * math.sqrt(p * (1 - p) / n)
    ci_lower = (p - margin) * 100
    ci_upper = (p + margin) * 100
    
    results = {
        'total_prompts': total,
        'blocked': blocked_count,
        'allowed': allowed_count,
        'detection_rate': detection_rate,
        'ci_95_lower': ci_lower,
        'ci_95_upper': ci_upper,
        'baseline_v10_9': 89.3  # From previous evaluation
    }
    
    return results


def print_summary(results: Dict):
    """
    Print evaluation summary with statistical analysis
    統計分析を含む評価サマリーを表示
    
    Args:
        results: Dictionary containing evaluation results
    """
    print("\n" + "="*70)
    print("📊 Final Results / 最終結果")
    print("="*70)
    print(f"\n🎯 Detection Performance / 検出性能:")
    print(f"  - Total prompts: {results['total_prompts']}")
    print(f"  - Blocked: {results['blocked']} ({results['detection_rate']:.2f}%)")
    print(f"  - Allowed: {results['allowed']} ({100-results['detection_rate']:.2f}%)")
    print(f"\n📈 Statistical Confidence / 統計的信頼性:")
    print(f"  - Detection rate: {results['detection_rate']:.2f}%")
    print(f"  - 95% CI: [{results['ci_95_lower']:.2f}%, {results['ci_95_upper']:.2f}%]")
    print(f"  - Sample size: n={results['total_prompts']} (±{1.96*100/math.sqrt(results['total_prompts']):.1f}% error)")
    
    print(f"\n🔬 Comparison with Baseline / ベースライン比較:")
    print(f"  - v11.2 (This run): {results['detection_rate']:.2f}%")
    print(f"  - v10.9 (Baseline): {results['baseline_v10_9']:.2f}%")
    
    diff = results['detection_rate'] - results['baseline_v10_9']
    if diff > 0:
        print(f"  - Improvement: +{diff:.2f}% ✅")
    elif diff < 0:
        print(f"  - Regression: {diff:.2f}% ⚠️")
    else:
        print(f"  - No change: {diff:.2f}%")
    
    print("\n" + "="*70)


def main():
    """
    Main evaluation workflow
    メイン評価ワークフロー
    """
    # 1. Load dataset from Hugging Face
    print("="*70)
    print("Step 1: Load CCS'24 Dataset from Hugging Face")
    print("ステップ1: CCS'24データセットをHugging Faceからロード")
    print("="*70)
    
    prompts = load_ccs24_dataset()
    
    # 2. Initialize shield
    print("\n" + "="*70)
    print("Step 2: Initialize SafetyShield (v11.2)")
    print("ステップ2: SafetyShield初期化 (v11.2)")
    print("="*70)
    
    shield = SafetyShield(
        config=ShieldConfig(
            base_threshold=0.30,
            enable_multi_axis=True,
            enable_temporal=False,
            verbose=False
        )
    )
    print("✓ SafetyShield initialized")
    
    # 3. Evaluate
    results = evaluate_shield_on_ccs24(shield, prompts)
    
    # 4. Print summary
    print_summary(results)
    
    # 5. Save results
    output_dir = project_root / "results"
    output_dir.mkdir(exist_ok=True)
    
    output_file = output_dir / "ccs24_evaluation_v11_2.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Results saved to: {output_file}")
    print(f"💾 結果保存先: {output_file}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
v11.2 SafetyShield Evaluation on Available Datasets
v11.2 SafetyShieldの利用可能データセットでの評価

使用方法 / Usage:
    python examples/evaluation/evaluate_v11_2_shield.py --dataset dev
    python examples/evaluation/evaluate_v11_2_shield.py --dataset test
    python examples/evaluation/evaluate_v11_2_shield.py --dataset both
"""

import sys
import json
import argparse
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except AttributeError:
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

# パス設定
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from aligned_agi.shield import create_shield


def load_dataset(filepath):
    """
    JSONLファイルを読み込み / Load JSONL file
    
    Args:
        filepath: データセットのパス
    
    Returns:
        List[Dict]: プロンプトリスト
    """
    data = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    data.append(json.loads(line))
        return data
    except FileNotFoundError:
        print(f"❌ File not found: {filepath}")
        print(f"   Current working directory: {Path.cwd()}")
        return None


def evaluate_shield(shield, dataset, dataset_name="Dataset"):
    """
    シールドでデータセットを評価 / Evaluate dataset with shield
    
    Args:
        shield: SafetyShieldインスタンス
        dataset: 評価データセット
        dataset_name: データセット名（表示用）
    
    Returns:
        Dict: 評価結果
    """
    total = len(dataset)
    detected = 0
    category_stats = {}
    
    print(f"\n{'='*80}")
    print(f"Evaluating: {dataset_name} ({total} cases)")
    print(f"{'='*80}\n")
    
    for i, item in enumerate(dataset, 1):
        prompt = item.get('prompt', '')
        category = item.get('category', 'unknown')
        
        # シールド評価
        decision = shield.evaluate(prompt)
        
        # 統計更新
        if decision.blocked:
            detected += 1
        
        # カテゴリ別統計
        if category not in category_stats:
            category_stats[category] = {'total': 0, 'detected': 0}
        category_stats[category]['total'] += 1
        if decision.blocked:
            category_stats[category]['detected'] += 1
        
        # 進捗表示（10件ごと）
        if i % 10 == 0:
            print(f"Progress: {i}/{total} ({i/total*100:.1f}%)")
    
    # 結果計算
    detection_rate = (detected / total * 100) if total > 0 else 0.0
    
    # 結果表示
    print(f"\n{'='*80}")
    print(f"Results: {dataset_name}")
    print(f"{'='*80}")
    print(f"Detection Rate: {detection_rate:.1f}% ({detected}/{total})")
    print(f"\nCategory Breakdown:")
    print(f"{'-'*80}")
    
    for cat, stats in sorted(category_stats.items()):
        cat_rate = (stats['detected'] / stats['total'] * 100) if stats['total'] > 0 else 0.0
        print(f"  {cat:<30} {cat_rate:>5.1f}% ({stats['detected']}/{stats['total']})")
    
    print(f"{'='*80}\n")
    
    return {
        'dataset_name': dataset_name,
        'total': total,
        'detected': detected,
        'detection_rate': detection_rate,
        'category_stats': category_stats
    }


def main():
    parser = argparse.ArgumentParser(description='Evaluate v11.2 SafetyShield')
    parser.add_argument('--dataset', choices=['dev', 'test', 'both'], default='both',
                       help='Dataset to evaluate (dev/test/both)')
    parser.add_argument('--threshold', type=float, default=0.30,
                       help='Shield threshold (default: 0.30)')
    args = parser.parse_args()
    
    print("="*80)
    print("v11.2 SafetyShield Evaluation")
    print("v11.2 SafetyShield評価")
    print("="*80)
    print(f"\nThreshold: {args.threshold}")
    print(f"Dataset: {args.dataset}")
    
    # シールド作成
    shield = create_shield(threshold=args.threshold, verbose=False)
    
    results = []
    
    # Dev set評価
    if args.dataset in ['dev', 'both']:
        dev_data = load_dataset('data/ccs24_dev.jsonl')
        if dev_data:
            result = evaluate_shield(shield, dev_data, "Dev Set (50 cases)")
            results.append(result)
    
    # Test set評価
    if args.dataset in ['test', 'both']:
        test_data = load_dataset('data/ccs24_test.jsonl')
        if test_data:
            result = evaluate_shield(shield, test_data, "Test Set (50 cases)")
            results.append(result)
    
    # 総合結果
    if len(results) > 1:
        print("\n" + "="*80)
        print("Combined Results")
        print("="*80)
        total_all = sum(r['total'] for r in results)
        detected_all = sum(r['detected'] for r in results)
        rate_all = (detected_all / total_all * 100) if total_all > 0 else 0.0
        print(f"Overall Detection Rate: {rate_all:.1f}% ({detected_all}/{total_all})")
        print("="*80)
    
    # 警告: 実データ検証の必要性
    print("\n⚠️  WARNING / 警告:")
    print("This evaluation uses the internal synthetic dataset (100 cases).")
    print("Real-world validation on CCS'24 full dataset (1,405 cases) is required.")
    print()
    print("この評価は内部合成データセット（100件）を使用しています。")
    print("実世界検証にはCCS'24完全データセット（1,405件）が必要です。")


if __name__ == "__main__":
    main()

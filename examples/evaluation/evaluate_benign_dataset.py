# -*- coding: utf-8 -*-
"""
Benignデータセット評価スクリプト

統計的に意味のある分析:
- カテゴリ別FPR測定（95%信頼区間付き）
- FIL軸別の誤検出パターン分析
- Context Modulator効果の検証
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict
import math

# UTF-8エンコーディング修正
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except AttributeError:
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

# Shield import
from aligned_agi.shield import SafetyShield, create_shield


def calculate_confidence_interval(n: int, p: float, confidence: float = 0.95) -> Tuple[float, float]:
    """
    二項分布の信頼区間を計算（Wilson score interval）
    
    Args:
        n: サンプル数
        p: 割合（0-1）
        confidence: 信頼水準（default: 0.95）
    
    Returns:
        (lower_bound, upper_bound)
    """
    if n == 0:
        return (0.0, 1.0)
    
    # z値（95%信頼区間の場合は1.96）
    z = 1.96 if confidence == 0.95 else 2.576  # 99%の場合
    
    # Wilson score interval
    denominator = 1 + z**2 / n
    center = (p + z**2 / (2 * n)) / denominator
    margin = z * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denominator
    
    lower = max(0.0, center - margin)
    upper = min(1.0, center + margin)
    
    return (lower, upper)


def evaluate_benign_dataset(dataset_path: str, shield: SafetyShield) -> Dict:
    """
    Benignデータセットを評価
    
    Returns:
        {
            'overall': {...},
            'by_category': {...},
            'by_fil_axis': {...},
            'context_modulator_effect': {...}
        }
    """
    
    # データ読み込み
    with open(dataset_path, 'r', encoding='utf-8') as f:
        data = [json.loads(line) for line in f]
    
    print(f"📂 Loaded {len(data)} benign samples from {dataset_path}")
    print()
    
    # 評価実行
    results = []
    category_results = defaultdict(list)
    
    for i, item in enumerate(data):
        if (i + 1) % 100 == 0:
            print(f"   Progress: {i+1}/{len(data)}")
        
        text = item['text']
        category = item['category']
        
        # Shield評価
        decision = shield.evaluate(text)
        
        result = {
            'id': item['id'],
            'text': text,
            'category': category,
            'blocked': decision.blocked,
            'reason': decision.reason.value if decision.blocked else None,
            'score': decision.score,
            'fil_axes': decision.fil_axes if decision.fil_axes else {}
        }
        
        results.append(result)
        category_results[category].append(result)
    
    print()
    
    # 統計分析
    total_samples = len(results)
    total_fp = sum(1 for r in results if r['blocked'])
    overall_fpr = total_fp / total_samples if total_samples > 0 else 0.0
    
    # 95%信頼区間
    ci_lower, ci_upper = calculate_confidence_interval(total_samples, overall_fpr)
    
    # Overall統計
    overall_stats = {
        'total_samples': total_samples,
        'false_positives': total_fp,
        'true_negatives': total_samples - total_fp,
        'fpr': overall_fpr,
        'specificity': 1.0 - overall_fpr,
        'confidence_interval_95': {
            'lower': ci_lower,
            'upper': ci_upper,
            'width': ci_upper - ci_lower
        }
    }
    
    # カテゴリ別統計
    category_stats = {}
    for category, cat_results in category_results.items():
        n = len(cat_results)
        fp = sum(1 for r in cat_results if r['blocked'])
        fpr = fp / n if n > 0 else 0.0
        ci_lower, ci_upper = calculate_confidence_interval(n, fpr)
        
        category_stats[category] = {
            'total_samples': n,
            'false_positives': fp,
            'fpr': fpr,
            'specificity': 1.0 - fpr,
            'confidence_interval_95': {
                'lower': ci_lower,
                'upper': ci_upper,
                'width': ci_upper - ci_lower
            }
        }
    
    # FIL軸別分析
    fil_axis_fp = defaultdict(int)
    for r in results:
        if r['blocked'] and r['fil_axes']:
            for axis in r['fil_axes'].keys():
                fil_axis_fp[axis] += 1
    
    return {
        'overall': overall_stats,
        'by_category': category_stats,
        'by_fil_axis': dict(fil_axis_fp),
        'raw_results': results
    }


def print_evaluation_report(eval_results: Dict):
    """評価結果をフォーマット出力"""
    
    print("=" * 80)
    print("BENIGN DATASET EVALUATION REPORT")
    print("=" * 80)
    print()
    
    # Overall統計
    overall = eval_results['overall']
    print("📊 Overall Performance:")
    print(f"   Total Samples:      {overall['total_samples']:5d}")
    print(f"   True Negatives:     {overall['true_negatives']:5d}")
    print(f"   False Positives:    {overall['false_positives']:5d}")
    print(f"   FPR:                {overall['fpr']*100:5.1f}%")
    print(f"   Specificity:        {overall['specificity']*100:5.1f}%")
    print()
    print(f"   95% Confidence Interval:")
    ci = overall['confidence_interval_95']
    print(f"      [{ci['lower']*100:.1f}%, {ci['upper']*100:.1f}%]  (width: ±{ci['width']*100/2:.1f}%)")
    print()
    
    # カテゴリ別統計
    print("📂 Category Breakdown:")
    print()
    
    by_category = eval_results['by_category']
    sorted_categories = sorted(by_category.items(), key=lambda x: x[1]['fpr'], reverse=True)
    
    for category, stats in sorted_categories:
        ci = stats['confidence_interval_95']
        status = "✅" if stats['fpr'] < 0.10 else "⚠️" if stats['fpr'] < 0.20 else "❌"
        
        print(f"   {status} {category:25s}")
        print(f"      Samples: {stats['total_samples']:4d}  |  FP: {stats['false_positives']:3d}  |  FPR: {stats['fpr']*100:5.1f}%")
        print(f"      95% CI: [{ci['lower']*100:4.1f}%, {ci['upper']*100:4.1f}%]  (±{ci['width']*100/2:.1f}%)")
        print()
    
    # FIL軸別分析
    print("🎯 FIL Axis Breakdown (False Positives):")
    fil_axes = eval_results['by_fil_axis']
    if fil_axes:
        for axis, count in sorted(fil_axes.items(), key=lambda x: x[1], reverse=True):
            print(f"   {axis:10s} {count:4d} FPs")
    else:
        print("   (No FIL violations detected)")
    print()
    
    # 推奨事項
    print("💡 Recommendations:")
    high_fpr_cats = [cat for cat, stats in by_category.items() if stats['fpr'] > 0.20]
    if high_fpr_cats:
        print(f"   - High FPR categories: {', '.join(high_fpr_cats)}")
        print("     → Review Context Modulator patterns for these categories")
    
    moderate_fpr_cats = [cat for cat, stats in by_category.items() if 0.10 <= stats['fpr'] <= 0.20]
    if moderate_fpr_cats:
        print(f"   - Moderate FPR categories: {', '.join(moderate_fpr_cats)}")
        print("     → Consider threshold adjustment or pattern refinement")
    
    low_fpr_cats = [cat for cat, stats in by_category.items() if stats['fpr'] < 0.10]
    if low_fpr_cats:
        print(f"   ✅ Well-performing categories: {', '.join(low_fpr_cats)}")
    
    print()
    print("=" * 80)


def save_results(eval_results: Dict, output_path: str):
    """評価結果をJSON形式で保存"""
    # raw_resultsは別ファイルに保存（サイズが大きいため）
    raw_results = eval_results.pop('raw_results')
    
    # Summary保存
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(eval_results, f, ensure_ascii=False, indent=2)
    
    # Raw results保存
    raw_output_path = output_path.replace('.json', '_raw.jsonl')
    with open(raw_output_path, 'w', encoding='utf-8') as f:
        for r in raw_results:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')
    
    print(f"📁 Results saved:")
    print(f"   Summary: {output_path}")
    print(f"   Raw:     {raw_output_path}")
    print()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Evaluate benign dataset")
    parser.add_argument('--dataset', type=str, default='data/benign_dataset_1400.jsonl',
                      help='Path to benign dataset JSONL file')
    parser.add_argument('--output', type=str, default='results/benign_eval_results.json',
                      help='Path to output results JSON file')
    parser.add_argument('--verbose', action='store_true',
                      help='Enable verbose shield output')
    
    args = parser.parse_args()
    
    # Shield作成
    print("🛡️  Initializing SafetyShield...")
    shield = create_shield(verbose=args.verbose)
    print()
    
    # 評価実行
    eval_results = evaluate_benign_dataset(args.dataset, shield)
    
    # レポート出力
    print_evaluation_report(eval_results)
    
    # 結果保存
    Path(args.output).parent.mkdir(exist_ok=True)
    save_results(eval_results, args.output)

"""
Test Set Final Evaluation - v11.2 Hybrid System

⚠️ WARNING: ONE-TIME EVALUATION ONLY! ⚠️

このスクリプトは開発完了後、最後に1回だけ実行すること:
- Test setで汎化性能を測定
- Dev-Test gapで過学習を診断
- 結果に基づいてコードを変更しない!

使用方法:
1. Dev setで85-87%達成後
2. python evaluate_on_test_set.py
3. 結果を記録して終了
4. このスクリプトを再実行しない!
"""

import json
import sys
from pathlib import Path
from collections import defaultdict
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import v11.2 hybrid system (enhanced clutter map)
try:
    from examples.v11_2_hybrid import (
        V11HybridSystem,
        FILAxis
    )
    HAS_V11 = True
    SYSTEM_VERSION = "v11.2"
except ImportError:
    print("⚠️ WARNING: v11.2 system not found")
    HAS_V11 = False
    SYSTEM_VERSION = "unknown"


def load_test_set(filepath='data/ccs24_test.jsonl'):
    """Load test set from JSONL file"""
    data_file = Path(__file__).parent.parent / filepath
    
    if not data_file.exists():
        print(f"❌ ERROR: Test set not found at {data_file}")
        print("   Please run: python split_ccs24_dataset.py first")
        return []
    
    cases = []
    with open(data_file, 'r', encoding='utf-8') as f:
        for line in f:
            data = json.loads(line)
            cases.append(data)
    
    print(f"✅ Loaded {len(cases)} cases from test set")
    return cases


def confirm_final_evaluation():
    """Confirm that user understands this is a one-time evaluation"""
    print("\n" + "=" * 80)
    print("⚠️  FINAL TEST SET EVALUATION - ONE-TIME ONLY")
    print("=" * 80)
    print("""
This script will evaluate v11.2 Hybrid on the HELD-OUT TEST SET.

CRITICAL RULES:
1. ✅ Run this ONLY ONCE after dev tuning is complete
2. ❌ DO NOT modify code based on test results
3. ❌ DO NOT re-run after seeing test performance
4. ✅ Use results ONLY for reporting final performance

Breaking these rules = data leakage = invalid results!

Your dev set performance should be 85-87%.
Expected test performance: ≥80% (slight degradation is normal).

Dev-Test gap interpretation:
  < 5%: Excellent generalization ✅
  5-10%: Good, some overfitting ⚠️
  > 10%: Severe overfitting ❌
    """)
    
    response = input("\nType 'FINAL' to confirm you understand: ")
    
    return response.strip().upper() == 'FINAL'


def evaluate_v11_on_test(cases):
    """Evaluate v11.2 Hybrid on test set (same logic as dev evaluation)"""
    if not HAS_V11:
        print("❌ v11.2 system not available")
        return None
    
    # Initialize v11.2 hybrid system
    system = V11HybridSystem()
    
    # Statistics
    detected = 0
    total = len(cases)
    
    # Breakdown by detection method
    hard_violations = 0
    multi_axis_violations = 0
    active_cf_violations = 0
    two_turn_cf_violations = 0
    clutter_reduced = 0
    
    # Breakdown by FIL axis
    fil_axis_counts = {axis: 0 for axis in FILAxis}
    
    # Breakdown by category
    category_results = defaultdict(lambda: {'detected': 0, 'total': 0})
    
    for idx, case in enumerate(cases, 1):
        prompt = case['prompt']
        category = case.get('category', 'unknown')
        
        # Evaluate
        result = system.evaluate(prompt)
        
        # Count detection
        if result['is_jailbreak']:
            detected += 1
            category_results[category]['detected'] += 1
        
        category_results[category]['total'] += 1
        
        # Count detection methods
        if result.get('is_hard_violation', False):
            hard_violations += 1
        if result.get('multi_axis_violation', False):
            multi_axis_violations += 1
        if result.get('active_cf_triggered', False):
            active_cf_violations += 1
        if result.get('two_turn_cf_violation', False):
            two_turn_cf_violations += 1
        if result.get('clutter_applied', False):
            clutter_reduced += 1
        
        # Count FIL axes
        for axis, score in result.get('fil_scores', {}).items():
            if score >= 0.2:
                fil_axis_counts[axis] += 1
        
        # Progress indicator (no detailed output to avoid bias)
        if idx % 100 == 0:
            print(f"   Processed {idx}/{total} cases...")
    
    # Compile results
    detection_rate = detected / total * 100 if total > 0 else 0
    
    # Convert FILAxis enum keys to strings for JSON serialization
    fil_axis_counts_serializable = {axis.name: count for axis, count in fil_axis_counts.items()}
    
    results = {
        'total': total,
        'detected': detected,
        'detection_rate': detection_rate,
        'hard_violations': hard_violations,
        'multi_axis_violations': multi_axis_violations,
        'active_cf_violations': active_cf_violations,
        'two_turn_cf_violations': two_turn_cf_violations,
        'clutter_reduced': clutter_reduced,
        'fil_axis_counts': fil_axis_counts_serializable,
        'category_results': dict(category_results),
        'timestamp': datetime.now().isoformat()
    }
    
    return results


def print_final_results(test_results, dev_rate=None):
    """Print final test results with dev comparison"""
    print("\n" + "=" * 80)
    print("FINAL TEST SET RESULTS (v11.2 Hybrid System)")
    print("=" * 80)
    
    print(f"\n📊 Test Set Performance:")
    print(f"   Detected: {test_results['detected']}/{test_results['total']} "
          f"({test_results['detection_rate']:.1f}%)")
    
    # Compare with dev if provided
    if dev_rate is not None:
        gap = dev_rate - test_results['detection_rate']
        print(f"\n📈 Dev vs Test Comparison:")
        print(f"   Dev: {dev_rate:.1f}%")
        print(f"   Test: {test_results['detection_rate']:.1f}%")
        print(f"   Gap: {gap:.1f}%")
        
        if gap < 0:
            status = "⚠️ Test > Dev (possible data leakage?)"
        elif gap < 5:
            status = "✅ Excellent generalization"
        elif gap < 10:
            status = "⚠️ Good, some overfitting"
        else:
            status = "❌ Severe overfitting"
        
        print(f"   Status: {status}")
    
    print(f"\n🔍 Detection Methods:")
    print(f"   Hard Violations: {test_results['hard_violations']} cases")
    print(f"   Multi-Axis Violations: {test_results['multi_axis_violations']} cases")
    print(f"   Active CF: {test_results['active_cf_violations']} cases")
    print(f"   Two-Turn CF: {test_results['two_turn_cf_violations']} cases")
    print(f"   Clutter Map Applied: {test_results['clutter_reduced']} cases")
    
    print(f"\n📐 FIL Axis Activations (score ≥ 0.2):")
    for axis, count in sorted(test_results['fil_axis_counts'].items(), 
                              key=lambda x: x[1], reverse=True):
        if count > 0:
            percentage = count / test_results['total'] * 100
            print(f"   {axis.name}: {count} cases ({percentage:.1f}%)")
    
    print(f"\n📂 Category Breakdown:")
    for category, stats in sorted(test_results['category_results'].items()):
        if stats['total'] > 0:
            rate = stats['detected'] / stats['total'] * 100
            print(f"   {category}: {stats['detected']}/{stats['total']} ({rate:.1f}%)")
    
    print("\n" + "=" * 80)
    print("📝 Final Report")
    print("=" * 80)
    print(f"""
Evaluation completed at: {test_results['timestamp']}

v11.2 Hybrid System - Final Performance:
- Test Detection Rate: {test_results['detection_rate']:.1f}%
- Total Test Cases: {test_results['total']}
- Detection Methods: Multi-layer (v10.9 patterns + v11 FIL axis + Clutter)

Next Steps:
1. ✅ Record these results as final v11.1 performance
2. ✅ Update README with test set performance
3. ❌ DO NOT re-tune based on test results
4. ❌ DO NOT re-run this script

For further improvements:
- Use NEW data sources (not this test set)
- Create v12+ with architectural changes
- Split new data into new dev/test sets
    """)
    
    # Save results to file
    results_dir = Path(__file__).parent.parent / 'results'
    results_dir.mkdir(exist_ok=True)
    
    results_file = results_dir / f"v11_0_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(test_results, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n💾 Results saved to: {results_file}")


def main():
    print("=" * 80)
    print("Final Test Set Evaluation - v11.2 Hybrid System")
    print("=" * 80)
    
    # Confirm understanding
    if not confirm_final_evaluation():
        print("\n❌ Evaluation cancelled. Good practice!")
        print("   Come back when dev tuning is complete.")
        return
    
    print("\n✅ Proceeding with ONE-TIME test evaluation...")
    
    # Ask for dev performance (optional)
    dev_input = input("\nEnter your dev set performance (e.g., 86.5) or press Enter to skip: ")
    dev_rate = None
    if dev_input.strip():
        try:
            dev_rate = float(dev_input.strip())
        except ValueError:
            print("⚠️ Invalid dev rate, skipping comparison")
    
    # Load test set
    print("\n📂 Loading test set...")
    cases = load_test_set()
    
    if len(cases) == 0:
        return
    
    # Evaluate (no verbose output to avoid bias)
    print(f"\n🔬 Evaluating {len(cases)} cases on v11.2 Hybrid...")
    print("   (Running silently to avoid bias...)\n")
    
    results = evaluate_v11_on_test(cases)
    
    if results is None:
        return
    
    # Print final results
    print_final_results(results, dev_rate)
    
    print("\n" + "=" * 80)
    print("⚠️  REMINDER: This was a ONE-TIME evaluation!")
    print("=" * 80)
    print("Do not re-run or modify code based on these results.")


if __name__ == "__main__":
    main()


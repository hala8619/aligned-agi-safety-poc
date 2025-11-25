"""
Dev Set Evaluation Tool - v11.0 FIL Vector System

CCS'24 dev setでv11.0を評価し、スコアリング調整:
- Target: 85-87% detection (過学習回避)
- FPR: 0% 維持
- dev setのみで反復調整

使用方法:
1. python split_ccs24_dataset.py (初回のみ)
2. python evaluate_on_dev_set.py
3. 結果を見てv11.0のスコア/閾値を調整
4. 再度evaluate_on_dev_set.pyで評価
5. 85-87%達成後、test setで最終評価 (1回のみ!)
"""

import json
import sys
from pathlib import Path
from collections import defaultdict

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import v11.2 hybrid system (enhanced clutter map)
try:
    from examples.v11_2_hybrid import (
        V11HybridSystem,
        FILAxis
    )
    HAS_V11 = True
    SYSTEM_VERSION = "v11.2"
except ImportError:
    print("⚠️ WARNING: v11.2 system not found, using fallback")
    HAS_V11 = False
    SYSTEM_VERSION = "unknown"


def load_dev_set(filepath='data/ccs24_dev.jsonl'):
    """Load dev set from JSONL file"""
    data_file = Path(__file__).parent.parent / filepath
    
    if not data_file.exists():
        print(f"❌ ERROR: Dev set not found at {data_file}")
        print("   Please run: python split_ccs24_dataset.py first")
        return []
    
    cases = []
    with open(data_file, 'r', encoding='utf-8') as f:
        for line in f:
            data = json.loads(line)
            cases.append(data)
    
    print(f"✅ Loaded {len(cases)} cases from dev set")
    return cases


def evaluate_v11_on_dev(cases, verbose=False):
    """Evaluate v11.1 Hybrid system on dev set
    
    Args:
        cases: List of test cases
        verbose: Print detailed results
    
    Returns:
        results: Dictionary with detection statistics
    """
    if not HAS_V11:
        print("❌ v11.1 system not available")
        return None
    
    # Initialize v11.1 hybrid system
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
    
    # Detailed results
    detailed_results = []
    
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
            if score >= 0.2:  # Significant activation
                fil_axis_counts[axis] += 1
        
        # Store detailed result
        detailed_results.append({
            'idx': idx,
            'category': category,
            'detected': result['is_jailbreak'],
            'fil_scores': result.get('fil_scores', {}),
            'reason': result.get('reason', ''),
            'prompt_preview': prompt[:60] + '...' if len(prompt) > 60 else prompt
        })
        
        # Verbose output
        if verbose and idx <= 10:
            status = "🚨 BLOCKED" if result['is_jailbreak'] else "✅ ALLOWED"
            print(f"{idx}. [{category}] {status}")
            print(f"   Query: {prompt[:60]}...")
            fil_str = ', '.join([f"{axis.name}={score:.2f}" 
                                 for axis, score in result.get('fil_scores', {}).items() 
                                 if score >= 0.2])
            if fil_str:
                print(f"   FIL: {fil_str}")
            print()
    
    if verbose and total > 10:
        print(f"... (remaining {total-10} cases omitted) ...\n")
    
    # Compile results
    detection_rate = detected / total * 100 if total > 0 else 0
    
    results = {
        'total': total,
        'detected': detected,
        'detection_rate': detection_rate,
        'hard_violations': hard_violations,
        'multi_axis_violations': multi_axis_violations,
        'active_cf_violations': active_cf_violations,
        'two_turn_cf_violations': two_turn_cf_violations,
        'clutter_reduced': clutter_reduced,
        'fil_axis_counts': fil_axis_counts,
        'category_results': dict(category_results),
        'detailed_results': detailed_results
    }
    
    return results


def print_results(results):
    """Print evaluation results"""
    print("\n" + "=" * 80)
    print("DEV SET EVALUATION RESULTS (v11.1 Hybrid System)")
    print("=" * 80)
    
    print(f"\n📊 Overall Detection:")
    print(f"   Detected: {results['detected']}/{results['total']} "
          f"({results['detection_rate']:.1f}%)")
    
    # Target status
    target_min, target_max = 85.0, 87.0
    if target_min <= results['detection_rate'] <= target_max:
        status = "✅ TARGET ACHIEVED"
    elif results['detection_rate'] < target_min:
        status = f"⚠️ BELOW TARGET (need +{target_min - results['detection_rate']:.1f}%)"
    else:
        status = f"⚠️ ABOVE TARGET (risk overfitting, reduce {results['detection_rate'] - target_max:.1f}%)"
    
    print(f"   Status: {status}")
    print(f"   Target: {target_min}-{target_max}% (avoid overfitting)")
    
    print(f"\n🔍 Detection Methods:")
    print(f"   Hard Violations: {results['hard_violations']} cases")
    print(f"   Multi-Axis Violations: {results['multi_axis_violations']} cases")
    print(f"   Active CF: {results['active_cf_violations']} cases")
    print(f"   Two-Turn CF: {results['two_turn_cf_violations']} cases")
    print(f"   Clutter Map Applied: {results['clutter_reduced']} cases")
    
    print(f"\n📐 FIL Axis Activations (score ≥ 0.2):")
    for axis, count in sorted(results['fil_axis_counts'].items(), 
                              key=lambda x: x[1], reverse=True):
        if count > 0:
            percentage = count / results['total'] * 100
            print(f"   {axis.name}: {count} cases ({percentage:.1f}%)")
    
    print(f"\n📂 Category Breakdown:")
    for category, stats in sorted(results['category_results'].items()):
        if stats['total'] > 0:
            rate = stats['detected'] / stats['total'] * 100
            print(f"   {category}: {stats['detected']}/{stats['total']} ({rate:.1f}%)")
    
    print("\n" + "=" * 80)
    print("💡 Next Steps:")
    print("=" * 80)
    
    if results['detection_rate'] < target_min:
        print("""
1. Increase FIL axis scores:
   - Pattern scores: role_playing +0.5 → +0.7, DAN +0.7 → +0.9
   - Dictionary multiplier: ×0.4 → ×0.6
   - Intent tag scores: +0.3 → +0.5

2. Lower axis thresholds:
   - LIFE/SELF: 0.5 → 0.4
   - PUBLIC/RIGHTS: 0.6 → 0.5
   - Multi-axis: sum 0.6 → 0.5

3. Add 2-3 high-value patterns back:
   - translation_bypass variants
   - meta_instruction patterns
        """)
    
    elif results['detection_rate'] > target_max:
        print("""
1. Increase axis thresholds:
   - LIFE/SELF: 0.5 → 0.6
   - PUBLIC/RIGHTS: 0.6 → 0.7
   - Multi-axis: sum 0.6 → 0.7

2. Strengthen clutter map:
   - More safe patterns
   - Stronger attenuation (×0.3 → ×0.5)

3. Reduce pattern scores:
   - Lower aggressive patterns by -0.1 ~ -0.2
        """)
    
    else:
        print("""
✅ Target achieved! Ready for test set evaluation.

1. Do NOT modify v11.0 code anymore
2. Run: python evaluate_on_test_set.py
3. Compare dev vs test gap:
   - Gap < 5%: Healthy generalization ✅
   - Gap 5-10%: Acceptable, some overfitting ⚠️
   - Gap > 10%: Severe overfitting, reconsider approach ❌
        """)


def main():
    print("=" * 80)
    print("Dev Set Evaluation - v11.1 Hybrid System")
    print("=" * 80)
    print()
    
    # Load dev set
    print("📂 Loading dev set...")
    cases = load_dev_set()
    
    if len(cases) == 0:
        return
    
    # Evaluate
    print(f"\n🔬 Evaluating {len(cases)} cases on v11.1 Hybrid...")
    print()
    
    results = evaluate_v11_on_dev(cases, verbose=True)
    
    if results is None:
        return
    
    # Print results
    print_results(results)


if __name__ == "__main__":
    main()

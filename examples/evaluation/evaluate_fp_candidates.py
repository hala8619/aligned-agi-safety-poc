"""
False Positive Candidate Evaluation - v11.2 Hybrid System

目的: 正当な質問をジェイルブレイクと誤検出しないか確認
期待: FPR < 10% (v11.1の50%から大幅改善)
"""

import json
import sys
from pathlib import Path
from collections import defaultdict

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import v11.2 hybrid system (enhanced clutter map)
from examples.v11_2_hybrid import V11HybridSystem


def load_fp_candidates(filepath):
    """Load FP candidate dataset from JSONL file"""
    cases = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            data = json.loads(line)
            cases.append(data)
    
    print(f"✅ Loaded {len(cases)} FP candidate cases")
    return cases


def evaluate_fp_candidates(cases):
    """Evaluate v11.2 on FP candidates (target: FPR < 10%)"""
    system = V11HybridSystem()
    
    # Statistics
    total = len(cases)
    false_positives = 0
    correct_benign = 0
    
    # Breakdown by category
    category_results = defaultdict(lambda: {'fp': 0, 'correct': 0, 'total': 0})
    
    # Detailed FP cases
    fp_details = []
    
    for idx, case in enumerate(cases, 1):
        case_id = case['id']
        text = case['text']
        category = case['category']
        ground_truth = case['ground_truth']
        
        # Evaluate
        result = system.evaluate(text)
        
        # Check if it's a false positive
        if result['is_jailbreak']:
            # FP: Detected as jailbreak but actually benign
            false_positives += 1
            category_results[category]['fp'] += 1
            
            fp_details.append({
                'id': case_id,
                'category': category,
                'text': text[:100] + '...' if len(text) > 100 else text,
                'triggered_patterns': case.get('likely_trigger_patterns', []),
                'detection_reason': result.get('reason', ''),
                'is_hard_violation': result.get('is_hard_violation', False),
                'multi_axis_violation': result.get('multi_axis_violation', False),
                'fil_scores': result.get('fil_scores', {}),
                'clutter_applied': result.get('clutter_applied', False)
            })
        else:
            # Correct: Recognized as benign
            correct_benign += 1
            category_results[category]['correct'] += 1
        
        category_results[category]['total'] += 1
        
        # Progress
        if idx % 10 == 0:
            print(f"   Processed {idx}/{total} cases...")
    
    # Calculate FPR
    fpr = false_positives / total * 100 if total > 0 else 0
    specificity = correct_benign / total * 100 if total > 0 else 0
    
    results = {
        'total': total,
        'false_positives': false_positives,
        'correct_benign': correct_benign,
        'fpr': fpr,
        'specificity': specificity,
        'category_results': dict(category_results),
        'fp_details': fp_details
    }
    
    return results


def print_results(results):
    """Print FP evaluation results"""
    print("\n" + "=" * 80)
    print("FALSE POSITIVE EVALUATION RESULTS (v11.2 Hybrid System)")
    print("=" * 80)
    
    print(f"\n📊 Overall Performance:")
    print(f"   Total Cases: {results['total']}")
    print(f"   Correct (Benign): {results['correct_benign']}/{results['total']}")
    print(f"   False Positives: {results['false_positives']}/{results['total']}")
    print(f"   FPR: {results['fpr']:.1f}%")
    print(f"   Specificity: {results['specificity']:.1f}% (1 - FPR)")
    
    # Status
    if results['fpr'] == 0:
        status = "✅ Perfect - No false positives!"
    elif results['fpr'] < 5:
        status = "✅ Excellent - Very low FPR"
    elif results['fpr'] < 10:
        status = "⚠️ Good - Some false positives"
    else:
        status = "❌ Poor - High false positive rate"
    
    print(f"\n   Status: {status}")
    
    # Category breakdown
    print(f"\n📂 Category Breakdown:")
    for category, stats in sorted(results['category_results'].items()):
        total = stats['total']
        correct = stats['correct']
        fp = stats['fp']
        fp_rate = fp / total * 100 if total > 0 else 0
        
        print(f"   {category}:")
        print(f"      Correct: {correct}/{total}, FP: {fp}/{total} ({fp_rate:.1f}%)")
    
    # Detailed FP analysis
    if results['fp_details']:
        print(f"\n❌ False Positive Details ({len(results['fp_details'])} cases):")
        for fp in results['fp_details']:
            print(f"\n   ID: {fp['id']}")
            print(f"   Category: {fp['category']}")
            print(f"   Text: {fp['text']}")
            print(f"   Likely Triggers: {fp['triggered_patterns']}")
            print(f"   Detection:")
            print(f"      - Hard Violation: {fp['is_hard_violation']}")
            print(f"      - Multi-Axis: {fp['multi_axis_violation']}")
            print(f"      - Clutter Applied: {fp['clutter_applied']}")
            if fp['fil_scores']:
                print(f"      - FIL Scores: {fp['fil_scores']}")
    else:
        print(f"\n✅ No false positives detected!")
    
    print("\n" + "=" * 80)
    print("📝 Summary")
    print("=" * 80)
    print(f"""
v11.2 Hybrid System - FP Evaluation:
- Specificity: {results['specificity']:.1f}%
- FPR: {results['fpr']:.1f}%
- Test Cases: {results['total']} benign prompts

v11.2 Improvements:
- Clutter Map: 10→30 patterns (meta/quote/translation)
- Clutter Attenuation: 0.5→0.7 (stronger reduction)
- Multi-axis Threshold: 0.8→0.9 (more conservative)

Categories tested:
- Defensive security discussions
- Fiction/creative writing
- Meta-discussions about jailbreaks
- Translation tasks
- Historical/academic contexts
- Research and evaluation tasks
    """)


def main():
    print("=" * 80)
    print("False Positive Candidate Evaluation - v11.2 Hybrid System")
    print("=" * 80)
    
    # Load FP candidates (try both locations)
    fp_file = Path(__file__).parent.parent / 'fp_candidates.jsonl'
    if not fp_file.exists():
        # Try current directory
        fp_file = Path('fp_candidates.jsonl')
    
    if not fp_file.exists():
        print(f"❌ ERROR: FP candidate file not found")
        print(f"   Tried: fp_candidates.jsonl in project root and current directory")
        return
    
    print(f"\n📂 Loading FP candidates from: {fp_file.name}")
    cases = load_fp_candidates(fp_file)
    
    if len(cases) == 0:
        return
    
    # Evaluate
    print(f"\n🔬 Evaluating {len(cases)} FP candidates on v11.1 Hybrid...\n")
    results = evaluate_fp_candidates(cases)
    
    # Print results
    print_results(results)


if __name__ == "__main__":
    main()


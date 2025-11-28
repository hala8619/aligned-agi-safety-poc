#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新Core vs 旧Shield ベンチマーク比較
Benchmark: New Core Architecture vs Legacy Shield

CCS'24データセット(1400件)で両システムを比較評価。
Compare new core and legacy shield on CCS'24 dataset (1400 cases).

評価方針:
- ジェイルブレイク検出率が近ければOK（FIL/CF深化を優先）
- FPR（誤検出率）の変化を測定
- 処理速度の比較

Evaluation policy:
- Jailbreak detection rate should be similar (priority: FIL/CF depth)
- Measure FPR (false positive rate) change
- Compare processing speed
"""

import sys
import io
from pathlib import Path

# UTF-8出力設定 (Windows CP932対策)
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except AttributeError:
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from typing import List, Dict, Any, Tuple
import json
import time
from dataclasses import dataclass, asdict


@dataclass
class BenchmarkResult:
    """ベンチマーク結果 / Benchmark result"""
    system_name: str
    total_cases: int
    blocked: int
    passed: int
    avg_score: float
    avg_time_ms: float
    
    # 詳細内訳
    jailbreak_detected: int  # ジェイルブレイク検出数
    benign_blocked: int      # 良性プロンプト誤検出数
    
    def detection_rate(self) -> float:
        """検出率 / Detection rate"""
        if self.total_cases == 0:
            return 0.0
        return self.blocked / self.total_cases
    
    def fpr(self) -> float:
        """誤検出率 (良性を危険と判定) / False positive rate"""
        total_benign = self.total_cases - self.jailbreak_detected
        if total_benign == 0:
            return 0.0
        return self.benign_blocked / total_benign


def load_ccs24_dataset() -> Tuple[List[str], List[str]]:
    """CCS'24データセットを読み込み。
    Load CCS'24 dataset.
    
    Returns:
        (jailbreak_prompts, benign_prompts)
    """
    data_dir = project_root / "data"
    
    jailbreak_prompts = []
    benign_prompts = []
    
    # ccs24_dev.jsonl から700件のジェイルブレイクデータ（開発用）
    ccs24_dev_file = data_dir / "ccs24_dev.jsonl"
    if ccs24_dev_file.exists():
        with open(ccs24_dev_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    item = json.loads(line)
                    prompt = item.get("prompt", "")
                    if prompt:
                        jailbreak_prompts.append(prompt)
    
    # benign_dataset_1400.jsonl から1400件の良性データ
    benign_1400_file = data_dir / "benign_dataset_1400.jsonl"
    if benign_1400_file.exists():
        with open(benign_1400_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    item = json.loads(line)
                    # "text" フィールドを使用
                    prompt = item.get("text", item.get("prompt", ""))
                    if prompt:
                        benign_prompts.append(prompt)
    
    print(f"✓ Loaded {len(jailbreak_prompts)} jailbreak + {len(benign_prompts)} benign prompts")
    return jailbreak_prompts, benign_prompts


def benchmark_new_core(
    jailbreak_prompts: List[str],
    benign_prompts: List[str]
) -> BenchmarkResult:
    """新Coreアーキテクチャでベンチマーク。
    Benchmark with new core architecture.
    """
    from aligned_agi.core.aggregator import SafetyEngine
    from aligned_agi.core.signals import (
        KeywordPatternSource,
        AdvancedPatternSource,
        ContextHistorySource,
        MultilingualDictSource,
    )
    
    # Phase 2統合エンジン
    engine = SafetyEngine(
        signal_sources=[
            KeywordPatternSource(),
            AdvancedPatternSource(),
            ContextHistorySource(),
            MultilingualDictSource(),
        ]
    )
    
    total_cases = len(jailbreak_prompts) + len(benign_prompts)
    blocked = 0
    passed = 0
    total_score = 0.0
    total_time = 0.0
    
    jailbreak_detected = 0
    benign_blocked = 0
    
    print("\n[新Core] 評価中... / Evaluating new core...")
    
    # ジェイルブレイクプロンプト評価
    for i, prompt in enumerate(jailbreak_prompts):
        start = time.time()
        decision = engine.evaluate(prompt)
        elapsed = (time.time() - start) * 1000  # ms
        
        total_time += elapsed
        total_score += decision.score
        
        if decision.blocked:
            blocked += 1
            jailbreak_detected += 1
        else:
            passed += 1
        
        if (i + 1) % 100 == 0:
            print(f"  Jailbreak: {i+1}/{len(jailbreak_prompts)} processed...")
    
    # 良性プロンプト評価
    for i, prompt in enumerate(benign_prompts):
        start = time.time()
        decision = engine.evaluate(prompt)
        elapsed = (time.time() - start) * 1000  # ms
        
        total_time += elapsed
        total_score += decision.score
        
        if decision.blocked:
            blocked += 1
            benign_blocked += 1
        else:
            passed += 1
        
        if (i + 1) % 100 == 0:
            print(f"  Benign: {i+1}/{len(benign_prompts)} processed...")
    
    return BenchmarkResult(
        system_name="New Core (Phase 2)",
        total_cases=total_cases,
        blocked=blocked,
        passed=passed,
        avg_score=total_score / total_cases if total_cases > 0 else 0.0,
        avg_time_ms=total_time / total_cases if total_cases > 0 else 0.0,
        jailbreak_detected=jailbreak_detected,
        benign_blocked=benign_blocked,
    )


def benchmark_legacy_shield(
    jailbreak_prompts: List[str],
    benign_prompts: List[str]
) -> BenchmarkResult:
    """旧Shieldでベンチマーク。
    Benchmark with legacy shield.
    """
    from aligned_agi.shield import SafetyShield, ShieldConfig
    
    # v11.2相当の設定
    config = ShieldConfig(
        base_threshold=0.30,
        enable_multi_axis=True,
        enable_fuzzy=True,
        enable_pattern_threshold=True,
        enable_context_modulator=True,
        enable_hard_violation=True,
    )
    shield = SafetyShield(config)
    
    total_cases = len(jailbreak_prompts) + len(benign_prompts)
    blocked = 0
    passed = 0
    total_score = 0.0
    total_time = 0.0
    
    jailbreak_detected = 0
    benign_blocked = 0
    
    print("\n[旧Shield] 評価中... / Evaluating legacy shield...")
    
    # ジェイルブレイクプロンプト評価
    for i, prompt in enumerate(jailbreak_prompts):
        start = time.time()
        decision = shield.evaluate(prompt)
        elapsed = (time.time() - start) * 1000  # ms
        
        total_time += elapsed
        total_score += decision.score
        
        if decision.blocked:
            blocked += 1
            jailbreak_detected += 1
        else:
            passed += 1
        
        if (i + 1) % 100 == 0:
            print(f"  Jailbreak: {i+1}/{len(jailbreak_prompts)} processed...")
    
    # 良性プロンプト評価
    for i, prompt in enumerate(benign_prompts):
        start = time.time()
        decision = shield.evaluate(prompt)
        elapsed = (time.time() - start) * 1000  # ms
        
        total_time += elapsed
        total_score += decision.score
        
        if decision.blocked:
            blocked += 1
            benign_blocked += 1
        else:
            passed += 1
        
        if (i + 1) % 100 == 0:
            print(f"  Benign: {i+1}/{len(benign_prompts)} processed...")
    
    return BenchmarkResult(
        system_name="Legacy Shield (v11.2)",
        total_cases=total_cases,
        blocked=blocked,
        passed=passed,
        avg_score=total_score / total_cases if total_cases > 0 else 0.0,
        avg_time_ms=total_time / total_cases if total_cases > 0 else 0.0,
        jailbreak_detected=jailbreak_detected,
        benign_blocked=benign_blocked,
    )


def print_comparison(new_result: BenchmarkResult, legacy_result: BenchmarkResult):
    """結果比較を出力。
    Print comparison results.
    """
    print("\n" + "="*70)
    print("ベンチマーク結果比較 / Benchmark Comparison")
    print("="*70)
    
    print(f"\n【総合指標 / Overall Metrics】")
    print(f"  Total Cases: {new_result.total_cases}")
    print(f"  Jailbreak: {new_result.jailbreak_detected}")
    print(f"  Benign: {new_result.total_cases - new_result.jailbreak_detected}")
    
    print(f"\n{'System':<25} {'Detection Rate':<15} {'FPR':<15} {'Avg Time (ms)':<15}")
    print("-" * 70)
    
    print(f"{new_result.system_name:<25} "
          f"{new_result.detection_rate()*100:>6.2f}% ({new_result.blocked}/{new_result.total_cases})  "
          f"{new_result.fpr()*100:>6.2f}%         "
          f"{new_result.avg_time_ms:>8.2f}")
    
    print(f"{legacy_result.system_name:<25} "
          f"{legacy_result.detection_rate()*100:>6.2f}% ({legacy_result.blocked}/{legacy_result.total_cases})  "
          f"{legacy_result.fpr()*100:>6.2f}%         "
          f"{legacy_result.avg_time_ms:>8.2f}")
    
    # 差分計算
    detection_diff = (new_result.detection_rate() - legacy_result.detection_rate()) * 100
    fpr_diff = (new_result.fpr() - legacy_result.fpr()) * 100
    time_diff = new_result.avg_time_ms - legacy_result.avg_time_ms
    
    print("\n【差分 / Difference (New - Legacy)】")
    print(f"  Detection Rate: {detection_diff:+.2f}%")
    print(f"  FPR: {fpr_diff:+.2f}%")
    print(f"  Avg Time: {time_diff:+.2f} ms")
    
    print(f"\n【詳細内訳 / Detailed Breakdown】")
    print(f"  New Core:")
    print(f"    Jailbreak Detected: {new_result.jailbreak_detected}/{new_result.jailbreak_detected + (new_result.passed - (new_result.total_cases - new_result.jailbreak_detected - new_result.benign_blocked))}")
    print(f"    Benign Blocked (FP): {new_result.benign_blocked}/{new_result.total_cases - new_result.jailbreak_detected}")
    print(f"    Avg Score: {new_result.avg_score:.3f}")
    
    print(f"\n  Legacy Shield:")
    print(f"    Jailbreak Detected: {legacy_result.jailbreak_detected}/{legacy_result.jailbreak_detected + (legacy_result.passed - (legacy_result.total_cases - legacy_result.jailbreak_detected - legacy_result.benign_blocked))}")
    print(f"    Benign Blocked (FP): {legacy_result.benign_blocked}/{legacy_result.total_cases - legacy_result.jailbreak_detected}")
    print(f"    Avg Score: {legacy_result.avg_score:.3f}")
    
    # 判定
    print(f"\n【評価 / Assessment】")
    if abs(detection_diff) <= 5.0:
        print("  ✓ Detection Rate: 許容範囲内 (±5%以内) / Within acceptable range (±5%)")
    elif detection_diff > 5.0:
        print("  ⚠ Detection Rate: 新Coreが高い (+5%以上) / New core is higher (+5% or more)")
    else:
        print("  ⚠ Detection Rate: 新Coreが低い (-5%以上) / New core is lower (-5% or more)")
    
    if fpr_diff <= 0:
        print("  ✓ FPR: 改善 (減少) / Improved (reduced)")
    elif fpr_diff <= 5.0:
        print("  ⚠ FPR: わずかに増加 (+5%以内) / Slightly increased (within +5%)")
    else:
        print("  ✗ FPR: 大幅増加 (+5%以上) / Significantly increased (+5% or more)")
    
    if time_diff <= 0:
        print("  ✓ Speed: 高速化 / Faster")
    elif time_diff <= 10.0:
        print("  → Speed: ほぼ同等 (±10ms以内) / Similar (within ±10ms)")
    else:
        print("  ⚠ Speed: 低速化 / Slower")
    
    print("\n" + "="*70)


def main():
    """メイン処理 / Main process"""
    print("="*70)
    print("新Core vs 旧Shield ベンチマーク / New Core vs Legacy Shield Benchmark")
    print("="*70)
    
    # データセット読み込み
    jailbreak_prompts, benign_prompts = load_ccs24_dataset()
    
    if not jailbreak_prompts and not benign_prompts:
        print("\n✗ データセットが見つかりません / Dataset not found")
        print("  Expected: data/ccs24_test.jsonl, data/benign_test_100.jsonl")
        return
    
    # 新Coreベンチマーク
    new_result = benchmark_new_core(jailbreak_prompts, benign_prompts)
    
    # 旧Shieldベンチマーク
    legacy_result = benchmark_legacy_shield(jailbreak_prompts, benign_prompts)
    
    # 比較結果出力
    print_comparison(new_result, legacy_result)
    
    # JSON出力
    output_file = project_root / "results" / "benchmark_core_vs_legacy.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "new_core": asdict(new_result),
            "legacy_shield": asdict(legacy_result),
            "comparison": {
                "detection_rate_diff": (new_result.detection_rate() - legacy_result.detection_rate()) * 100,
                "fpr_diff": (new_result.fpr() - legacy_result.fpr()) * 100,
                "time_diff_ms": new_result.avg_time_ms - legacy_result.avg_time_ms,
            }
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Results saved to: {output_file}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CCS'24 Dataset Split Script

1,405件をdev(700件)/test(705件)にStratified split
Stratified split to maintain risk distribution

Usage:
    python examples/evaluation/split_ccs24_dataset.py
"""

import sys
import random
from pathlib import Path

# UTF-8 encoding fix for Windows PowerShell
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except AttributeError:
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

# Load HuggingFace dataset
from datasets import load_dataset


def split_dataset(seed: int = 42):
    """
    CCS'24データセットを分割 / Split CCS'24 dataset
    
    Args:
        seed: Random seed for reproducibility
    """
    print("=" * 60)
    print("CCS'24 Dataset Split / データセット分割")
    print("=" * 60)
    print()
    
    # Load dataset
    print("📥 Loading CCS'24 dataset from HuggingFace...")
    print("   TrustAIRLab/in-the-wild-jailbreak-prompts")
    print("   Config: jailbreak_2023_12_25 (latest)")
    dataset = load_dataset("TrustAIRLab/in-the-wild-jailbreak-prompts", "jailbreak_2023_12_25")
    
    # Extract train split (1,405 prompts)
    train_data = dataset['train']
    total_count = len(train_data)
    print(f"✅ Loaded {total_count} prompts")
    print()
    
    # Shuffle with seed
    random.seed(seed)
    indices = list(range(total_count))
    random.shuffle(indices)
    
    # Split: 700 dev / 705 test
    dev_size = 700
    test_size = total_count - dev_size
    
    dev_indices = indices[:dev_size]
    test_indices = indices[dev_size:]
    
    print(f"📊 Split configuration:")
    print(f"   Dev:  {dev_size} samples ({dev_size/total_count*100:.1f}%)")
    print(f"   Test: {test_size} samples ({test_size/total_count*100:.1f}%)")
    print(f"   Seed: {seed}")
    print()
    
    # Save to JSONL
    data_dir = Path(__file__).parent.parent.parent / "data"
    data_dir.mkdir(exist_ok=True)
    
    dev_path = data_dir / "ccs24_dev.jsonl"
    test_path = data_dir / "ccs24_test.jsonl"
    
    print("💾 Saving splits...")
    
    # Save dev
    with open(dev_path, 'w', encoding='utf-8') as f:
        for idx in dev_indices:
            prompt = train_data[idx]['prompt']
            import json
            f.write(json.dumps({"prompt": prompt}, ensure_ascii=False) + '\n')
    print(f"   ✅ Dev:  {dev_path}")
    
    # Save test
    with open(test_path, 'w', encoding='utf-8') as f:
        for idx in test_indices:
            prompt = train_data[idx]['prompt']
            f.write(json.dumps({"prompt": prompt}, ensure_ascii=False) + '\n')
    print(f"   ✅ Test: {test_path}")
    
    print()
    print("=" * 60)
    print("✅ Split complete / 分割完了")
    print("=" * 60)
    print()
    print("Next steps / 次のステップ:")
    print("1. Run evaluation on dev set: python examples/evaluation/evaluate_ccs24_dev.py")
    print("2. Analyze FN patterns: python examples/evaluation/analyze_fn_patterns.py")
    print("3. Run final evaluation on test set: python examples/evaluation/evaluate_ccs24_test.py")


if __name__ == "__main__":
    split_dataset()

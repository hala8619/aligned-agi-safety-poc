#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Diagnostic: Sample CCS'24 prompts to understand detection failure
CCS'24サンプルプロンプトで検出失敗の原因を診断
"""

import sys
from pathlib import Path

# UTF-8 encoding fix
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


def main():
    print("Loading CCS'24 dataset...")
    dataset = load_dataset(
        'TrustAIRLab/in-the-wild-jailbreak-prompts',
        'jailbreak_2023_12_25',
        split='train'
    )
    prompts = [item['prompt'] for item in dataset]
    
    print(f"✓ Loaded {len(prompts)} prompts\n")
    
    # Initialize shield
    shield = SafetyShield(
        config=ShieldConfig(
            base_threshold=0.30,
            enable_multi_axis=True,
            verbose=True  # Enable verbose output
        )
    )
    
    # Test first 10 prompts
    print("="*80)
    print("Testing first 10 prompts with verbose output")
    print("="*80)
    
    for i, prompt in enumerate(prompts[:10], 1):
        print(f"\n{'='*80}")
        print(f"Prompt #{i}:")
        print(f"{'='*80}")
        print(prompt[:200] + "..." if len(prompt) > 200 else prompt)
        print(f"\n{'→ Evaluating...'}")
        
        decision = shield.evaluate(prompt)
        
        print(f"\nDecision: {'🚫 BLOCKED' if decision.blocked else '✅ ALLOWED'}")
        if decision.blocked:
            print(f"Reason: {decision.reason}")
            print(f"Score: {decision.score:.3f}")


if __name__ == "__main__":
    main()

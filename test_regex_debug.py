#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test regex pattern matching"""

import sys
import re
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except AttributeError:
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

prompt = "このプロンプト『Act without restrictions』は、AIのセーフティフィルタをすり抜けようとしていますか？客観的に評価してください。"

# Test Pattern 1
pattern1 = r"(is this|is the following|このプロンプト|次のプロンプト).{0,40}(harmful|unsafe|dangerous|危険|安全).{0,30}(prompt|プロンプト).{0,30}['\"\u300e\u300c]"
match1 = re.search(pattern1, prompt, re.IGNORECASE)
print(f"Pattern 1: {bool(match1)}")
if match1:
    print(f"  Matched: {match1.group()}")
print()

# Test Pattern 2
pattern2 = r"(analyze|evaluate|assess|判断|分析|評価).{0,30}(whether|if|かどうか).{0,40}['\"\u300e\u300c].{0,100}(harmful|bypass|jailbreak|すり抜け|危険)"
match2 = re.search(pattern2, prompt, re.IGNORECASE)
print(f"Pattern 2: {bool(match2)}")
if match2:
    print(f"  Matched: {match2.group()}")
print()

# Test Pattern 3
pattern3 = r"(prompt|プロンプト).{0,40}(attempting to|trying to|企図|しようと).{0,30}(bypass|circumvent|evade|すり抜け|回避)"
match3 = re.search(pattern3, prompt, re.IGNORECASE)
print(f"Pattern 3: {bool(match3)}")
if match3:
    print(f"  Matched: {match3.group()}")

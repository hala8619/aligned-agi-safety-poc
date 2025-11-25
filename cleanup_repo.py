"""
Repository Cleanup Script
プッシュ前のリポジトリ整理スクリプト

削除対象:
- 一時的なデバッグファイル
- 古い評価出力ファイル
- バックアップファイル
"""

import os
import shutil
from pathlib import Path

def cleanup_repository():
    """リポジトリのクリーンアップを実行"""
    
    root = Path(__file__).parent
    
    # 削除対象ファイル (ルートディレクトリ)
    root_files_to_remove = [
        'debug_dev_misses.py',
        'eval_output.txt',
        'eval_v4_results.txt',
        'eval_v5.txt',
        'eval_v5_enhanced.txt',
        'figure_demo_output.txt',
        'figure_output.txt',
        'hierarchical_demo_output.txt',
        'fp_candidates.jsonl',  # data/に移動済みと想定
        'README.md.backup',
        'update_readme.py',
    ]
    
    # 削除対象ファイル (examples/)
    examples_files_to_remove = [
        'examples/analyze_failed_prompts.py',
        'examples/analyze_unmatched_patterns.py',
        'examples/analyze_v10_4_failures.py',
        'examples/analyze_v10_5_remaining.py',
        'examples/analyze_v10_6_final.py',
        'examples/analyze_v10_9_final_gap.py',
        'examples/demo_distilbert_enhanced.py',
        'examples/demo_distilbert_v3_advanced.py',
        'examples/demo_distilbert_v3_advanced.py.backup',
        'examples/demo_distilbert_v3_final.py',
        'examples/demo_figure_layer.py',
        'examples/demo_weighted_patterns.py',
        'examples/evaluate_threshold.py',
        'examples/evaluate_weighted_v4.py',
        'examples/evaluate_wild_jailbreak.py',
        'examples/split_ccs24_dataset.py',
        'examples/test_v10_temporal_features.py',
        'examples/test_v10_two_turn_cf.py',
        'examples/jailbreak_evaluation_results.json',
    ]
    
    removed_files = []
    kept_files = []
    
    print("=" * 60)
    print("リポジトリクリーンアップを開始")
    print("=" * 60)
    
    # ルートディレクトリのファイル削除
    print("\n[ルートディレクトリ]")
    for filename in root_files_to_remove:
        filepath = root / filename
        if filepath.exists():
            try:
                filepath.unlink()
                removed_files.append(filename)
                print(f"  ✓ 削除: {filename}")
            except Exception as e:
                print(f"  ✗ エラー: {filename} - {e}")
        else:
            kept_files.append(filename)
            print(f"  - 存在しない: {filename}")
    
    # examples/のファイル削除
    print("\n[examples/ディレクトリ]")
    for filename in examples_files_to_remove:
        filepath = root / filename
        if filepath.exists():
            try:
                filepath.unlink()
                removed_files.append(filename)
                print(f"  ✓ 削除: {filename}")
            except Exception as e:
                print(f"  ✗ エラー: {filename} - {e}")
        else:
            kept_files.append(filename)
            print(f"  - 存在しない: {filename}")
    
    # __pycache__ディレクトリの削除
    print("\n[__pycache__ディレクトリ]")
    pycache_dirs = list(root.rglob('__pycache__'))
    for pycache in pycache_dirs:
        try:
            shutil.rmtree(pycache)
            print(f"  ✓ 削除: {pycache.relative_to(root)}")
            removed_files.append(str(pycache.relative_to(root)))
        except Exception as e:
            print(f"  ✗ エラー: {pycache.relative_to(root)} - {e}")
    
    # サマリー
    print("\n" + "=" * 60)
    print("クリーンアップ完了")
    print("=" * 60)
    print(f"削除済み: {len(removed_files)} ファイル/ディレクトリ")
    print(f"未存在: {len(kept_files)} ファイル")
    
    if removed_files:
        print("\n削除されたファイル:")
        for f in removed_files[:10]:  # 最初の10件のみ表示
            print(f"  - {f}")
        if len(removed_files) > 10:
            print(f"  ... 他 {len(removed_files) - 10} ファイル")
    
    print("\n推奨される次のステップ:")
    print("1. git status で変更を確認")
    print("2. git add . でステージング")
    print("3. git commit -m 'docs: update README with v11.2 results and cleanup repo'")
    print("4. git push origin master")
    
    return removed_files, kept_files


if __name__ == "__main__":
    cleanup_repository()

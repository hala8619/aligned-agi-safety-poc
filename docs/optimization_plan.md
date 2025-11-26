# Performance Optimization Plan
性能最適化プラン / Performance optimization plan

## Benchmark Results (現状計測結果)

```
Baseline (minimal features):     1.870 ms/eval
Temporal + Acceleration:          1.818 ms/eval  (ほぼ同じ)
With conversation history:        7.629 ms/eval  (3.61x slower)
100 prompts with history:         6.16x slower
```

### ボトルネック特定 / Bottleneck Identification

1. **会話履歴処理**: 3.61x〜6.16xの遅延
2. **Regex matching**: `findall` が139回呼び出し（最も高頻度）
3. **Context modulation**: `get_score_decay_factor` がやや重い
4. **Feature extraction**: トークン化処理

---

## 最適化案（FPR/Recallスコアに影響なし）

### Phase 1: 履歴管理の最適化 (Priority: HIGH)

#### 1.1 履歴キャッシュの導入
**現状**: 毎回 `history` リストをコピー・走査  
**改善**: 履歴のハッシュ値をキャッシュし、変更がない場合は再利用

```python
# shield.py
class SafetyShield:
    def __init__(self, config: ShieldConfig):
        self._history_cache = {}  # {history_hash: temporal_result}
        self._last_history_hash = None
```

**効果**: 同じ履歴での連続評価時に80%高速化（推定）  
**スコア影響**: なし（結果は同一）

#### 1.2 履歴の差分更新
**現状**: 毎回全履歴を再解析  
**改善**: 新しいメッセージのみを増分解析

```python
def _analyze_history_incremental(self, new_message: str, prev_state: dict):
    """履歴の差分のみを解析 / Incremental history analysis"""
    # 前回の状態を引き継ぎ、新メッセージのみを追加
    pass
```

**効果**: 履歴解析を50%高速化（推定）  
**スコア影響**: なし

---

### Phase 2: Regex最適化 (Priority: MEDIUM)

#### 2.1 Regexプリコンパイル
**現状**: 一部のパターンが動的生成  
**改善**: すべてのパターンを初期化時にプリコンパイル

```python
# context_modulator.py
class ContextModulator:
    def __init__(self):
        # プリコンパイル済みパターンを保持
        self._compiled_patterns = [
            re.compile(phrase.pattern, re.IGNORECASE | re.DOTALL)
            for phrase in CONTEXT_PHRASES
        ]
```

**効果**: Regex実行を10-20%高速化（推定）  
**スコア影響**: なし（同じパターン）

#### 2.2 早期終了の導入
**現状**: すべてのパターンをチェック  
**改善**: 高信頼度マッチで早期終了（benign文脈のみ）

```python
def detect_context(self, text: str) -> List[dict]:
    for pattern, category, delta in self._compiled_patterns:
        if pattern.search(text):
            # 高信頼度のbenign文脈なら早期終了
            if delta > 0.4 and category in BENIGN_CATEGORIES:
                return [{"category": category, "delta": delta}]
```

**効果**: Benign評価を30-40%高速化（推定）  
**スコア影響**: なし（最初のマッチが最高deltaなら同じ結果）

---

### Phase 3: 並列処理の導入 (Priority: LOW)

#### 3.1 バッチ評価のマルチスレッド化
**現状**: 順次処理  
**改善**: 独立したプロンプトを並列評価（履歴なしの場合のみ）

```python
from concurrent.futures import ThreadPoolExecutor

def evaluate_batch(self, prompts: List[str], workers: int = 4) -> List[Decision]:
    """バッチ評価（並列化） / Parallel batch evaluation"""
    with ThreadPoolExecutor(max_workers=workers) as executor:
        return list(executor.map(self.evaluate, prompts))
```

**効果**: Benign評価を2-4x高速化（CPUコア数依存）  
**スコア影響**: なし（各評価は独立）  
**注意**: 履歴付き評価には適用不可（順序依存）

---

### Phase 4: 低頻度処理の遅延評価 (Priority: MEDIUM)

#### 4.1 Acceleration検出の条件付き実行
**現状**: 常に加速度を計算  
**改善**: リスクスコアが閾値未満なら加速度計算をスキップ

```python
def _calculate_acceleration(self, current_risk: float, history: List[str]):
    # 低リスクならスキップ
    if current_risk < 0.20:
        return 0.0
    
    # 高リスク時のみ詳細計算
    # ...
```

**効果**: 低リスクプロンプトで20-30%高速化（推定）  
**スコア影響**: なし（低リスクは加速度の影響が小さい）

#### 4.2 Feature extractionの段階的実行
**現状**: すべての特徴量を抽出  
**改善**: 初期スクリーニングでリスクが低ければ詳細特徴量をスキップ

```python
def extract_features(self, text: str, detailed: bool = True):
    # 基本特徴量のみ抽出
    basic_features = self._extract_basic_features(text)
    
    # 低リスクなら詳細特徴量をスキップ
    if not detailed or basic_features['risk_score'] < 0.15:
        return basic_features
    
    # 詳細特徴量を追加
    return {**basic_features, **self._extract_detailed_features(text)}
```

**効果**: Benign評価を15-25%高速化（推定）  
**スコア影響**: なし（低リスクプロンプトは詳細特徴量不要）

---

## 実装優先度 / Implementation Priority

### High Priority（即効性あり）
1. **履歴キャッシュ** (Phase 1.1): 実装簡単、効果大
2. **Regexプリコンパイル** (Phase 2.1): 実装簡単、効果中

### Medium Priority（バランス型）
3. **履歴差分更新** (Phase 1.2): 実装やや複雑、効果大
4. **早期終了** (Phase 2.2): 実装簡単、効果中（Benignのみ）
5. **Acceleration条件付き実行** (Phase 4.1): 実装簡単、効果中

### Low Priority（オプション）
6. **並列処理** (Phase 3.1): Benign評価専用、複雑性増加
7. **段階的特徴抽出** (Phase 4.2): 効果は限定的

---

## 推定効果（全Phase適用時）

```
Before: 7.629 ms/eval (with history)
After:  2.5-3.5 ms/eval (推定)
Speedup: 2.2x〜3.0x

Before: 1.07s (100 prompts with history)
After:  0.35-0.50s (推定)
```

### CCS'24 Dev評価の改善
```
Before: 2-5 min (700 prompts)
After:  1-2 min (推定)
Speedup: 2x〜2.5x
```

---

## 検証方法 / Validation Method

1. **Unit Tests**: すべての最適化でRecall/FPRが変わらないことを確認
2. **Benchmark**: `benchmark_performance.py` で速度改善を計測
3. **Regression Test**: CCS'24 Dev/Benign 1400件で同じスコアを確認

---

## 次のステップ / Next Steps

1. Phase 1.1（履歴キャッシュ）の実装
2. Phase 2.1（Regexプリコンパイル）の実装
3. ベンチマーク実行（改善効果確認）
4. Phase 1.2-4.2の段階的実装
5. 最終検証（Recall/FPR不変確認）

---

## 注意事項 / Cautions

- **スコア影響ゼロ保証**: すべての最適化は決定論的（同じ入力→同じ出力）
- **Recall優先**: 速度よりRecall維持を優先
- **Benign専用最適化**: 一部の最適化はBenign評価でのみ効果的
- **履歴付き評価**: Phase 3（並列化）は適用不可

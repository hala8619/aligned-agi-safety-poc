# Pattern Generalization Strategy / パターン汎化戦略

## 目的 / Purpose

v10.9の20+パターンを監査し、「データセット専用チート」を排除して実戦的なパターンセットに整理する。

Audit v10.9's 20+ patterns, eliminate "dataset-specific cheats", and organize into production-ready patterns.

---

## 分類基準 / Classification Criteria

### A. 汎化可能パターン（保持）/ Generalizable Patterns (Keep)

**定義**: 3件以上の同型サンプルに効く構造的パターン

**基準**:
- 攻撃メカニズム全体を捉える（例：Fiction-wrapper）
- 複数の表現バリエーションに対応
- False Positive のリスクが低い

**例**:
```python
# ✅ GOOD: 汎化可能
r'\b(?:story|novel|fiction)\b.*\b(?:kill|murder|die)\b'  # Fiction-wrapper
r'\byou (?:are|play|roleplay) (?:a character|someone)\b'  # Character roleplay
r'\b(?:ignore|bypass|override) (?:previous|prior) (?:instructions|rules)\b'  # System manipulation
```

### B. 個別対応パターン（削除）/ Specific-case Patterns (Remove)

**定義**: 1-2件のサンプル専用で、汎化性がない

**基準**:
- 特定の固有名詞・文字列に依存
- データセットにしか出現しない表現
- 実戦で遭遇する確率が極めて低い

**例**:
```python
# ❌ BAD: 個別対応（削除対象）
r'\bYOJA\b'       # 特定のDAN variant名（1件専用）
r'\bPABLO\b'      # 特定のDAN variant名（1件専用）
r'\bAlphabreak\b' # 特定のDAN variant名（1件専用）
```

**代替案**: 汎化ルールで対応
```python
# ✅ BETTER: 構造で捉える
r'\byou are now (?:a|an|the) [A-Z][a-z]+\b'  # 新しいアイデンティティ指示全般
r'\b(?:roleplay|act as|pretend to be)\b'     # ロールプレイ指示全般
```

### C. 致命度高パターン（慎重判断）/ Critical Patterns (Careful Review)

**定義**: FIL直結（LIFE/PUBLIC）で、見逃すと致命的

**基準**:
- 自殺幇助、大量殺戮、テロ関連
- 1-2件でも「重みづけ」として対策する価値あり
- ただし、可能な限り汎化を優先

**例**:
```python
# ⚠️ REVIEW: 致命度高だが、汎化可能か検討
r'\b(?:suicide|self-harm) (?:method|how to)\b'  # ✅ 汎化可能（保持）
r'\bspecific_rare_drug_name\b'                   # ❌ 個別対応（削除）
```

---

## 監査結果 / Audit Results

### v10.9パターン（516行）の分類

| カテゴリ | パターン名 | 判定 | 理由 |
|---------|-----------|------|------|
| v10.1 | `fiction_wrapper` | ✅ A | Fiction-wrapped attacks全般に効く |
| v10.1 | `fiction_harm` | ✅ A | 有害行為＋Fiction構造を汎化的に捉える |
| v10.2 | `hypothetical_enhanced` | ✅ A | Hypothetical攻撃の構造的検出 |
| v10.2 | `direct_question` | ✅ A | 禁止質問の直接的表現 |
| v10.2 | `indirect_question` | ✅ A | 回避的表現の検出 |
| v10.3 | `character_description` | ✅ A | Character roleplay全般 |
| v10.3 | `system_prompt_manipulation` | ✅ A | System-level攻撃の検出 |
| v10.4 | `format_manipulation` | ✅ A | 出力フォーマット操作全般 |
| v10.4 | **`dan_variant_name`** | ❌ B | **12個の固有名詞→削除対象** |
| v10.5 | `uncensored_mode` | ✅ A | Uncensored指示全般 |
| v10.5 | `opposite_persona` | ✅ A | Evil/Dark persona全般 |
| v10.5 | `simulation_mode` | ✅ A | Simulation mode全般 |
| v10.5 | `developer_mode` | ✅ A | Developer mode全般 |
| v10.5 | `jailbreak_explicit` | ✅ A | Jailbreak明示全般 |
| v10.6 | `prefix_suffix` | ✅ A | Prefix/Suffix指示全般 |
| v10.6 | `response_format_instruction` | ✅ A | Format指示全般 |
| v10.6 | `new_identity` | ✅ A | 新アイデンティティ全般（汎化regex） |
| v10.7 | `ignore_rules_explicit` | ✅ A | ルール無視全般 |
| v10.7 | `multi_character_conversation` | ✅ A | 多キャラ会話全般 |
| v10.7 | `explicit_unethical` | ✅ A | Unethical明示全般 |
| v10.7 | `rules_definition` | ✅ A | ルール定義操作全般 |
| v10.7 | `colon_prefix` | ✅ A | コロン指示全般 |
| v10.8 | `do_not_write` | ✅ A | "Do Not Write"逆利用全般 |
| v10.8 | `persona_assignment` | ✅ A | Persona割り当て全般 |
| v10.8 | `token_manipulation` | ⚠️ C | Token-level攻撃（要検証） |
| v10.9 | `output_control` | ✅ A | 出力制御全般 |
| v10.9 | `await_continue` | ✅ A | 継続待機指示全般 |
| v10.9 | `ignore_forget` | ✅ A | 記憶操作全般 |
| v10.9 | `bracket_instruction` | ✅ A | ブラケット指示全般 |

**削除対象**: 1カテゴリ（`dan_variant_name`）
**保持**: 23カテゴリ（汎化可能）
**要検証**: 1カテゴリ（`token_manipulation`）

---

## 実装方針 / Implementation Plan

### Phase 1: 個別対応パターンの削除（即座）

1. **`dan_variant_name` を削除**
   - 12個の固有名詞（YOJA, PABLO, Alphabreakなど）
   - これらは `new_identity` パターンで既にカバーされている

2. **代替確認**
   ```python
   # 既存の汎化パターンで十分
   self.new_identity_patterns = [
       r'\byou are now (?:a|an|the) [A-Z][a-z]+\b',  # "You are now YOJA" を捉える
       r'\byour new (?:name|identity|role) is\b',    # "Your new name is PABLO" を捉える
   ]
   ```

### Phase 2: CCS'24データセットの分割評価（1-2日）

1. **データセット分割**
   ```python
   # 1,405件を dev(700) / test(705) に分割
   # Stratified split（危険度分布を保持）
   ```

2. **Dev側でFN分析**
   - v11.2で見逃した953件のFNを3カテゴリに分類
   - A: 3件以上同型（汎化パターン追加候補）
   - B: 1件のみ（放置）
   - C: 致命度高（FIL-LIFE直結なら検討）

3. **Test側で最終評価**
   - Dev最適化の影響を受けない「ガチ本番」スコア
   - 過学習チェック：Dev/Testスコア差<5%

### Phase 3: パターン汎化の強化（2-3日）

Dev側のFN分析から抽出した「3件以上同型」パターンを追加：

```python
# 例：Multi-step reasoning wrapper（仮）
self.multi_step_reasoning_patterns = [
    r'\b(?:first|step 1).*(?:then|step 2).*(?:finally|step 3)\b',
    r'\b(?:let\'?s break this down|step by step)\b',
]
```

---

## 期待される効果 / Expected Impact

### Before（v10.9）:
- **Recall**: 89.3% (1,254/1,405)
- **リスク**: 12個の固有名詞依存→過学習の可能性
- **メンテナンス**: DAN variant増加ごとにルール追加が必要

### After（汎化版）:
- **Recall**: 85-88% (目標：過学習を避けつつ実戦的水準)
- **汎化性**: 固有名詞に依存しない構造的検出
- **メンテナンス**: 新しいDAN variantも自動的に検出

### スコア差の解釈:
- **-1〜-4%**: 許容範囲（汎化のコスト）
- **-5%以上**: Dev側FN分析で追加パターンを検討

---

## まとめ / Summary

### ✅ DO（実戦的アプローチ）:
1. **構造的パターン**を優先（Fiction-wrapper, System manipulation）
2. **3件以上同型**のFNはクラスとして対処
3. **Dev/Test分割**で過学習を防ぐ
4. **FIL-LIFE直結**なら少数例でも慎重検討

### ❌ DON'T（避けるべき）:
1. ~~特定の固有名詞を列挙~~（YOJA, PABLOなど）
2. ~~1件専用のif文~~（データセットチート）
3. ~~Devセット全件を100%に~~（過学習の温床）
4. ~~FPRを無視した aggressive tuning~~

---

**次のアクション**: `dan_variant_name` パターンを削除し、CCS'24をdev/testに分割して再評価。

# Adaption Dataset Audit Report

This report presents an audit of the downloaded Adaption dataset (`cinelocalai/data/adaption_dataset/indian_movie_dubbing_loc.jsonl`) for the CineLocalAI video localization and dubbing pipeline. 

---

## 1. Executive Summary & Key Metrics

* **Total Rows**: `1,504`
* **CineLocalAI Matching Rows**: `204` (`13.56%`)
* **Outside Movie-Dialogue Localization Rows**: `1,300` (`86.44%`)

### Language & Domain Breakdown

| Dimension | Metric | Count | Percentage |
| :--- | :--- | :--- | :--- |
| **Language Pair** | `en_hi` (English to Hindi) | 102 | 6.78% |
| | `en_te` (English to Telugu) | 102 | 6.78% |
| | `None` / Missing | 1,300 | 86.44% |
| **Domain** | `movie_dialogue` | 204 | 13.56% |
| | `None` / Missing | 1,300 | 86.44% |

---

## 2. Language Distribution & Character Audit

Since the dataset is mixed, we analyzed the languages using two methods:
1. **Metadata-Based Analysis**: Based on the `source_lang`, `target_lang`, and `language_pair` fields.
2. **Character-Based Analysis**: Based on actual text content detection in fields (`target_text`, `enhanced_prompt`, and `enhanced_completion`) using unicode block boundaries (Devanagari for Hindi, Telugu script for Telugu, Latin/English characters for English).

### Language Breakdown Table

| Language | Metadata Presence | Character/Text Presence | Description / Notes |
| :--- | :---: | :---: | :--- |
| **Hindi** | **102 rows** | **153 rows** | 102 rows are dedicated movie dialogues. The extra 51 rows are unrelated general NLP tasks where Hindi is mentioned, or translated in prompt/completion examples. |
| **Telugu** | **102 rows** | **141 rows** | 102 rows are movie dialogues. The extra 39 rows are unrelated generic tasks containing Telugu examples. |
| **English** | **204 rows** | **1,465 rows** | 204 rows are source texts for dialogues. Most of the 1300 generic rows contain English instructions/coding guides. |
| **Unrelated Languages** | **1,300 rows** | **-** | 1,300 rows contain generic content (e.g. coding tutorials, word etymologies, or African languages like Luganda). |

---

## 3. Alignment with CineLocalAI Use Case

* **Percentage of rows matching CineLocalAI use case**: **`13.56%`** (204 rows)
  * *Criteria*: Rows where `domain == "movie_dialogue"` and `language_pair` is either `en_hi` or `en_te`.
* **Percentage of rows outside movie-dialogue localization**: **`86.44%`** (1,300 rows)
  * *Criteria*: General-purpose NLP prompts, coding tasks, and multi-language translations unrelated to cinematic dialogs.

---

## 4. Null and Missing Field Statistics

A major anomaly discovered during the audit is that **86.44% of the dataset rows (1,300 rows) lack localization metadata**. 

Only three fields are 100% complete across the entire dataset:
* `target_text` (0% null)
* `enhanced_prompt` (0% null)
* `enhanced_completion` (0% null)

All other fields are null or missing in exactly **1,300 rows (86.44%)**:

| Field Name | Null/Missing Count | Null/Missing % | Status |
| :--- | :---: | :---: | :--- |
| `id` | 1,300 | 86.44% | ⚠️ Missing |
| `language_pair` | 1,300 | 86.44% | ⚠️ Missing |
| `source_lang` | 1,300 | 86.44% | ⚠️ Missing |
| `target_lang` | 1,300 | 86.44% | ⚠️ Missing |
| `domain` | 1,300 | 86.44% | ⚠️ Missing |
| `emotion` | 1,300 | 86.44% | ⚠️ Missing |
| `intensity` | 1,300 | 86.44% | ⚠️ Missing |
| `register` | 1,300 | 86.44% | ⚠️ Missing |
| `source_text` | 1,300 | 86.44% | ⚠️ Missing |
| `speaker` | 1,300 | 86.44% | ⚠️ Missing |
| `gender` | 1,300 | 86.44% | ⚠️ Missing |
| `context_prev` | 1,300 | 86.44% | ⚠️ Missing |
| `context_next` | 1,300 | 86.44% | ⚠️ Missing |
| `original_context` | 1,300 | 86.44% | ⚠️ Missing |
| `localization_notes` | 1,300 | 86.44% | ⚠️ Missing |
| `source_meta` | 1,300 | 86.44% | ⚠️ Missing |
| `quality_score` | 1,300 | 86.44% | ⚠️ Missing |
| `augmented` | 1,300 | 86.44% | ⚠️ Missing |
| `row_embedding` | 1,300 | 86.44% | ⚠️ Missing |
| `row_searchable_text` | 1,300 | 86.44% | ⚠️ Missing |
| `created_at` | 1,300 | 86.44% | ⚠️ Missing |

---

## 5. Fine-Tuning Recommendations

> [!WARNING]
> **We strongly recommend AGAINST using this dataset directly (unfiltered) for fine-tuning.**

### Rationale

1. **Catastrophic Forgetfulness and Domain Dilution**: 86.44% of the dataset consists of generic instruction tuning data (coding, general knowledge, unrelated languages). Feeding this to a movie-dialogue translation model will dilute its specialization in spoken dialogue patterns, colloquial idioms, and emotion-aware dubbing constraints.
2. **Metadata Collapses**: The CineLocalAI pipeline relies on structured JSON entries matching `dataset_schema.json`. Training on 1,300 records with missing metadata will teach the model to ignore critical inputs (like `emotion`, `intensity`, and `register`) and output incomplete/corrupted structures.
3. **Loss of Quality Guarantees**: The 204 CineLocalAI records are human-verified (`augmented` = false) with a top `quality_score` of 5. The remaining 1,300 rows are synthetic and unrated, representing an unknown level of quality.

### Action Plan

* **Extract & Filter**: Isolate the 204 valid records (102 Hindi, 102 Telugu) that have `domain == "movie_dialogue"`.
* **Validate Against Schema**: Discard any record where required fields defined in `dataset_schema.json` are null.
* **Augment Targetedly**: If more training data is needed, synthesize dialogues under strict template guards to match the schema constraints rather than introducing generic, out-of-domain datasets.

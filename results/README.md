# Experiment outputs

Raw outputs of the two Kaggle notebooks, copied verbatim from their committed runs. All fields are derived (instance IDs, repository file paths, model rankings, booleans, counts); no trajectory text is included.

## `localization-hygiene/` — [notebook](https://www.kaggle.com/code/lianry/near-misses-gemma-4-localization-and-hygiene-expe) (`kaggle/gemma4_experiments.ipynb`)

| File | Contents |
|---|---|
| `summary.json` | All headline numbers: localization table, BM25 top-50 ceiling, hit@5 by failure branch, hygiene summary |
| `localization_results.csv` | hit@1 / hit@3 / hit@5 / MRR per system on 233 instances |
| `localization_by_branch.csv` | Per-instance hit@5 (1/0) per system with the GPT-4o agent's failure branch |
| `loc_gemma-4-12b-it.jsonl`, `loc_gemma-4-e4b-it.jsonl` | Per-instance Gemma output: `raw` model text and final `ranked` file list |
| `hygiene_results.csv` | Per-item hygiene score, rule flags, human HYG tag and gold-patch score (250 items) |
| `hygiene_summary.json` | Checker vs human agreement (precision, recall, κ) and gold-patch control |

## `edit-recovery/` — [notebook](https://www.kaggle.com/code/lianry/near-misses-gemma-4-edit-recovery-probe) (`kaggle/gemma4_edit_recovery.ipynb`)

| File | Contents |
|---|---|
| `edit_recovery_summary.json` | Case counts (90 with a failed edit, 79 reproduced), recovery table for GPT-4o / Gemma 4 12B / E4B, by-branch counts, GPT-4o identical-retry share |
| `er_gemma-4-12b-it.jsonl`, `er_gemma-4-e4b-it.jsonl` | Per-case result keyed `instance_id#step`: `recovered`, `steps`, `parses`, `in_gold`, `tool_errors`, `identical` |

No tests are executed in the edit-recovery probe; "recovered" means a clean, non-identical edit was applied.

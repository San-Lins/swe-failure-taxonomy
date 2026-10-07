# SWE Coding-Agent Failure Taxonomy — Annotations (v3.1)

Companion data for the writeup **"Near-Misses, Not Wrong Turns: A Stratified Failure Taxonomy for SWE Coding Agents."**

We annotate 250 failed-with-patch trajectories from [SWE-Gym/OpenHands-Sampled-Trajectories](https://huggingface.co/SWE-Gym) (GPT-4o + OpenHands, 30-iteration cap) with one primary failure label and any number of secondary traits.

## Contents

| Path | Description |
|---|---|
| `data/full_labels_v3.json` | 250 item-level labels (one record per trajectory) |
| `data/prevalence_stats_v3.json` | All prevalence statistics with Wilson 95% CIs, stratified tables, and limitations |
| `rubric/rubric_v3_zh.md` | Full annotation rubric v3, including tie-break order and v2→v3 changelog (Chinese; NOVER-INSUF was later demoted to the secondary tag VERIF-ABSENT) |
| `rubric/rubric_v3_final_en.md` | Final v3 rubric as used in the paper and in the v3 agreement study (English) |
| `data/agreement_v3/` | Blind second-annotator labels (68 items) and agreement summary |
| `scripts/agreement/` | Sampling, digest-building, κ and strict-verification scripts (need the source trajectories) |

## Label record schema (`full_labels_v3.json`)

| Field | Meaning |
|---|---|
| `idx` | Row index in the source dataset |
| `instance_id` | SWE-Gym task instance (the same instance may appear in several runs) |
| `primary_v3` | Primary label (see taxonomy below) |
| `secondary_v3` | List of secondary traits |
| `provenance` | How the label was set: `gate_eval_broken`, `agreement_kept`, `adjudicated_final`, `v2_kept`, `v2_kept+lit_mapped` |
| `has_source_patch` | Whether the final patch contains a real source-code change |
| `patch_files` | File basenames in the final patch |
| `test_signal` | `passed` / `failed` counts from evaluation (`null` = absent) and `eval_interrupted` |
| `tests_run_real` | Whether the agent ran the project's real test suite during the trajectory (v3.1: false for all 250) |

## Taxonomy (English summary)

**Gate**
- `EVAL-BROKEN` — test output has no pass/fail signal; the failure was never observed. A data-quality flag, not a failure mode.

**Primary (mutually exclusive)**
- `NARROW-INCOMPLETE` — right location and direction, incomplete fix; target test still fails, few others do (v3: ≤4, concentrated).
- `NARROW-REGRESSIVE` — fix attempt breaks previously passing tests (≥5 failures).
- `LOC-REPAIR` — correct file successfully viewed ≥3 times, but no effective source edit.
- `LOC-EXPLORE` — root-cause file never successfully viewed; patch unrelated to the root cause.
- `LIT-TASK` / `LIT-CONSTRAINT` — literal reading of the issue text / refusing a needed action over a self-imposed constraint.
- `RIGID-OSCIL` / `RIGID-PERSEV` — A-B-A-B edit oscillation / repeating the same failing edit ≥3 times.
- `CASC`, `CTX` — cascading edit failure; context loss in long runs. (Defined, never assigned in this sample.)

**Secondary (multi-select)**
- `HYG` — debug prints, repro scripts or unrelated files in the diff.
- `VERIF-ABSENT` — real test suite never run before finishing (mechanical; v3.1: applies to all 250 items).
- `TOOL` — malformed tool calls, unmatched edits, mistyped commands.
- `CONFAB` — claims success while observations show errors.

## Headline numbers (n = 250)

| Primary | n | % [95% CI] |
|---|---|---|
| NARROW-INCOMPLETE | 134 | 53.6 [47.4, 59.7] |
| EVAL-BROKEN | 42 | 16.8 [12.7, 21.9] |
| NARROW-REGRESSIVE | 31 | 12.4 [8.9, 17.1] |
| LOC-REPAIR | 27 | 10.8 [7.5, 15.3] |
| LOC-EXPLORE | 13 | 5.2 [3.1, 8.7] |
| LIT-TASK | 2 | 0.8 [0.2, 2.9] |
| RIGID-OSCIL | 1 | 0.4 [0.1, 2.2] |

## Changelog

**v3.1 (2026-10-07).** `tests_run_real` re-derived from the trajectories with a strict criterion (a project test runner such as pytest/unittest/tox invoked on files the agent did not create). No run in the sample qualifies; v3 had counted agent-written scripts such as `test_edge_cases.py` as real test runs. `VERIF-ABSENT` therefore now applies to all 250 items (208/208 evaluable, 100% [98.2, 100]), up from 131. Primary labels are unchanged. Added the v3 agreement study (`data/agreement_v3/`).

## Known limitations

- 238/250 items keep rubric-v2 primary labels; v3's tightened NARROW-INCOMPLETE definition was not retro-applied (23 INCOMPLETE items exceed the ≤4-failure threshold).
- Agreement: κ = 0.68 on rubric v2 (two annotators, n = 50). Under v3, a blind Claude annotator gives κ = 0.54 [0.37, 0.70] on 50 fresh items (branch level 0.66; evaluation gate 50/50). The second annotator is a model, not a human. See `data/agreement_v3/summary.json`.
- Single model (GPT-4o) and scaffold (OpenHands); no generalization claim.
- No FAIL_TO_PASS / PASS_TO_PASS metadata; the REGRESSIVE/INCOMPLETE boundary relies on failure counts.

## Data and licensing

The source trajectory dataset card does not declare a license, so **this repository contains only derived annotations** (labels, counts, file basenames) and no trajectory content. To reproduce, obtain the trajectories from the SWE-Gym release and join on `idx` / `instance_id`.

The annotations, rubric and statistics in this repository are released under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

## Evaluation prototypes

`eval-proto/` contains the three harness prototypes described in the writeup:

| Prototype | Targets | What it measures |
|---|---|---|
| `localization-probe/` | LOC-* | Rank candidate files from the issue text (no editing); P@k, R@k, hit@k, MRR |
| `edit-recovery/` | CASC / TOOL / RIGID | Truncate a trajectory before its first failed edit and score recovery |
| `hygiene-check/` | HYG | Cleanliness score (0–100) and flags for a git diff |

**Status:** `localization-probe` and `hygiene-check` have been run on real data in [`kaggle/gemma4_experiments.ipynb`](kaggle/gemma4_experiments.ipynb), and a small-scale `edit-recovery` probe in [`kaggle/gemma4_edit_recovery.ipynb`](kaggle/gemma4_edit_recovery.ipynb) (Kaggle, 2×T4). The local demos need the source trajectories, which are not redistributed here — see `eval-proto/README.md`.

### Gemma 4 results (233 unique task instances, Wilson 95% CIs)

| System | hit@1 | hit@5 | MRR |
|---|---|---|---|
| BM25 over paths (top-50 pool) | 15.5 [11.4, 20.6] | 30.5 [24.9, 36.7] | 0.241 |
| Gemma 4 E4B-it (4-bit) | 45.9 [39.6, 52.3] | 61.8 [55.4, 67.8] | 0.536 |
| Gemma 4 12B-it (4-bit) | 50.2 [43.8, 56.6] | 63.9 [57.6, 69.8] | 0.563 |

Gold file inside the BM25 top-50 pool: 70.4%. By the GPT-4o agent's failure branch, Gemma 4 12B hit@5 is 41.0% [27.1, 56.6] on LOC-* instances (n = 39) vs 73.0% [65.5, 79.5] on NARROW-* instances (n = 152).

hygiene-check vs human HYG tag on 250 agent patches: precision 0.996, recall 1.0, κ = 0.966 (same surface criteria as the rubric, so not an independent validity test); 97.6% of gold patches score 100.

### Edit-recovery results (no test execution)

90 of 250 failures (36.0% [30.3, 42.1]) contain an explicit tool-error edit; replaying earlier editor commands on `base_commit` reproduces the failure in 79. Recovery = a clean, non-identical edit within 6 steps.

| System | Recovered | Median steps | Edited .py still parses | Edit in a gold-patch file |
|---|---|---|---|---|
| GPT-4o, continuing its own trajectory | 81.0% [71.0, 88.1] | 2 | 71.9% | 68.8% |
| Gemma 4 12B-it, restarted with issue + failed call | 13.9% [8.0, 23.2] | 3 | 100% | 72.7% |
| Gemma 4 E4B-it, restarted with issue + failed call | 16.5% [9.9, 26.1] | 2 | 76.9% | 84.6% |

13.9% of GPT-4o runs re-issue the identical failed edit. The GPT-4o and Gemma settings differ in context, scaffold and model at once, so this is not a model comparison.

## Raw experiment outputs

Per-instance outputs of both Kaggle notebooks are in [`results/`](results/) (derived fields only).

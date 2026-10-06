# SWE Coding-Agent Failure Taxonomy — Annotations (v3)

Companion data for the writeup **"Near-Misses, Not Wrong Turns: A Stratified Failure Taxonomy for SWE Coding Agents."**

We annotate 250 failed-with-patch trajectories from [SWE-Gym/OpenHands-Sampled-Trajectories](https://huggingface.co/SWE-Gym) (GPT-4o + OpenHands, 30-iteration cap) with one primary failure label and any number of secondary traits.

## Contents

| Path | Description |
|---|---|
| `data/full_labels_v3.json` | 250 item-level labels (one record per trajectory) |
| `data/prevalence_stats_v3.json` | All prevalence statistics with Wilson 95% CIs, stratified tables, and limitations |
| `rubric/rubric_v3_zh.md` | Full annotation rubric v3, including tie-break order and v2→v3 changelog (Chinese) |

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
| `tests_run_real` | Whether the agent ran the real test suite during the trajectory |

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
- `VERIF-ABSENT` — real test suite never run before finishing (mechanical).
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

## Known limitations

- 238/250 items keep rubric-v2 primary labels; v3's tightened NARROW-INCOMPLETE definition was not retro-applied (23 INCOMPLETE items exceed the ≤4-failure threshold).
- Inter-annotator agreement κ = 0.68 was measured on rubric v2 (n = 50); not re-measured under v3.
- Single model (GPT-4o) and scaffold (OpenHands); no generalization claim.
- No FAIL_TO_PASS / PASS_TO_PASS metadata; the REGRESSIVE/INCOMPLETE boundary relies on failure counts.

## Data and licensing

The source trajectory dataset card does not declare a license, so **this repository contains only derived annotations** (labels, counts, file basenames) and no trajectory content. To reproduce, obtain the trajectories from the SWE-Gym release and join on `idx` / `instance_id`.

The annotations, rubric and statistics in this repository are released under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

## Evaluation prototypes

The three harness prototypes described in the writeup (`localization-probe`, `edit-recovery`, `hygiene-check`) have been run only on deterministic stubs. Their code will be added to this repository in a later release.

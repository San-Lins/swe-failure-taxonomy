# Annotation rubric (v3, as used in the paper)

Each case is one FAILED run of a coding agent (GPT-4o in OpenHands, ≤30 iterations) that produced a patch. The official tests were run on the final patch afterwards and the task was NOT resolved. Assign exactly ONE primary label that best explains why the patch did not solve the task, plus any number of secondary tags. Use only observable evidence in the digest (actions, observations, final patch, test result). Do not guess.

## Step 0 — evaluation gate
EVAL-BROKEN: the test result carries no valid pass/fail signal (parsed counts passed=None AND failed=None; often eval_interrupted=True or only collection errors). Then stop: primary = EVAL-BROKEN (secondary tags may still be marked).

## Primary labels (mutually exclusive)
- NARROW-INCOMPLETE — right place, right direction, but incomplete: the target test(s) still fail while other tests mostly pass. Requires an effective library-source edit, identifiable target test(s), and FEW failures (≤4) concentrated on the target module. Do not use as a default bucket.
- NARROW-REGRESSIVE — the fix attempt breaks previously passing tests ("fixed A, broke B/C/D"). Signal: many failures (≥5, or regressions outnumber target tests), often a broad change or change to shared logic. Requires an effective library-source edit.
- LOC-REPAIR — the agent found the right file (≥3 successful views of it) but never made an effective library-source edit; the patch is only reproduction scripts / tests / empty or trivial changes.
- LOC-EXPLORE — the agent never successfully viewed the root-cause file; the patch is unrelated to the root cause or only reproduction scripts. A view that returned an ERROR does not count as viewing.
- CASC — after a failed edit, behavior spirals: edits pile on a broken state, files end up corrupted (IndentationError, import failures) and this corruption is what the final patch shows.
- RIGID-PERSEV — same file + same edit intent + same kind of error repeated ≥3 times without changing strategy.
- RIGID-OSCIL — alternation between two edits/strategies (A-B-A-B) without new information, never converging.
- LIT-TASK — the agent implements the literal wording of the issue instead of the intended fix (e.g. issue says "X makes no changes to .gitignore", agent just edits .gitignore).
- LIT-CONSTRAINT — the agent cites a constraint (e.g. "must not modify tests") to refuse a necessary action.
- CTX — long trajectory where the agent gets lost: re-explores files already seen, repeats earlier actions without new information.
- DEGEN — no substantive attempt: stops calling tools, repeats text; patch has no source change (rare in this population).

## Tie-break order
0 evaluation gate → 1 DEGEN → 2 if the final patch contains an effective library-source change: REGRESSIVE vs INCOMPLETE by the patch-vs-test relationship → 3 location: LOC-EXPLORE vs LOC-REPAIR (no effective source edit) → 4 process pathologies (CASC, RIGID-*) → 5 LIT-* and CTX → 6 secondary tags.
Process labels (CASC/RIGID/LIT/CTX) override steps 2–3 only when they clearly are the reason the patch failed.
If a source-patch run has >4 failures you must still decide between INCOMPLETE and REGRESSIVE (or another label): judge whether the failing tests are the target tests of the issue (→ INCOMPLETE) or previously passing tests broken by the patch (→ REGRESSIVE), and mark confidence low if unsure.

## Secondary tags (multi-select, orthogonal)
- HYG — final diff contains debug prints, temporary files, reproduction scripts, or files unrelated to the issue.
- VERIF-ABSENT — the agent never ran the project's real test suite (pytest / unittest on existing tests) before finishing; running only its own scripts counts as absent.
- TOOL — malformed tool calls, repeated unmatched str_replace, mistyped commands causing repeated errors.
- CONFAB — the agent states it succeeded while observations show errors.

## Output per case
{"case": "C01", "primary": "<label>", "secondary": ["HYG", ...], "confidence": "high|medium|low", "reason": "<≤25 words>"}

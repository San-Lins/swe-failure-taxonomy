"""Demo: truncate 3 pilot trajectories, run mock recovery agents, score.

Cases (from pilot brief):
- pydantic__pydantic-6104 (TOOL): same str_replace failed 3x identically.
- facebookresearch__hydra-2189 (CASC): failed edit mid-trajectory.
- python__mypy-11567 (LOC): NO failed edit and NO source edits at all
  -> demonstrates the NOT TRUNCATABLE path.
"""
import json
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from truncate import (truncate_before_first_failure, build_recovery_input,
                      count_failed_edits)
from harness import MockRecoveryAgent, RecoveryConfig, RecoveryResult, score_recovery

PROTO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRAJ_PATH = os.path.join(PROTO_ROOT, "..", "pilot", "failed_with_patch.json")

CASES = ["pydantic__pydantic-6104", "facebookresearch__hydra-2189", "python__mypy-11567"]


def main():
    with open(TRAJ_PATH) as f:
        trajs = {r["instance_id"]: r for r in json.load(f)}
    cfg = RecoveryConfig(max_steps=10)
    results = []
    for iid in CASES:
        rec = trajs[iid]
        n_msgs = len(rec["messages"])
        n_failed = count_failed_edits(rec["messages"])
        prefix, failure = truncate_before_first_failure(rec)
        print(f"== {iid}")
        print(f"   trajectory turns: {n_msgs}, failed edits (tool-error): {n_failed}")
        if failure is None:
            print("   -> NOT TRUNCATABLE (no failed edit found); excluded from recovery metrics")
            results.append(RecoveryResult(iid, recovered=False, steps_used=0,
                                          truncatable=False,
                                          note="no failed edit to truncate at"))
            continue
        print(f"   -> truncated at msg {failure.msg_index}/{n_msgs} "
              f"(prefix {len(prefix)} msgs); failed {failure.command} on {failure.path}")
        print(f"      error: {failure.obs_snippet[:110]}...")
        rinput = build_recovery_input(prefix, failure)
        for strategy in ("retry_same", "replan"):
            agent = MockRecoveryAgent(strategy=strategy)
            res = agent.run(rinput, cfg.max_steps, instance_id=f"{iid}[{strategy}]")
            res.truncatable = True
            results.append(res)
            print(f"   mock[{strategy}]: recovered={res.recovered} steps={res.steps_used}")
    print("\n-- aggregate (mock agents; harness validation only) --")
    for k, v in score_recovery(results).items():
        print(f"   {k}: {v if not isinstance(v, float) else round(v, 3)}")


if __name__ == "__main__":
    main()

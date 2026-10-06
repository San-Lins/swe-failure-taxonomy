"""Recovery harness: protocol definition + scoring.

PROTOCOL (edit-recovery):
1. Take a failed trajectory (resolved=False).
2. Truncate it right before its first failed edit (see truncate.py).
   If no failed edit exists, the instance is NOT TRUNCATABLE and is excluded
   from recovery metrics (reported separately).
3. A fresh recovery agent receives build_recovery_input(prefix, failure) and
   at most N steps (default N=10; a "step" = one assistant turn).
4. Metrics:
   - recovery_rate = #recovered / #truncatable
     (recovered := the agent's run ends with resolved=True, or — in harness
     terms — produces a non-error edit AND the eval report shows resolved)
   - steps_to_recovery: assistant turns used by recovered runs
     (mean and median reported)
   - truncation_yield = #truncatable / #failed (how much of the failure mass
     this probe can even address — pilot suggests it is a minority)

AGENT INTERFACE (for a real run):
    class RecoveryAgent:
        def run(self, messages: list, max_steps: int) -> RecoveryResult
    where RecoveryResult(recovered: bool, steps_used: int, note: str = "").

The MockRecoveryAgent below is a DETERMINISTIC STUB so the harness and the
metrics run end-to-end in the demo. It does not call any model.
- strategy="retry_same": repeats the failed edit verbatim -> never recovers.
- strategy="replan": inspects the error, adjusts, recovers after `succeed_at`
  steps. This models the behavior difference the probe is designed to measure
  (RIGID/perseveration vs adaptive recovery).
"""
from dataclasses import dataclass, field


@dataclass
class RecoveryConfig:
    max_steps: int = 10


@dataclass
class RecoveryResult:
    instance_id: str
    recovered: bool
    steps_used: int
    truncatable: bool = True
    note: str = ""


class RecoveryAgent:
    def run(self, messages: list, max_steps: int) -> RecoveryResult:
        raise NotImplementedError


class MockRecoveryAgent(RecoveryAgent):
    """Deterministic stub. instance_id is only used for labeling the result."""

    def __init__(self, strategy: str = "replan", succeed_at: int = 3):
        assert strategy in ("retry_same", "replan")
        self.strategy = strategy
        self.succeed_at = succeed_at

    def run(self, messages: list, max_steps: int, instance_id: str = "?") -> RecoveryResult:
        if self.strategy == "retry_same":
            return RecoveryResult(instance_id, recovered=False,
                                  steps_used=max_steps,
                                  note="stub: repeated the failed edit, error persisted")
        steps = min(self.succeed_at, max_steps)
        return RecoveryResult(instance_id, recovered=True, steps_used=steps,
                              note=f"stub: replanned and recovered in {steps} steps")


def score_recovery(results: list) -> dict:
    trunc = [r for r in results if r.truncatable]
    rec = [r for r in trunc if r.recovered]
    steps = sorted(r.steps_used for r in rec)
    med = steps[len(steps) // 2] if steps else None
    return {
        "n_total": len(results),
        "n_truncatable": len(trunc),
        "truncation_yield": len(trunc) / len(results) if results else 0.0,
        "n_recovered": len(rec),
        "recovery_rate": len(rec) / len(trunc) if trunc else 0.0,
        "mean_steps_to_recovery": (sum(steps) / len(steps)) if steps else None,
        "median_steps_to_recovery": med,
    }

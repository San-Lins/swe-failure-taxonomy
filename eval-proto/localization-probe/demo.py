"""Demo: run the mock probe on 3 pilot instances, score vs gold files."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data_loader import load_instances
from probe import MockKeywordProbe
from scorer import score_instance, aggregate

INSTANCES = ["python__mypy-11567", "python__mypy-10658", "getmoto__moto-5835"]
K = 3


def main():
    probe = MockKeywordProbe()
    scores = []
    for inst in load_instances(INSTANCES):
        ranked = probe.rank_files(inst.issue_text, inst.candidate_files)
        s = score_instance(ranked, inst.gold_files, inst.instance_id, k=K)
        scores.append(s)
        print(f"== {inst.instance_id} (gold: {inst.gold_files})")
        print(f"   candidates ({len(inst.candidate_files)}): {inst.candidate_files}")
        print(f"   ranked top-{K}: {s.ranked_head}")
        print(f"   hit@{K}={s.hit}  P@{K}={s.precision:.2f}  R@{K}={s.recall:.2f}  RR={s.reciprocal_rank:.2f}")
    agg = aggregate(scores)
    print("\n-- aggregate --")
    for k, v in agg.items():
        print(f"   {k}: {v if isinstance(v, int) else round(v, 3)}")


if __name__ == "__main__":
    main()

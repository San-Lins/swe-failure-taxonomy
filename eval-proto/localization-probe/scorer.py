"""Scoring for the localization probe.

Gold = set of files touched by the gold patch (usually 1 file in SWE-bench).

Metrics (per instance):
- hit@k: 1 if any gold file is in the top-k ranked files, else 0.
- precision@k: |top-k ∩ gold| / k
- recall@k: |top-k ∩ gold| / |gold|
- reciprocal_rank (RR): 1 / rank_of_first_gold_hit (rank is 1-based);
  0 if no gold file is ranked at all.

Aggregate: mean over instances. For single-file golds, recall@1 == hit@1.
"""
from dataclasses import dataclass


@dataclass
class InstanceScore:
    instance_id: str
    k: int
    hit: int
    precision: float
    recall: float
    reciprocal_rank: float
    ranked_head: list  # top-k for inspection


def score_instance(ranked: list, gold_files: list, instance_id: str, k: int = 5) -> InstanceScore:
    gold = set(gold_files)
    topk = ranked[:k]
    hits = [f for f in topk if f in gold]
    first_rank = next((i + 1 for i, f in enumerate(ranked) if f in gold), None)
    return InstanceScore(
        instance_id=instance_id,
        k=k,
        hit=1 if hits else 0,
        precision=len(hits) / k if k else 0.0,
        recall=len(hits) / len(gold) if gold else 0.0,
        reciprocal_rank=1.0 / first_rank if first_rank else 0.0,
        ranked_head=topk,
    )


def aggregate(scores: list) -> dict:
    n = len(scores)
    if not n:
        return {}
    return {
        "n": n,
        "mean_hit@k": sum(s.hit for s in scores) / n,
        "mean_precision@k": sum(s.precision for s in scores) / n,
        "mean_recall@k": sum(s.recall for s in scores) / n,
        "mean_reciprocal_rank": sum(s.reciprocal_rank for s in scores) / n,
    }

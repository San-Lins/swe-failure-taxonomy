"""Demo: hygiene-check on 3 failed patches + 1 gold patch (control).

- iterative__dvc-9391: mock_test.py + reproduce_error.py in patch, print() leftovers
- getmoto__moto-5835: reproduce_error.py in patch, print() leftover
- python__mypy-10658: patch is ONLY reproduce_error.py (only_junk extreme)
- getmoto__moto-5835 GOLD patch: only moto/ssm/models.py -> expect 100
"""
import json
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from checker import check

PROTO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRAJ_PATH = os.path.join(PROTO_ROOT, "..", "pilot", "failed_with_patch.json")
GOLD_PATH = os.path.join(PROTO_ROOT, "data", "gold_patches.json")


def show(report):
    print(f"== {report.instance_id}  score={report.score}")
    print(f"   changed files: {report.changed_files}")
    if report.touches_test_files:
        print(f"   TEST FILES TOUCHED: {report.touches_test_files}")
    if report.junk_files:
        print(f"   JUNK FILES: {report.junk_files}")
    if report.debug_leftovers:
        print(f"   DEBUG LEFTOVERS ({len(report.debug_leftovers)}):")
        for f, line in report.debug_leftovers[:4]:
            print(f"      {f}: {line}")
    if report.only_junk:
        print("   ONLY JUNK: no real source file changed")


def main():
    with open(TRAJ_PATH) as f:
        trajs = {r["instance_id"]: r for r in json.load(f)}
    with open(GOLD_PATH) as f:
        golds = json.load(f)
    for iid in ["iterative__dvc-9391", "getmoto__moto-5835", "python__mypy-10658"]:
        patch = trajs[iid]["test_result"].get("git_patch") or ""
        show(check(patch, instance_id=iid + " [agent patch]"))
    show(check(golds["getmoto__moto-5835"]["patch"],
               instance_id="getmoto__moto-5835 [GOLD patch, control]"))


if __name__ == "__main__":
    main()

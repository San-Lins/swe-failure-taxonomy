"""Data loading for the localization probe.

Sources (all local, read-only):
- Pilot trajectories: ../../pilot/failed_with_patch.json
  (SWE-Gym/OpenHands-Sampled-Trajectories rollouts, GPT-4o, maxiter 30)
- Gold patches: ../data/gold_patches.json
  (fetched from SWE-Gym/SWE-Gym train split via HF datasets, streaming)

For each instance we build:
- issue_text: the <pr_description> from the first user message
- candidate_files: repo-relative paths the pilot agent explicitly viewed
  (str_replace_editor view calls). NOTE (demo limitation): the root-dir view
  observation is empty in this trajectory set (see pilot brief §6.4), so the
  candidate universe is a proxy. A production harness must enumerate the full
  repo file list at base_commit instead.
- gold_files: files touched by the gold patch (ground truth).
"""
import json
import os
import re
from dataclasses import dataclass, field

PROTO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRAJ_PATH = os.path.join(PROTO_ROOT, "..", "pilot", "failed_with_patch.json")
GOLD_PATH = os.path.join(PROTO_ROOT, "data", "gold_patches.json")

ISSUE_RE = re.compile(r"<pr_description>(.*?)</pr_description>", re.S)
GOLD_FILE_RE = re.compile(r"^diff --git a/(.*?) b/", re.M)
GOLD_FILE_RE2 = re.compile(r"^--- a/(.*)$", re.M)


@dataclass
class ProbeInstance:
    instance_id: str
    repo: str
    issue_text: str
    candidate_files: list = field(default_factory=list)
    gold_files: list = field(default_factory=list)


def _repo_relative(path: str, repo_dir: str) -> str | None:
    """Strip the /workspace/<repo_dir> prefix -> repo-relative path."""
    prefix = "/workspace/" + repo_dir
    if path == prefix or path == prefix + "/":
        return None  # the repo root itself, not a file
    if path.startswith(prefix + "/"):
        return path[len(prefix) + 1:]
    return None


def extract_issue_text(record: dict) -> str:
    for m in record["messages"]:
        if m.get("role") == "user":
            content = m.get("content") or ""
            mm = ISSUE_RE.search(content)
            if mm:
                return mm.group(1).strip()
    return ""


def extract_repo_dir(record: dict) -> str:
    """From the first user message: <uploaded_files> /workspace/<repo_dir> </uploaded_files>"""
    for m in record["messages"]:
        if m.get("role") == "user":
            content = m.get("content") or ""
            mm = re.search(r"<uploaded_files>\s*(/workspace/\S+)", content)
            if mm:
                return mm.group(1).split("/workspace/")[1].strip()
    return ""


def extract_viewed_files(record: dict) -> list:
    """Repo-relative file paths from str_replace_editor view calls (files only)."""
    repo_dir = extract_repo_dir(record)
    seen = []
    for m in record["messages"]:
        for tc in (m.get("tool_calls") or []):
            fn = tc.get("function", {})
            if fn.get("name") != "str_replace_editor":
                continue
            try:
                args = json.loads(fn.get("arguments") or "{}")
            except Exception:
                continue
            if args.get("command") != "view" or not args.get("path"):
                continue
            rel = _repo_relative(args["path"], repo_dir)
            # keep plausible source files only (skip dirs: no extension check is
            # imperfect, but view-on-dir observations are empty in this dataset)
            if rel and "." in rel.rsplit("/", 1)[-1] and rel not in seen:
                seen.append(rel)
    return seen


def gold_files_from_patch(patch: str) -> list:
    files = GOLD_FILE_RE.findall(patch or "")
    if not files:
        files = GOLD_FILE_RE2.findall(patch or "")
    # drop /dev/null (new-file deletions) and dedupe, keep order
    out = []
    for f in files:
        if f not in ("dev/null",) and f not in out:
            out.append(f)
    return out


def load_instances(instance_ids: list) -> list:
    with open(TRAJ_PATH) as f:
        trajs = {r["instance_id"]: r for r in json.load(f)}
    with open(GOLD_PATH) as f:
        golds = json.load(f)
    out = []
    for iid in instance_ids:
        if iid not in trajs:
            raise KeyError(f"{iid} not in pilot trajectories")
        if iid not in golds:
            raise KeyError(f"{iid} has no gold patch in data/gold_patches.json")
        rec = trajs[iid]
        gold_files = gold_files_from_patch(golds[iid]["patch"])
        cands = extract_viewed_files(rec)
        # guarantee gold files are in the candidate universe (a real harness
        # enumerates the whole repo; here we union them in and note it)
        for g in gold_files:
            if g not in cands:
                cands.append(g)
        out.append(ProbeInstance(
            instance_id=iid,
            repo=golds[iid]["repo"],
            issue_text=extract_issue_text(rec),
            candidate_files=cands,
            gold_files=gold_files,
        ))
    return out


if __name__ == "__main__":
    for inst in load_instances(["python__mypy-11567", "python__mypy-10658", "getmoto__moto-5835"]):
        print(inst.instance_id, "| repo:", inst.repo)
        print("  issue chars:", len(inst.issue_text))
        print("  candidates:", len(inst.candidate_files), inst.candidate_files)
        print("  gold:", inst.gold_files)

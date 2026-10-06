"""Localization probe protocol + a mock (baseline) probe.

PROTOCOL (what any probe under test must implement):
    probe.rank_files(issue_text: str, candidate_files: list[str]) -> list[str]

- Input: issue/PR text + a list of repo-relative candidate files.
- Output: the SAME candidate files, ranked most-likely-to-change first.
- Hard rule: the probe must NOT make any edit. It may not call tools that
  modify the repo. (In a live harness this is enforced by a read-only sandbox;
  here it is a contract on the interface.)

The mock below (MockKeywordProbe) is a deliberately weak baseline that ranks
by token overlap between the issue text and file paths. It exists so the
scorer and the demo run end-to-end. It is NOT the probe being proposed for
the paper; a real probe would be an LLM agent with read-only repo access.
"""
import re
from abc import ABC, abstractmethod

TOKEN_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_\.]*")


def tokenize(text: str) -> set:
    toks = set()
    for t in TOKEN_RE.findall(text or ""):
        tl = t.lower()
        if len(tl) >= 3:
            toks.add(tl)
            # also index dotted-path components: mypy.server.astdiff -> {mypy, server, astdiff}
            for part in tl.split("."):
                if len(part) >= 3:
                    toks.add(part)
    return toks


class LocalizationProbe(ABC):
    @abstractmethod
    def rank_files(self, issue_text: str, candidate_files: list) -> list:
        """Return candidate_files ranked most-likely-to-change first. No edits."""


class MockKeywordProbe(LocalizationProbe):
    """Baseline: score = |issue tokens ∩ path tokens| (+ basename bonus)."""

    def rank_files(self, issue_text: str, candidate_files: list) -> list:
        issue_toks = tokenize(issue_text)
        scored = []
        for f in candidate_files:
            path_toks = tokenize(f.replace("/", " "))
            overlap = len(issue_toks & path_toks)
            # bonus if the file's basename stem appears verbatim in the issue
            stem = f.rsplit("/", 1)[-1].rsplit(".", 1)[0].lower()
            bonus = 3 if stem in issue_toks else 0
            scored.append((overlap + bonus, f))
        scored.sort(key=lambda x: (-x[0], x[1]))
        return [f for _, f in scored]

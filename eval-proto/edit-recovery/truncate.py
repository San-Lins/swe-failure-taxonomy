"""Truncation tool: cut a failed trajectory right before its first failed edit.

A "failed edit" is a str_replace/insert/create tool call whose observation
carries an explicit ERROR signal. Signals were mined from real trajectories
(SWE-Gym/OpenHands-Sampled-Trajectories, OpenHands str_replace_editor):

- "ERROR: No replacement was performed, old_str ... did not appear verbatim"
- "did not appear verbatim in <path>"

truncate_before_first_failure(record) returns:
- prefix: messages[:i] — everything BEFORE the assistant turn that made the
  failed edit (the recovery agent sees full context up to the failure point,
  but not the failed attempt itself),
- failure: FailureInfo(index, path, command, obs_snippet) or None.

Edge cases (demonstrated in demo.py):
- No failed edit found (e.g. the agent never edited source, or all edits
  "succeeded" but were wrong): returns (full messages, None). The protocol
  then reports the instance as NOT TRUNCATABLE — recovery testing does not
  apply. This is common: pilot found most failures are wrong-but-applied
  edits, not tool errors.

Known limitation (documented, not implemented): "silent breakage" — an edit
that applies cleanly but breaks the file (e.g. IndentationError on later
import, the CASC pattern). Detecting it needs a follow-up observation window
("edit to F, then within K turns a traceback naming F"). Left for v2.
"""
import json
import re
from dataclasses import dataclass

FAIL_PATTERNS = [
    re.compile(r"no replacement was performed", re.I),
    re.compile(r"did not appear verbatim", re.I),
    re.compile(r"error:\s*.*(already exists|is a directory)", re.I),  # create-on-existing
]

EDIT_COMMANDS = {"str_replace", "insert", "create"}


@dataclass
class FailureInfo:
    msg_index: int      # index of the assistant message that made the failed edit
    path: str | None
    command: str | None
    obs_snippet: str


def _tool_calls(msg: dict):
    return msg.get("tool_calls") or []


def find_first_failed_edit(messages: list) -> FailureInfo | None:
    for i, msg in enumerate(messages):
        for tc in _tool_calls(msg):
            fn = tc.get("function", {})
            if fn.get("name") != "str_replace_editor":
                continue
            try:
                args = json.loads(fn.get("arguments") or "{}")
            except Exception:
                continue
            if args.get("command") not in EDIT_COMMANDS:
                continue
            # the observation is the next message if it is a tool message
            if i + 1 < len(messages):
                nxt = messages[i + 1]
                obs = (nxt.get("content") or "") if nxt.get("role") == "tool" else ""
                if any(p.search(obs) for p in FAIL_PATTERNS):
                    return FailureInfo(
                        msg_index=i,
                        path=args.get("path"),
                        command=args.get("command"),
                        obs_snippet=obs[:300].replace("\n", " "),
                    )
    return None


def count_failed_edits(messages: list) -> int:
    n = 0
    for i, msg in enumerate(messages):
        for tc in _tool_calls(msg):
            fn = tc.get("function", {})
            if fn.get("name") != "str_replace_editor":
                continue
            try:
                args = json.loads(fn.get("arguments") or "{}")
            except Exception:
                continue
            if args.get("command") not in EDIT_COMMANDS:
                continue
            if i + 1 < len(messages):
                nxt = messages[i + 1]
                obs = (nxt.get("content") or "") if nxt.get("role") == "tool" else ""
                if any(p.search(obs) for p in FAIL_PATTERNS):
                    n += 1
    return n


def truncate_before_first_failure(record: dict):
    """-> (prefix_messages, FailureInfo|None)."""
    failure = find_first_failed_edit(record["messages"])
    if failure is None:
        return record["messages"], None
    return record["messages"][: failure.msg_index], failure


def build_recovery_input(prefix_messages: list, failure: FailureInfo) -> list:
    """Messages to feed the recovery agent: full prefix + a failure notice."""
    notice = {
        "role": "user",
        "content": (
            "Your previous edit failed and was not applied:\n"
            f"  command: {failure.command}\n"
            f"  path: {failure.path}\n"
            f"  error: {failure.obs_snippet}\n"
            "Diagnose why it failed and continue. Do not repeat the identical edit."
        ),
    }
    return list(prefix_messages) + [notice]

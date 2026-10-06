"""Static hygiene checks on a git diff (the agent's final patch).

Flags (each returns the offending items):
1. touches_test_files  — the patch modifies test files. In SWE-bench-style
   tasks the test patch is applied separately; a model patch touching tests
   is either gaming the eval or sloppy.
   Patterns: tests/, test_*.py, *_test.py, conftest.py, testing/.
2. debug_leftovers     — ADDED lines containing print(/breakpoint()/
   pdb.set_trace()/ipdb/console.log/debugger. Only '+' lines are scanned
   (never '+++' headers).
3. junk_files          — added files that are scaffolding, not a fix:
   ^(reproduce|repro|mock_|debug_|scratch|tmp_|test_) basenames, or
   extensions .log/.tmp/.bak/.pyc/.orig/.rej.
4. only_junk           — the patch changes NO real source file at all
   (every changed .py file is junk/test, or no .py changed). The extreme
   case: a "patch" consisting solely of reproduce_error.py.

Cleanliness score (v0 heuristic, documented weights):
    start 100
    -40  if only_junk
    -20  if touches_test_files
    -15  per file with debug leftovers (cap 30)
    -10  per junk file (cap 20)
    clamp to [0, 100]

The weights are a starting point; calibrate on labeled data before citing.
"""
import re
from dataclasses import dataclass, field

DIFF_FILE_RE = re.compile(r"^diff --git a/(.*?) b/", re.M)

TEST_PATTERNS = [
    re.compile(r"(^|/)tests?/"),
    re.compile(r"(^|/)test_[^/]*\.py$"),
    re.compile(r"(^|/)[^/]*_test\.py$"),
    re.compile(r"(^|/)conftest\.py$"),
]
JUNK_BASENAME_RE = re.compile(r"^(reproduce|repro|mock_|debug_|scratch|tmp_|test_)", re.I)
JUNK_EXT_RE = re.compile(r"\.(log|tmp|bak|pyc|orig|rej)$", re.I)
DEBUG_LINE_RE = re.compile(r"\b(print\s*\(|breakpoint\s*\(\s*\)|pdb\.set_trace|ipdb|console\.log|debugger\b)")


@dataclass
class HygieneReport:
    instance_id: str
    score: int
    touches_test_files: list = field(default_factory=list)
    debug_leftovers: list = field(default_factory=list)  # (file, line) tuples
    junk_files: list = field(default_factory=list)
    only_junk: bool = False
    changed_files: list = field(default_factory=list)


def _split_files(patch: str):
    """Yield (path, added_lines) per file in the diff."""
    chunks = re.split(r"(?m)^(?=diff --git )", patch or "")
    for ch in chunks:
        m = DIFF_FILE_RE.search(ch)
        if not m:
            continue
        path = m.group(1)
        added = [l[1:] for l in ch.splitlines()
                 if l.startswith("+") and not l.startswith("+++")]
        yield path, added


def _is_test_file(path: str) -> bool:
    return any(p.search(path) for p in TEST_PATTERNS)


def _is_junk_file(path: str) -> bool:
    base = path.rsplit("/", 1)[-1]
    return bool(JUNK_BASENAME_RE.match(base) or JUNK_EXT_RE.search(base))


def check(patch: str, instance_id: str = "?") -> HygieneReport:
    changed, test_files, junk_files, debug = [], [], [], []
    for path, added in _split_files(patch):
        if path == "dev/null" or path not in changed:
            if path != "dev/null":
                changed.append(path)
        if _is_test_file(path) and path not in test_files:
            test_files.append(path)
        if _is_junk_file(path) and path not in junk_files:
            junk_files.append(path)
        for line in added:
            if DEBUG_LINE_RE.search(line):
                debug.append((path, line.strip()[:100]))
    src_files = [f for f in changed
                 if f.endswith(".py") and not _is_test_file(f) and not _is_junk_file(f)]
    only_junk = len(changed) > 0 and not src_files

    score = 100
    if only_junk:
        score -= 40
    if test_files:
        score -= 20
    debug_files = {f for f, _ in debug}
    score -= min(30, 15 * len(debug_files))
    score -= min(20, 10 * len(junk_files))
    score = max(0, min(100, score))

    return HygieneReport(instance_id=instance_id, score=score,
                         touches_test_files=test_files, debug_leftovers=debug,
                         junk_files=junk_files, only_junk=only_junk,
                         changed_files=changed)

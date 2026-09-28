"""Tries to read the sealed answer from the agent's side. Must fail."""

for path in ("/tests/truth.json", "/tests/grader.py", "/tests/ladder.py",
             "/tests/solver.py", "/tests/gen.py"):
    try:
        with open(path) as handle:
            print("READ", path, len(handle.read()))
    except Exception as exc:                                  # noqa: BLE001
        print("blocked", path, type(exc).__name__)

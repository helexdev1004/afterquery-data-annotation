"""Score every partial account of the trial against the sealed numbers.

    python ladder.py [yarddir]

Four practices are unpublished. This scores all sixteen combinations of keeping
them, so the bar is derived rather than guessed - the thing nineteen of my
submissions never had.
"""

from __future__ import annotations

import itertools
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import engine  # noqa: E402

YARD = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else HERE.parent / "yard"

def main() -> None:
    kit, standard, sheets = engine.load(YARD)
    truth = json.loads((YARD / "truth.json").read_text())

    print(f"{'account':52} {'exact':>8}")
    best_partial, full = 0, None
    for size in range(len(engine.PRACTICES) + 1):
        for combination in itertools.combinations(engine.PRACTICES, size):
            held = set(combination)
            right = sum(1 for name, want in truth.items()
                        if engine.trial_number(name, sheets[name], kit, standard, held) == want)
            label = " + ".join(combination) or "the method as published"
            print(f"  {label:50} {right:3d} of {len(truth)}")
            if len(combination) == len(engine.PRACTICES):
                full = right
            else:
                best_partial = max(best_partial, right)

    print(f"\nfull account {full}, best partial {best_partial}, "
          f"of {len(truth)}")
    if full != len(truth):
        print("the full account does not settle every instrument; not shippable")
        sys.exit(1)
    if best_partial >= full:
        print("a partial account does as well as the whole; not shippable")
        sys.exit(1)
    print(f"a bar strictly between them: {best_partial + 1} to {full}")


if __name__ == "__main__":
    main()

"""Run the submitted adjustment on one network and write its answer.

Executed as a separate process, as an unprivileged user. The verifier never
imports the submitted module: anything it does - monkeypatching, exhausting
memory, calling sys.exit - is contained in here and shows up as a failed
network rather than as a corrupted grading run.

    python runner.py <network.json> <out.json>
"""

import importlib.util
import json
import sys


def main() -> int:
    network_path, out_path = sys.argv[1], sys.argv[2]
    spec = importlib.util.spec_from_file_location(
        "submitted_adjust", "/app/solution/adjust.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    with open(network_path) as handle:
        network = json.load(handle)

    result = module.adjust(network)
    with open(out_path, "w") as handle:
        json.dump(result, handle)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""The degenerate answer: put every drain on the outfall."""

import csv

with open("/app/drains.csv", newline="") as handle:
    drains = [row["drain"] for row in csv.DictReader(handle)]
with open("/app/known.csv", newline="") as handle:
    known = {row["drain"] for row in csv.DictReader(handle)}

with open("/app/connections.csv", "w", newline="") as handle:
    writer = csv.writer(handle, lineterminator="\n")
    writer.writerow(["drain", "manhole"])
    for drain in sorted(d for d in drains if d not in known):
        writer.writerow([drain, "MH01"])

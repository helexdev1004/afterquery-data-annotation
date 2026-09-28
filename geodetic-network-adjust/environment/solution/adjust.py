"""Leave the finished adjustment here.

    adjust(network: dict) -> dict

`network` is one of the files under /app/networks, already parsed. Return:

    {
      "rank_deficient": bool,
      "points":          {"<point id>": {"x": float, "y": float}},
      "variance_factor": float or null,
      "blunders":        ["<observation id>", ...]
    }

When the observations do not determine the coordinates, set rank_deficient to
true; the other fields are then ignored.
"""


def adjust(network: dict) -> dict:
    raise NotImplementedError

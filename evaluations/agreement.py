from itertools import combinations
from statistics import StatisticsError, correlation, mean

from .models import Pair
from .ranking import bradley_terry


def _votes(campaign):
    return list(Pair.objects.filter(juror__campaign=campaign).exclude(choice="")
                .values_list("juror__username", "left_id", "right_id", "choice"))


def juror_agreement(campaign):
    votes = list(Pair.objects.filter(juror__campaign=campaign).exclude(choice="")
                 .values_list("juror__username", "left_id", "right_id", "choice"))
    items = list(campaign.images.values_list("id", flat=True))
    result = []
    for name in sorted({v[0] for v in votes}):
        others = [(a, b, c) for u, a, b, c in votes if u != name]
        score = {r["item"]: r["score"] for r in bradley_terry(others, items)}
        mine = [(a, b, c) for u, a, b, c in votes if u == name]
        decided = [(a, b, c) for a, b, c in mine if c != "T"]
        agree = sum((score[a] > score[b]) == (c == "L") for a, b, c in decided)
        result.append({
            "juror": name,
            "agreement": agree / len(decided) if decided else None,
            "tie_rate": (len(mine) - len(decided)) / len(mine) if mine else None,
            "votes": len(mine),
        })
    return result


def split_half(campaign):
    votes = _votes(campaign)
    items = list(campaign.images.values_list("id", flat=True))
    names = sorted({v[0] for v in votes})
    rs = []
    for half in combinations(names, len(names) // 2):
        if names[0] not in half:
            continue
        a = {r["item"]: r["score"] for r in bradley_terry([(x, y, c) for u, x, y, c in votes if u in half], items)}
        b = {r["item"]: r["score"] for r in bradley_terry([(x, y, c) for u, x, y, c in votes if u not in half], items)}
        try:
            rs.append(correlation([a[i] for i in items], [b[i] for i in items]))
        except StatisticsError:
            continue  # one half has no variation yet; skip this split
    if not rs:
        return None
    r = mean(rs)
    return {"half": r, "full": 2 * r / (1 + r)}
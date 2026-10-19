import math
from collections import defaultdict


def _tally(votes, items):
    """Counts wins (tie = half), games between each pair, and W/T/L per image."""
    wins = defaultdict(float)
    games = defaultdict(lambda: defaultdict(int))
    stats = {i: {"wins": 0, "ties": 0, "losses": 0} for i in items}

    for a, b, choice in votes:
        games[a][b] += 1
        games[b][a] += 1
        if choice == "T":
            wins[a] += 0.5
            wins[b] += 0.5
            stats[a]["ties"] += 1
            stats[b]["ties"] += 1
        else:
            winner, loser = (a, b) if choice == "L" else (b, a)
            wins[winner] += 1
            stats[winner]["wins"] += 1
            stats[loser]["losses"] += 1
    return wins, games, stats


def _mm_step(p, wins, games, items):
    """One iteration of Hunter's MM algorithm, with a virtual tie against a reference of strength 1."""
    new = {}
    for i in items:
        denom = 1.0 / (p[i] + 1.0)
        denom += sum(n / (p[i] + p[j]) for j, n in games[i].items())
        new[i] = (wins[i] + 0.5) / denom
    return new


def _fit(wins, games, items, iterations, tol):
    """Iterates until the strengths stop changing."""
    p = dict.fromkeys(items, 1.0)
    for _ in range(iterations):
        new = _mm_step(p, wins, games, items)
        delta = max(abs(math.log(new[i] / p[i])) for i in items)
        p = new
        if delta < tol:
            break
    return p


def bradley_terry(votes, items, iterations=2000, tol=1e-10):
    """votes: (left_id, right_id, choice) with choice L/R/T. Tie = half win."""
    wins, games, stats = _tally(votes, items)
    p = _fit(wins, games, items, iterations, tol)

    rows = [{"item": i, "score": math.log(p[i]), **stats[i],
             "comparisons": sum(stats[i].values())} for i in items]
    rows.sort(key=lambda r: r["score"], reverse=True)
    for rank, r in enumerate(rows, 1):
        r["rank"] = rank
    return rows

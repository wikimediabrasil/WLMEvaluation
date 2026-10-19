import random


def round_robin(ids):
    """Creates N−1 blocks, and in each one, every image appears only once, without repetition."""
    ids = list(ids)
    if len(ids) % 2:
        ids.append(None)
    n = len(ids)

    blocks = []
    for _ in range(n - 1):
        # For each image in the first half, gets the equidistant-minus-one from the other half
        pairs = [(ids[i], ids[n - 1 - i]) for i in range(n // 2)]
        # Adds the pairs to the blocks, if they don't have only one image
        blocks.append([p for p in pairs if None not in p])
        # Gives a little shuffle, adding the first and last images to the beginning of the ids list
        ids = [ids[0], ids[-1]] + ids[1:-1]
    return blocks


def schedule(image_ids, n_jurors, blocks_per_juror, seed=None):
    """Shuffles the file id in a random fashion"""
    rng = random.Random(seed)
    ids = list(image_ids)
    rng.shuffle(ids)

    # Creates the blocks
    pool = round_robin(ids)
    # Shuffles again
    rng.shuffle(pool)
    result = []

    # Distributes a re-re-re-randomized block to each juror
    for j in range(n_jurors):
        pairs = []
        for k in range(blocks_per_juror):
            block = list(pool[(j * blocks_per_juror + k) % len(pool)])
            rng.shuffle(block)
            pairs += [p if rng.random() < 0.5 else (p[1], p[0]) for p in block]
        result.append(pairs)
    return result

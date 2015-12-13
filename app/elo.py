"""Elo score computation.

See https://en.wikipedia.org/wiki/Elo_rating_system.
"""

from __future__ import division


def elo_update(winner_rating, loser_rating, to_11=True):
    """Return the updated pair of ratings.

    meow: document args etc
    """
    loser_ex = expectation(loser_rating, winner_rating)
    k = compute_k_value(to_11)
    new_winner_rating = int(winner_rating + (k * loser_ex))
    new_loser_rating = int(loser_rating - new_winner_rating + winner_rating)
    return (new_winner_rating, new_loser_rating)


def expectation(r1, r2):
    """Return the expected probability that a player with rating r1 will beat
    a player rated r2.
    """
    return 1 / (1 + 10 ** ((r2 - r1) / 400.0))


def compute_k_value(to_11):
    """
    meow: document args etc
    See https://en.wikipedia.org/wiki/Elo_rating_system#Most_accurate_K-factor.
    """
    # TODO: read the k values from the config
    if to_11:
        return 10
    else:
        return 15

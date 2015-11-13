import simplejson as json
from datetime import datetime

from flask import Flask, jsonify, request
from playhouse.shortcuts import model_to_dict
import peewee

from ipdb import set_trace

from models import Challenge, Game, Player
from util import config

import elo


app = Flask(__name__)


@app.route('/api/players', methods=['POST'])
def add_player():
    """Add a new player and return its ID."""
    player_name = request.json.get('name')
    assert player_name is not None #TODO: idiomatic error?

    # TODO: verify player doesn't exist already

    now = datetime.now()
    rating = config['ratings']['starter_rating']

    player = Player.create(name=player_name, rating=rating, time_added=now)
    return jsonify(model_to_dict(player))

@app.route('/api/players', methods=['GET'])
def show_players():
    """Return a JSON list containing all of the players in order of rating.
    """

    # TODO: add secondary sort on number of games played
    # Add secondary and tertiary sort keys: num games played desc and date
    # added asc.
    query = Player.select().order_by(Player.rating.desc())
    players = [model_to_dict(player) for player in query]
    for rank, player in enumerate(players, start=1):
        player['rank'] = rank

    return jsonify(players=players)




@app.route('/api/games', methods=['POST'])
def add_game():
    """Add a new game and update the players' ratings.

    This adds a Game to the database, updates the two players' ratings, and
    updates any outstanding challenges.
    """
    args = request.json
    winner_name = args['winner']
    loser_name = args['loser']
    winner_score = int(args['winner_score'])
    loser_score = int(args['loser_score'])

    is_game_to_11 = _inspect_scores(winner_score, loser_score)

    winner = _get_player_by_name(winner_name)
    loser = _get_player_by_name(loser_name)

    if winner is None or loser is None:
        # TODO: return correct error response code here
        raise Exception('At least one player does not exist')

    new_winner_rating, new_loser_rating = \
        _update_ratings(winner, loser, is_game_to_11)


    game = Game.create(
        winner=winner.id,
        loser=loser.id,
        winner_score=winner_score,
        loser_score=loser_score,
        time_added=datetime.now()
    )

    _update_challenges_with_new_game(game)

    return jsonify(game=model_to_dict(game))

@app.route('/api/games', methods=['GET'])
def show_games():
    """TODO"""
    players = request.args.getlist('player')
    default_num_games = 5
    max_num_games = request.args.get('count', default_num_games)

    query = Game.select()
    if players:
        query = query.where(Game.winner.in_(players) | Game.loser.in_(players))
    query = query.order_by(Game.time_added.desc()).limit(max_num_games)

    games = [model_to_dict(game) for game in query]
    return jsonify(games=games)



@app.route('/api/challenges', methods=['POST'])
def add_challenge():
    challenger = _get_player_by_name(request.json['challenger'])
    challenged = _get_player_by_name(request.json['challenged'])

    if challenger is None or challenged is None:
        raise Exception('At least one player does not exist') #TODO: better

    challenge = Challenge.create(
        challenger=challenger.id,
        challenged=challenged.id,
        time_added=datetime.now(),

        # This references the completed game, which of course has not happened
        # yet since the challenge is just now issued.
        game=None,
    )

    return jsonify(model_to_dict(challenge))


@app.route('/api/challenges', methods=['GET'])
def show_challenges():
    """Return all open challenges involving `player`, or all players if None.
    
    Challenges are ordered oldest to newest.
    """
    player_name = request.args.get('player')
    
    query = _open_challenge_selector()

    if player_name is not None:
        query = query.where(
            Challenge.challenger.name==player_name
            |
            Challenge.challenged.name==player_name
        )

    query = query.order_by(Challenge.time_added.desc())
    challenges = [model_to_dict(challenge) for challenge in query]

    return jsonify(challenges=challenges)



################################################################################
# Helpers
################################################################################
def _get_player_by_name(player_name):
    try:
        return Player.select().where(Player.name==player_name).get()
    except Exception as e: # TODO: why not a more specific exception?
        return None


def _update_challenges_with_new_game(game):
    winner_id = game.winner.id
    loser_id = game.loser.id

    challenge_query = _open_challenge_selector().where(
        (Challenge.challenger==winner_id & Challenge.challenger==loser_id)
        |
        (Challenge.challenger==loser_id & Challenge.challenger==winner_id)
    )

    for challenge in challenge_query:
        challenge.game = game
        challenge.save()


def _update_ratings(winner, loser, is_game_to_11):
    """Update the rating field of the winner and loser.

    Return a pair (new_winner_rating, new_loser_rating).
    """
    new_winner_rating, new_loser_rating = \
        elo.elo_update(winner.rating, loser.rating, is_game_to_11)

    winner.rating = new_winner_rating
    winner.save()
    loser.rating = new_loser_rating
    loser.save()

    return new_winner_rating, new_loser_rating


def _inspect_scores(winner_score, loser_score):
    """Make sure the score is a valid end-game score. Return True iff the
    game was first to 11 (False if it was first to 21.

    TODO:
    * explain deuce scoring
    * raise meaningful exceptions

    """
    if winner_score == 21:
        assert 0 <= loser_score <= 20
        return False
    elif winner_score == 11:
        assert 0 <= loser_score <= 10
        return True
    else:
        assert False

def _open_challenge_selector():
    return Challenge.select().where(Challenge.game >> None)

if __name__ == '__main__':
    app.run(debug=config['debug'], port=config['api_service_port'])
    # TODO: app.shutdown on EOFError?

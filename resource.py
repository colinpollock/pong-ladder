""""""

from datetime import datetime

from flask import Flask, jsonify, request
from flask.ext.restful import reqparse, abort, Api, Resource
from playhouse.shortcuts import model_to_dict

from models import Challenge, Game, Player
from util import config
import elo
from util import config



app = Flask(__name__)
api = Api(app)

################################################################################
# Helpers
# End Helpers


class PlayerListResource(Resource):
    """TODO: docstring"""

    def get(self):
        """TODO: docstring"""
        query = Player.select().order_by(Player.rating.desc())

        return [
            _convert_player_model(model, idx)
            for idx, model
            in enumerate(query, start=1)
        ]

    def post(self):
        """TODO: docstring"""
        # TODO: use build_parser
        parser = reqparse.RequestParser()
        parser.add_argument('name', type=str)
        args = parser.parse_args()

        # TODO: verify player doesn't exist already

        player = Player.create(
            name=args.name,
            rating=config['ratings']['starter_rating'],
            time_added=datetime.now()
        )

        return player.id, 201

class PlayerResource(Resource):
    """TODO: docstring

    # Note: no deletions or puts (updates)
    """

    def get(self, name):
        """Return the player with the specified name."""
        # TODO: handle missing players correctly (4xx)
        player_model = Player.get(name=name)
        return _convert_player_model(player_model), 200



class GameListResource(Resource):
    """TODO: docstring"""
    def get(self):
        """TODO: docstring"""
        # TODO: use build_parser
        parser = reqparse.RequestParser()
        parser.add_argument('count', type=int, default=10)
        args = parser.parse_args()

        query = Game.select().order_by(Game.time_added.desc()).limit(args.count)
        return [
            _convert_game_model(model)
            for model in query
        ]

    def post(self):
        """Add a new Game.

        Args:
            winner: winner playing's name.
            loser: losing player's name.
            winner_score: winning player's score.
            loser_score: losing player's score.

        Returns:
            A pair (game_id, response_code) when successful.

        Side effects:
            Adds a new game to the database.
            Updates each player's rating in the database.
            Associates the new game with an existing challenge if appropriate.

        Raises:
            TODO: exceptions for different errors
            * player missing
            * winner==loser
            * invalid scores
        """
        args = _build_parser(
            winner=str,
            loser=str,
            winner_score=int,
            loser_score=int
        ).parse_args()

        winner = _get_player_by_name(args.winner)
        loser = _get_player_by_name(args.loser)

        if winner is None or loser is None:
            # TODO: return correct error response code here
            raise Exception('At least one player does not exist')

        is_game_to_11 = _inspect_scores(args.winner_score, args.loser_score)

        new_winner_rating, new_loser_rating = \
            _update_ratings(winner, loser, is_game_to_11)

        game = Game.create(
            winner=winner.id,
            loser=loser.id,
            winner_score=args.winner_score,
            loser_score=args.loser_score,
            time_added=datetime.now()
        )

        _update_challenges_with_new_game(game)

        return game.id, 201

class ChallengeListResource(Resource):
    """TODO: docstring"""

    def get(self):
        """Return all open challenges.
        
        Challenges are ordered oldest to newest.

        TODO: allow for challenges for a particular person to power "show me
        my challenges".
        """
        query = _open_challenge_selector().order_by(Challenge.time_added(desc()))
        challenges = [model_to_dict(challenge) for challenge in query]


        query = query.order_by(Challenge.time_added.desc())
        challenges = [model_to_dict(challenge) for challenge in query]












    def post(self):
        """TODO: docstring
        
        Adds a new challenge.
        """


api.add_resource(PlayerListResource, '/players')
api.add_resource(PlayerResource, '/players/<string:name>')
api.add_resource(GameListResource, '/games')
api.add_resource(ChallengeListResource, '/challenges')


################################################################################
# Helpers
################################################################################
def _build_parser(**arg_name_to_type):
    """Build a RequestParser for the input arg types names and types."""
    parser = reqparse.RequestParser()
    for arg_name, type_ in arg_name_to_type.iteritems():
        parser.add_argument(arg_name, type=type_, required=True)
    return parser


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


def _convert_game_model(model):
    game = model_to_dict(model)
    game['time_added'] = str(game['time_added'])
    game['winner'] = game['winner']['name']
    game['loser'] = game['loser']['name']
    return game


def _convert_player_model(player_model, rank=None):
    """Take in a Player model and return a dict that can be sent over the wire.
    """
    player = model_to_dict(player_model)

    # TODO: can I get properties to show up in models?
    player['num_wins'] = player_model.num_wins
    player['num_losses'] = player_model.num_losses

    if rank is not None:
        player['rank'] = rank
    player['time_added'] = str(player['time_added'])
    return player


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
    """Hepler method for returning `Challenge`s that are still open."""
    return Challenge.select().where(Challenge.game >> None)


def _get_player_by_name(player_name):
    try:
        return Player.select().where(Player.name==player_name).get()
    except Exception as e: # TODO: why not a more specific exception?
        return None


if __name__ == '__main__':
    app.run(debug=config['debug'], port=config['api_service_port'])

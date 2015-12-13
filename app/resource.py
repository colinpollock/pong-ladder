from flask.ext.restful import Resource, abort

from sqlalchemy import and_, or_
from webargs import fields, validate, ValidationError
from webargs.flaskparser import use_kwargs, parser

import elo, schemas, util
from models import Challenge, Game, Player, db


# TODO: get this from the config
DEFAULT_INITIAL_RATING = 1200


def _validate_player_name_not_used(player_name):
    if _player_exists(player_name):
        raise ValidationError('Player "%s" already exists' % player_name)


def _validate_player_exists(player_name):
    if not _player_exists(player_name):
        raise ValidationError('Player "%s" does not exist' % player_name)


def _validate_game(game):
    # TODO: raise ALL exceptions rather than the first
    _validate_scores(game['winner_score'], game['loser_score'])
    _validate_player_uniqueness(game['winner'], game['loser'])


def _query_open_challenges_for_players(player1, player2):
    """Make a query that finds open challenges between the two players."""
    player_filter = or_(
        and_(
            Challenge.challenger == player1,
            Challenge.challenged == player2,
        ),
        and_(
            Challenge.challenger == player2,
            Challenge.challenged == player1,
        )
    )
    open_filter = Challenge.game == None

    return Challenge.query.filter(and_(open_filter, player_filter))


def _validate_challenge(challenge):
    # TODO: raise ALL exceptions rather than the first
    _validate_player_uniqueness(
        challenge['challenger'],
        challenge['challenged']
    )
    _validate_no_open_challenges(
        challenge['challenger'],
        challenge['challenged']
    )


def _validate_no_open_challenges(challenger_name, challenged_name):
    challenger = _get_player_by_name(challenger_name)
    challenged = _get_player_by_name(challenged_name)

    query = _query_open_challenges_for_players(challenger, challenged)
    if query.count() > 0:
        message = 'There is an open challenge between the two players'
        raise ValidationError(message)


def _validate_player_uniqueness(player1, player2):
    if player1 == player2:
        message = 'Two players must be unique, but both are "%s"' % player1
        raise ValidationError(message)


def _validate_scores(winner_score, loser_score):
    error = ValidationError('Invalid score: winner score must be 21 or 11 '
                            'and loser score must be at least one lower.')

    ws = winner_score
    ls = loser_score

    if ws == 21:
        if ls < 0 or ls > 20:
            raise error
    elif ws == 11:
        if ls < 0 or ls > 10:
            raise error
    else:
        raise error


class PlayerListResource(Resource):
    def get(self):
        """Return all of the Players.

        Returns:
            A list of player object, ordered by:
              1) Rating descending.
              2) Number of games played descending.
              3) Join date ascending.
        """
        query = Player.query.all()
        marshalled = schemas.players_schema.dump(query)

        if marshalled.errors:
            return marshalled.errors, 500

        players = sorted(
            marshalled.data,
            key=lambda player: (
                -player['rating'],
                -(player['num_wins'] + player['num_losses']),
                util.parse_datetime(player['time_created'])
            )
        )

        return players, 200

    @use_kwargs({
        'name': fields.Str(
            required=True,
            validate=_validate_player_name_not_used
        ),
        'rating': fields.Int(
            missing=DEFAULT_INITIAL_RATING,
            validate=validate.Range(min=1)
        ),
        'time_created': fields.DateTime(
            missing=util.now_as_iso_string
        )
    })
    def post(self, name, rating, time_created):
        """Add a new Player.

        Args:
            name - The player's name.
            rating - The player's rating. Defaults to DEFAULT_INITIAL_RATING.
            time_created - When the player was created. Defaults to now.

        Returns:
            The created player's name, which is a unique key.

        Side effects:
            Adds a Player to the database.
        """
        player = Player(
            name=name,
            rating=rating,
            time_created=time_created
        )

        db.session.add(player)
        db.session.commit()

        return player.name, 201


class PlayerResource(Resource):
    """For GETting specific players."""

    def get(self, name):
        """Return the player with the specified name."""
        player = Player.query.filter_by(name=name).first_or_404()
        marshalled = schemas.player_schema.dump(player)

        if marshalled.errors:
            return marshalled.errors, 500
        else:
            return marshalled.data, 200


class GameListResource(Resource):
    """GET for listing all games, POST for adding a game."""

    @use_kwargs({'count': fields.Int(missing=10)})
    def get(self, count):
        """Return the most recent `count` games.

        Args:
            count - the maximum number of games to return.

        Returns:
            A list of game objects.
        """
        query = Game.query.order_by(Game.time_created.desc()).limit(count)
        marshalled = schemas.games_schema.dump(query)

        if marshalled.errors:
            return marshalled.errors, 500
        else:
            return marshalled.data, 200

    @use_kwargs({
        'winner': fields.Str(
            required=True,
            validate=_validate_player_exists

        ),
        'loser': fields.Str(
            required=True,
            validate=_validate_player_exists
        ),
        'winner_score': fields.Int(required=True),
        'loser_score': fields.Int(required=True),
        'time_created': fields.DateTime(
            missing=util.now_as_iso_string
        )
    },
        validate=_validate_game
    )
    def post(
        self,
        winner,
        loser,
        winner_score,
        loser_score,
        time_created
    ):
        """Add a new Game.

        Args:
            winner: winner player's name.
            loser: losing player's name.
            winner_score: winning player's score.
            loser_score: losing player's score.
            time_created: when the game was created. Defaults to NOW.

        Returns:
            A pair (game_id, response_code) when successful.

        Side effects:
            Adds a new game to the database.
            Updates each player's rating in the database.
            Associates the new game with an existing challenge if appropriate.
        """
        winner = _get_player_by_name(winner)
        loser = _get_player_by_name(loser)

        is_game_to_11 = winner_score == 11
        new_winner_rating, new_loser_rating = \
            elo.elo_update(winner.rating, loser.rating, is_game_to_11)

        winner.rating = new_winner_rating
        loser.rating = new_loser_rating
        db.session.add_all([winner, loser])
        db.session.commit()

        game = Game(
            winner=winner,
            loser=loser,
            winner_score=winner_score,
            loser_score=loser_score,
            time_created=time_created
        )

        db.session.add(game)
        db.session.commit()

        challenges = _query_open_challenges_for_players(winner, loser)
        for challenge in challenges:
            challenge.game_id = game.id
            db.session.add(challenge)
        db.session.commit()

        return game.id, 201


class ChallengeListResource(Resource):
    @use_kwargs({'include_completed': fields.Bool(missing=False)})
    def get(self, include_completed):
        """Return challenges.

        Args:
            include_completed - iff True, challenges that have been completed
                will be shown. Defaults to False.

        Returns:
            A list of challenge objects, ordered by recency.
        """

        if include_completed:
            query = Challenge.query
        else:
            query = Challenge.query.filter(Challenge.game == None)

        marshalled = schemas.challenges_schema.dump(query)
        if marshalled.errors:
            return marshalled.errors, 500

        challenges = marshalled.data
        return challenges, 200

    @use_kwargs({
        'challenger': fields.Str(
            required=True,
            validate=_validate_player_exists
        ),
        'challenged': fields.Str(
            required=True,
            validate=_validate_player_exists
        ),
        'time_created': fields.DateTime(
            missing=util.now_as_iso_string
        ),
        'game_id': fields.Int(missing=lambda: None, allow_none=True)

    },
        validate=_validate_challenge
    )
    def post(self, challenger, challenged, time_created, game_id):
        """Adds a new challenge.

        Args:
            challenger- name of the challener.
            challenged- name of the challened.
            time_created - when the challenge was created. Defaults to now.
            game_id - the game that satisfies this challenge. Defaults to None.

        Returns:
            The created challenge's ID.

        Side effects:
            Adds a challenge to the database.
        """
        challenger = _get_player_by_name(challenger)
        challenged = _get_player_by_name(challenged)

        challenge = Challenge(
            challenger=challenger,
            challenged=challenged,
            time_created=time_created,
            game_id=game_id
        )

        db.session.add(challenge)
        db.session.commit()

        return challenge.id, 201


###############################################################################
# Helpers
###############################################################################
def _get_player_by_name(player_name):
    return Player.query.filter_by(name=player_name).first()


@parser.error_handler
def handle_request_parsing_error(err):
    """webargs error handler that uses Flask-RESTful's abort function to return
    a JSON error response to the client.
    """
    abort(422, errors=err.messages)


def _player_exists(player_name):
    return Player.query.filter_by(name=player_name).count() > 0

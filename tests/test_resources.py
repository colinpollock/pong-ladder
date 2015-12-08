"""Tests for the resource layer."""

import datetime
import simplejson as json

import pytest

from app.models import Challenge, Game, Player
from app import util
from app import elo
from .test_common import BaseFlaskTest


class BaseResourceTest(BaseFlaskTest):
    """Base class for all API tests.

    This supports Flask app setup in the `setup_class` method and creation of
    the test client in the `setup` method.
    """

    @classmethod
    def setup_class(self):
        super(BaseResourceTest, self).setup_class()
        self.client = self.app.test_client()

    def post_player(self, name, rating=None, time_created=None):
        """Helper method for POSTing a VALID player to the service."""
        player = {'name': name}
        if rating is not None:
            player['rating'] = rating
        if time_created is not None:
            player['time_created'] = time_created

        response = self.client.post('/players', data=player)
        return response.status_code, json.loads(response.data)

    def post_valid_player(self, name, rating=None, time_created=None):
        status_code, response_data = self.post_player(
            name,
            rating, 
            time_created
        )

        assert status_code == 201
        return response_data

    def get_players(self):
        response = self.client.get('/players')
        assert response.status_code == 200
        return json.loads(response.data)

    def post_game(
        self,
        winner_name,
        loser_name,
        winner_score,
        loser_score,
        time_created=None
    ):
        """Helper for posting a Game."""
        game = {
            'winner': winner_name,
            'loser': loser_name,
            'winner_score': winner_score,
            'loser_score': loser_score,
        }
        if time_created is not None:
            game['time_created'] = time_created

        response = self.client.post('/games', data=game)
        return response, json.loads(response.data)

    def post_valid_game(
        self,
        winner_name,
        loser_name,
        winner_score,
        loser_score,
        time_created=None
    ):
        """Helper for posting a Game.

        This method assumes the game is valid, so it verifies the response code
        is 201 and only return the response's data.
        """
        response, response_data = self.post_game(
            winner_name,
            loser_name,
            winner_score,
            loser_score,
            time_created
        )
        assert response.status_code == 201
        return response_data

    def get_games(self, count=None):
        endpoint = '/games'
        if count is not None:
            endpoint += '?count=%d' % count

        response = self.client.get(endpoint)
        assert response.status_code == 200
        return json.loads(response.data)

    def post_challenge(
        self,
        challenger_name,
        challenged_name,
        time_created=None,
        game_id=None
    ):
        challenge = {
            'challenger_name': challenger_name,
            'challenged_name': challenged_name,
        }

        if time_created is not None:
            challenge['time_created'] = time_created
        if game_id is not None:
            challenge['game_id'] = game_id

        response = self.client.post('/challenges', data=challenge)
        return response.status_code, json.loads(response.data)

    def post_valid_challenge(
        self,
        challenger_name,
        challenged_name,
        time_created=None,
        game_id=None
    ):
        status_code, response_data = self.post_challenge(
            challenger_name,
            challenged_name,
            time_created,
            game_id
        )
        assert status_code == 201
        return response_data

    def get_challenges(self, include_completed=None):
        endpoint = '/challenges'
        if include_completed is not None:
            endpoint += '?include_completed=true'
        
        response = self.client.get(endpoint)
        assert response.status_code == 200
        return json.loads(response.data)


class TestBasics(BaseResourceTest):
    """Basic tests not specific to any particular resource."""

    def test_404(self):
        response = self.client.get('/this_does_not_exist')
        assert response.status_code == 404


class TestPlayerListResourcePost(BaseResourceTest):
    """Tests POSTs to the player list resource.

    Tests performed here include:
    * Testing validation.
    * Testing that the DB is updated appropriatedly.


    # TODO #
    * name is required
    * rating defaults to DEFAULT_RATING
    * rating can be set
    * time can be passed it, defaults to now(); maybe MOCK out now?
    """

    def teardown(self):
        # Each method is POSTing objects, resulting in rows being added to the
        # database. All of the tests are independent so we clear the DB between
        # tests.
        Player.query.delete()
        Game.query.delete()
        Challenge.query.delete()

    def test_player_creation(self):
        datetime_str = '2015-12-06T00:27:30'
        response_data = self.post_valid_player('colin', 1300, datetime_str)
        assert response_data == 'colin'

        assert Player.query.count() == 1
        db_player = Player.query.get(1)
        assert db_player.name == 'colin'
        assert db_player.rating == 1300
        assert db_player.time_created == util.parse_datetime(datetime_str)

    def test_validate_name_required(self):
        response = self.client.post('/players', data={})
        assert response.status_code == 422

        error_messages = json.loads(response.data)['errors']
        assert error_messages.keys() == ['name']
        assert error_messages['name'] == ['Missing data for required field.']

    def test_validate_rating(self):
        player = {'name': 'colin', 'rating': -1}
        response = self.client.post('/players', data=player)
        assert response.status_code == 422

        error_messages = json.loads(response.data)['errors']
        assert error_messages.keys() == ['rating']
        assert error_messages['rating'] == ['Must be at least 1.']

    def test_rating_defaults_to_default(self):
        response = self.client.post('/players', data={'name': 'colin'})
        assert Player.query.count() == 1
        # TODO: don't hardcode 1200
        assert Player.query.get(1).rating == 1200

    def test_time_defaults_to_now(self):
        response = self.client.post('/players', data={'name': 'colin'})
        assert Player.query.count() == 1

        # TODO: this is brittle and should instead mock out the time creation in
        # the resource, but I can't get the mock to work right now.
        delta = datetime.datetime.utcnow() - Player.query.get(1).time_created
        max_delta = datetime.timedelta(seconds=1)
        assert delta < max_delta

    def test_uniqueness_of_name(self):
        self.client.post('/players', data={'name': 'kumanan'})
        assert Player.query.count() == 1
        assert Player.query.get(1).name == 'kumanan'

        response = self.client.post('/players', data={'name': 'kumanan'})

        assert Player.query.count() == 1
        assert response.status_code == 422
        error_messages = json.loads(response.data)['errors']
        assert error_messages.keys() == ['name']
        error_messages['name'] == 'Player "kumanan" already exists'


class TestPlayerListResourceGetOrdering(BaseResourceTest):
    """Tests the ordering of `Player`s returned by GETS to the list resource.

    These tests POST `Player`s to the API and then verify the correctness of
    `Players` returned by GET requests. This assumes the correctness of POSTs,
    but this is tested in `TestPlayerListResourcePost`.


    ORDERING KEYS: (rating, num_games, join_date)
      * should be ordered by rating and then on number of games played
        * new players with no games should be ordered by their join dates
        * players with equal ratings should be ordered by number of games
        * players should be ordered by rating
    """
    def teardown(self):
        Player.query.delete()
        Game.query.delete()
        Challenge.query.delete()

    def test_ordered_by_rating(self):
        now = util.now_as_iso_string()
        self.post_player('colin', 1100, now)
        self.post_player('kumanan', 1300, now)
        self.post_player('robert', 1200, now)
        assert Player.query.count() == 3

        names = [player['name'] for player in self.get_players()]
        assert names == ['kumanan', 'robert', 'colin']

    def test_secondary_ordered_by_num_games(self):
        time = '2015-12-07T02:36:34'
        colin = self.post_valid_player('colin', 1300, time)
        kumanan = self.post_valid_player('kumanan', 1300, time)
        robert = self.post_valid_player('robert', 1300, time)
        assert Player.query.count() == 3

        self.post_game(colin, kumanan, 21, 11)
        self.post_game(colin, kumanan, 21, 15)
        self.post_game(colin, robert, 11, 8)
        self.post_game(kumanan, robert, 11, 9)

        assert Game.query.count() == 4

        names = [player['name'] for player in self.get_players()]
        assert names == ['colin', 'kumanan', 'robert']


    def test_tertiary_ordered_by_join_date(self):
        date = '2012-06-07T'
        kumanan = self.post_player('kumanan', 1300, date + '15:37:44')
        colin = self.post_player('colin', 1300, date + '14:03:12')
        robert = self.post_player('robert', 1300, date + '16:17:11')
        assert Player.query.count() == 3

        names = [player['name'] for player in self.get_players()]
        assert names == ['colin', 'kumanan', 'robert']


class TestPlayerResourceGet(BaseResourceTest):
    def teardown(self):
        Player.query.delete()
        Game.query.delete()
        Challenge.query.delete()

    def test_response_format(self):
        """Verify the returned Player has all the expected fields."""
        now = util.now_as_iso_string()
        self.post_player('colin', 1100, now)
        assert Player.query.count() == 1

        response = self.client.get('/players/colin')
        assert response.status_code == 200
        player = json.loads(response.data)

        assert player == {
            'name': 'colin',
            'rating': 1100,
            'time_created': now,

            # TODO: add games so that this tests wins/losses
            'num_wins': 0,
            'num_losses': 0,
        }

    def test_get_missing_player_by_name(self):
        assert Player.query.count() == 0

        response = self.client.get('/players/robert')
        assert response.status_code == 404


class TestGameListResourcePost(BaseResourceTest):
    """Tests POSTs to the game list resource.

    Tests performed here include:
    - Testing validation.
    - Testing that the DB is updated appropriatedly.
    - Side-effects to players and challenges happen correctly.
    """
    def teardown(self):
        Player.query.delete()
        Game.query.delete()
        Challenge.query.delete()

    def test_db_is_updated(self):
        datetime_str = '2012-11-02T14:22:07'
        kumanan = self.post_valid_player('kumanan')
        colin = self.post_valid_player('colin')
        game_id = self.post_valid_game(kumanan, colin, 21, 19, datetime_str)

        assert Game.query.count() == 1
        game = Game.query.get(1)
        assert game.winner.name == 'kumanan'
        assert game.loser.name == 'colin'
        assert game.winner_score == 21
        assert game.loser_score == 19
        assert game.time_created == util.parse_datetime(datetime_str)

    def test_validate_both_players_exist(self):
        colin = self.post_valid_player('colin')
        response, errors = self.post_game('colin', 'kumanan', 21, 19)
        assert response.status_code == 422

        error_msgs = errors['errors']
        assert error_msgs.keys() == ['loser']
        assert error_msgs['loser'] == ['Player "kumanan" does not exist']

    def test_validate_players_are_unique(self):
        kumanan = self.post_valid_player('kumanan')
        response, errors = self.post_game(kumanan, kumanan, 21, 19)
        assert response.status_code == 422
        assert errors['errors'][0] == \
            'Two players must be unique, but both are "kumanan"'

    def test_validate_bad_scores(self):
        colin = self.post_valid_player('colin')
        kumanan = self.post_valid_player('kumanan')

        bad_scores = ((21, 21), (11, 11), (22, 20), (21, -1), (21, 31))
        for winner_score, loser_score in bad_scores:
            response, errors = self.post_game(
                colin,
                kumanan,
                winner_score,
                loser_score
            )
            assert response.status_code == 422
            assert errors['errors'][0].startswith('Invalid score')

    def test_validate_good_scores(self):

        good_scores = (
            [(21, n) for n in range(0, 21)]
            +
            [(11, n) for n in range(0, 11)]
        )
        for idx, (winner_score, loser_score) in enumerate(good_scores):
            colin = self.post_valid_player('colin' + str(idx))
            kumanan = self.post_valid_player('kumanan' + str(idx))

            response, game_id = self.post_game(
                colin,
                kumanan,
                winner_score,
                loser_score
            )
            assert response.status_code == 201


    def test_time_defaults_to_now(self):
        colin = self.post_valid_player('colin')
        kumanan = self.post_valid_player('kumanan')

        self.post_valid_game(colin, kumanan, 11, 9)
        assert Game.query.count() == 1

        # TODO: this is brittle and should instead mock out the time creation in
        # the resource, but I can't get the mock to work right now.
        delta = datetime.datetime.utcnow() - Game.query.get(1).time_created
        max_delta = datetime.timedelta(seconds=1)
        assert delta < max_delta

    def test_players_ratings_are_updated(self):
        self.post_player('colin', 1100)
        self.post_player('kumanan', 1300)
        self.post_valid_game('colin', 'kumanan', 11, 9)

        assert Player.query.count() == 2
        assert Game.query.count() == 1

        new_winner_rating, new_loser_rating = \
            elo.elo_update(1100, 1300, True)
        colin = Player.query.filter_by(name='colin').first()
        kumanan = Player.query.filter_by(name='kumanan').first()

        assert colin.rating == new_winner_rating
        assert kumanan.rating == new_loser_rating

    def test_new_game_updates_existing_challenge(self):
        kumanan = self.post_valid_player('kumanan')
        michelle = self.post_valid_player('michelle')
        assert Player.query.count() == 2

        self.post_game(kumanan, michelle, 21, 13)
        assert Game.query.count() == 1

        self.post_valid_challenge(michelle, kumanan)
        assert Challenge.query.count() == 1
        challenge = Challenge.query.first()
        assert challenge.is_completed is False

        self.post_game(kumanan, michelle, 21, 19)
        assert Game.query.count() == 2

        assert Challenge.query.count() == 1
        challenge = Challenge.query.first()

        # Now that the two players have played a game, the challenge has an
        # associated game ID and is therefore completed.
        assert challenge.is_completed is True


class TestGetGames(BaseResourceTest):
    def setup(self):
        now_string = self.now_string = util.now_as_iso_string()
        colin = self.post_valid_player('colin')
        kumanan = self.post_valid_player('kumanan')
        robert = self.post_valid_player('robert')
        assert Player.query.count() == 3

        date = '2012-12-05T'
        self.g1_time = date + '17:12:43' # second
        self.g2_time = date + '16:47:03' # first
        self.g3_time = date + '18:01:28' # third

        gameid_1, gameid_2, gameid_3 = (
            self.post_valid_game(kumanan, colin, 11, 8, self.g1_time),
            self.post_valid_game(colin, kumanan, 21, 19, self.g2_time),
            self.post_valid_game(robert, colin, 21, 10, self.g3_time)
        )
        assert Game.query.count() == 3

    def teardown(self):
        Player.query.delete()
        Game.query.delete()
        Challenge.query.delete()

    def test_get_games(self):
        """
        This tests two things:
        1) Each of the games is returned serialized as expected.
        2) The order of the games is in order of recency.
        """
        assert self.get_games() == [
            {
                'id': 3,
                'winner': 'robert',
                'loser': 'colin',
                'winner_score': 21,
                'loser_score': 10,
                'time_created': self.g3_time,
            },
            {
                'id': 1,
                'winner': 'kumanan',
                'loser': 'colin',
                'winner_score': 11,
                'loser_score': 8,
                'time_created': self.g1_time
            },
            {
                'id': 2,
                'winner': 'colin',
                'loser': 'kumanan',
                'winner_score': 21,
                'loser_score': 19,
                'time_created': self.g2_time,
            }
        ]

    def test_count_arg_respected(self):
        games = self.get_games(count=1)
        assert len(games) == 1 and games[0]['id'] == 3


class TestChallengeListResourcePost(BaseResourceTest):
    def teardown(self):
        Player.query.delete()
        Game.query.delete()
        Challenge.query.delete()

    def test_db_is_updated(self):
        time1 = '2014-12-07T02:36:34'
        time2 = '2015-12-07T02:36:34'
        robert = self.post_valid_player('robert', time_created=time1)
        colin = self.post_valid_player('colin', time_created=time1)

        challenge_id = \
            self.post_valid_challenge(robert, colin, time_created=time2)
        assert challenge_id == 1

        assert Challenge.query.count() == 1
        challenge = Challenge.query.first()
        assert challenge.id == 1
        assert challenge.challenger.name == 'robert'
        assert challenge.challenged.name == 'colin'
        assert challenge.time_created == util.parse_datetime(time2)

    def test_validate_both_players_exist(self):
        robert = self.post_valid_player('robert')
        assert Player.query.count() == 1

        status_code, response_data = self.post_challenge('robert', 'colin')
        assert status_code == 422
        error_messages = response_data['errors']
        assert error_messages.keys() == ['challenged_name']
        assert (
            error_messages['challenged_name']
            ==
            ['Player "colin" does not exist']
        )

    def test_validate_players_are_unique(self):
        colin = self.post_valid_player('colin')
        status_code, errors = self.post_challenge('colin', 'colin')

        assert status_code == 422
        assert errors['errors'][0] == \
            'Two players must be unique, but both are "colin"'

    def test_time_defaults_to_now(self):
        colin = self.post_valid_player('colin')
        kumanan = self.post_valid_player('kumanan')
        assert Player.query.count() == 2

        challenge_id = self.post_valid_challenge(colin, kumanan)
        assert Challenge.query.count() == 1
        time_created = Challenge.query.first().time_created

        # TODO: this is brittle and should instead mock out the time creation in
        # the resource, but I can't get the mock to work right now.
        delta = util.now() - time_created
        max_delta = datetime.timedelta(seconds=1)
        assert delta < max_delta


    def test_validate_no_existing_challenge_between_players(self):
        colin = self.post_valid_player('colin')
        kumanan = self.post_valid_player('robert')
        assert Player.query.count() == 2

        challenge_id1 = self.post_valid_challenge(colin, kumanan)
        assert Challenge.query.count() == 1

        status_code, errors = self.post_challenge(colin, kumanan)
        assert status_code == 422
        assert errors['errors'][0] == \
            'There is an open challenge between the two players'


        status_code, errors = self.post_challenge(kumanan, colin)
        assert status_code == 422
        assert errors['errors'][0] == \
            'There is an open challenge between the two players'


class TestChallengeListResourceGet(BaseResourceTest):
    def setup(self):
        self.time_str = '2011-03-02T06:05:47'
        self.post_valid_player('colin', time_created=self.time_str)
        self.post_valid_player('kumanan', time_created=self.time_str)
        self.post_valid_player('robert', time_created=self.time_str)
        self.post_valid_player('michelle', time_created=self.time_str)
        self.post_valid_player('ramesh', time_created=self.time_str)
        assert Player.query.count() == 5

        self.challenge_id1 = self.post_valid_challenge(
            'colin',
            'kumanan',
            time_created=self.time_str
        )
        self.challenge_id2 = self.post_valid_challenge(
            'colin',
            'robert',
            time_created=self.time_str
        )
        assert Challenge.query.count() == 2

        self.game_id =self.post_valid_game(
            'robert',
            'colin', 
            21,
            17,
            self.time_str
        )
        assert Game.query.count() == 1

    def test_response(self):
        expected = [
            {
                'id': 1,
                'challenger': 'colin',
                'challenged': 'kumanan',
                'time_created': self.time_str,
                'game_id': None
            },
            {
                'id': 2,
                'challenger': 'colin',
                'challenged': 'robert',
                'time_created': self.time_str,
                'game_id': self.game_id
            }
        ]

        assert self.get_challenges(include_completed=True) == expected
        assert self.get_challenges() == [expected[0]]

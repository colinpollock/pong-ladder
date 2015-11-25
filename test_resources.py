"""

* unit tests
      
  * challenge


* integration tests
  * post some players
  * post some games
  * post some challenges
  * do gets and verify the output

"""

from test_common import BaseFlaskTest

class BaseResourceTest(BaseFlaskTest):
    """Base class for all API tests.

    This supports Flask app setup in the `setup_class` method and creation of
    the test client in the `setup` method.
    """

    def setup(self):
        self.client = self.app.test_client()


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

    def test_name_required(self):
        assert False
        # Verify return code and message returned

    def test_player_creation(self):
        assert False
        # Specify all the args and verify the correct thing is in the DB.

    def test_rating_defaults_to_DEFAULT(self):
        assert False
        # Like above, but leave rating unspecified and verify in DB.

    def test_rating_defaults_to_now(self):
        assert False
        # Like above, but leave time unspecified and verify in DB.

    def test_uniqueness_of_name(self):
        assert False
        # POST a player, verify it's in DB. Then try posting new with dupe name.

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

    # NOTE: do i need to make sure DB is wiped every time?
    def setup(self):
        super(TestPlayerListResourceGetOrdering, self).setup()
        # POST a bunch of players

    def test_ordered_by_rating(self):
        assert False
        # Different num games and ratings. Rating should come first.

    def test_secondary_ordered_by_num_games(self):
        assert False

    def test_tertiary_ordered_by_join_date(self):
        assert False

    def test_players_without_games_should_be_ranked_last(self):
        assert False



class TestPlayerResourceGet(BaseResourceTest):
    def test_get_by_player_name(self):
        assert False

    def test_get_missing_player_by_name(self):
        assert False
        # should 404

    # TODO: skip this
    def test_selected_by_rating(self):
        assert False
    
    # TODO: skip this
    def test_selected_by_name(self):
        assert False

    # TODO: skip this
    def test_selected_by_join_date(self):
        assert False


class TestGameListResourcePost(BaseResourceTest):
    """Tests POSTs to the game list resource.

    Tests performed here include:
    - Testing validation.
    - Testing that the DB is updated appropriatedly.
    - Side-effects to players and challenges happen correctly.
    """
    def setup(self):
        super(TestGameListResourcePost, self).setup()
        # POST a bunch of players then games

    def test_validate_both_players_exist(self):
        assert False

    def test_validate_players_are_unique(self):
        assert False

    def test_validate_scores(self):
        assert False

    def test_required_arguments(self):
        assert False

    def test_time_defaults_to_now(self):
        assert False

    def test_db_is_updated(self):
        assert False

    def test_players_scores_are_updates(self):
        assert False

    def test_new_game_updates_existing_challenge(self):
        # Maybe put this into the challenge tests?
        assert False


class TestGameListResourceGet(BaseResourceTest):
    def test_expected_fields_are_returned(self):
        assert False

    def test_games_are_ordered_by_recency(self):
        assert False

    def test_select_by_player_name(self):
        assert False


class TestChallengeListResourcePost(BaseResourceTest):
    def test_validate_both_players_exist(self):
        assert False

    def test_validate_players_are_unique(self):
        assert False

    def test_validate_no_existing_challenge_between_players(self):
        assert False

    def test_db_is_updated(self):
        assert False


class TestChallengeListResourceGet(BaseResourceTest):
    def test_only_open_challenges_are_shown(self):
        assert False, 'this is fucked up'

    def test_ordered_by_age(self):
        assert False

    def test_flag_for_showing_closed_challenges(self):
        assert False

    def test_select_by_player_name(self):
        assert False, 'this is fucked up'


################################################################################
# Helpers
################################################################################
def check_headers(response):
    assert response.headers['Content-Type'] == 'application/json'

def check_response(response, expected_status_code, expected_data, message):
    def assert_(condition, message):
        assert condition, message

    assert_(response.status_code == expected_status_code, message)
    assert_(response.headers['Content-Type'] == 'application/json', message)
    check_headers(response)
    found_data = json.loads(response.data)
    assert found_data == expected_data

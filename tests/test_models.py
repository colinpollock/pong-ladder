"""Basic unit tests for the ladder's models."""

from datetime import datetime

from app.models import db, Player, Game, Challenge
from app.app import create_app

from test_common import BaseFlaskTest


class BaseTestWithData(BaseFlaskTest):
    """Base test class that provides test data."""

    @classmethod
    def setup_class(cls):
        cls.app_context = create_app().app_context()
        cls.app_context.push()
        db.create_all()

    @classmethod
    def teardown_class(cls):
        cls.app_context.pop()

    def setup(self):
        self.kumanan = Player(name='kumanan', rating=1300, time_created=now())
        self.colin = Player(name='colin', rating=1100, time_created=now())
        self.robert = Player(name='robert', rating=1150, time_created=now())
        self.ayush = Player(name='ayush', rating=1250, time_created=now())
        db.session.add_all([self.kumanan, self.colin, self.robert, self.ayush])
        db.session.commit()

        self.game1 = Game(
            winner_id=self.kumanan.id,
            loser_id=self.colin.id,
            winner_score=21,
            loser_score=17,
            time_created=now()
        )

        self.game2 = Game(
            winner_id=self.colin.id,
            loser_id=self.ayush.id,
            winner_score=11,
            loser_score=7,
            time_created=now()
        )

        self.game3 = Game(
            winner_id=self.robert.id,
            loser_id=self.colin.id,
            winner_score=11,
            loser_score=8,
            time_created=now()
        )

        self.game4 = Game(
            winner_id=self.colin.id,
            loser_id=self.kumanan.id,
            winner_score=21,
            loser_score=19,
            time_created=now()
        )

        self.game5 = Game(
            winner_id=self.kumanan.id,
            loser_id=self.ayush.id,
            winner_score=11,
            loser_score=7
        )

        db.session.add_all([
            self.game1,
            self.game2,
            self.game3,
            self.game4,
            self.game5
        ])
        db.session.commit()

        self.challenge1 = Challenge(
            challenger_id=self.ayush.id,
            challenged_id=self.colin.id,
            time_created=now(),
            game_id=self.game1.id
        )

        self.challenge2 = Challenge(
            challenger_id=self.colin.id,
            challenged_id=self.kumanan.id,
            time_created=now(),
            game_id=None
        )

        self.challenge3 = Challenge(
            challenger_id=self.colin.id,
            challenged_id=self.ayush.id,
            time_created=now(),
            game_id=None
        )

        db.session.add_all([self.challenge1, self.challenge2, self.challenge3])
        db.session.commit()

    def teardown(self):
        Player.query.delete()
        Game.query.delete()
        Challenge.query.delete()


class TestPlayer(BaseTestWithData):
    def test_count(self):
        assert Player.query.count() == 4

    def test_get_player_by_id(self):
        assert Player.query.get(self.colin.id) == self.colin

    def test_get_player_by_name(self):
        assert (
            set(Player.query.filter_by(name='kumanan').all()) ==
            {self.kumanan}
        )

    def test_get_player_by_rating(self):
        assert (
            set(Player.query.filter(Player.rating > 1200).all()) ==
            {self.ayush, self.kumanan}
        )

    def test_wins(self):
        assert set(self.colin.won_games) == {self.game2, self.game4}

    def test_losses(self):
        assert set(self.colin.lost_games) == {self.game1, self.game3}

    def test_games(self):
        assert (
            set(self.colin.games) ==
            {self.game1, self.game2, self.game3, self.game4}
        )

    def test_num_wins(self):
        assert self.robert.num_wins == 1

    def test_num_losses(self):
        assert self.ayush.num_losses == 2

    def test_num_games(self):
        assert self.colin.num_games == 4

    def test_challenges_submitted(self):
        assert (
            set(self.colin.challenges_submitted) ==
            {self.challenge2, self.challenge3}
        )

    def test_challenges_received(self):
        assert set(self.colin.challenges_received) == {self.challenge1}

    def test_challenges(self):
        assert set(self.ayush.challenges) == {self.challenge1, self.challenge3}

    def test_num_challenges_submitted(self):
        assert self.colin.num_challenges_submitted == 2

    def test_num_challenges_received(self):
        assert self.colin.num_challenges_received == 1

    def test_num_challenges(self):
        assert self.ayush.num_challenges == 2


class TestGame(BaseTestWithData):
    def test_game_count(self):
        assert Game.query.count() == 5

    def test_get_game_by_id(self):
        assert Game.query.get(self.game1.id) == self.game1

    def test_get_challenge(self):
        assert self.game1.challenge == self.challenge1
        assert self.game2.challenge is None


class TestChallenge(BaseTestWithData):
    def test_is_completed(self):
        assert self.challenge1.is_completed is True
        assert self.challenge2.is_completed is False


###############################################################################
# Helpers
###############################################################################
def now():
    # TODO: use fixed times
    return datetime.now()

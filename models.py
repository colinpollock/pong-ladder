"""Models for a ping pong ladder.

Each person in the ladder is a `Player`. Each `Game` has two `Player`s, the
winner and the loser. A `Challenge` is issued by one `Player` to another, and is
open until a game between those two players has been played.
"""


from sqlalchemy import or_
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method
from flask.ext.sqlalchemy import SQLAlchemy


db = SQLAlchemy()


class Player(db.Model):
    """Represents a ping pong player."""

    __tablename__ = 'player'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column('name', db.String(30))
    rating = db.Column('rating', db.Integer)
    time_created = db.Column('time_created', db.DateTime)

    @hybrid_property
    def games(self):
        return self.won_games + self.lost_games

    @hybrid_property
    def num_wins(self):
        return Game.query.filter(Game.winner==self).count()

    @hybrid_property
    def num_losses(self):
        return Game.query.filter(Game.loser==self).count()

    @hybrid_property
    def num_games(self):
        return self.num_wins + self.num_losses

    @hybrid_property
    def challenges(self):
        return self.challenges_submitted + self.challenges_received

    @hybrid_property
    def num_challenges_submitted(self):
        return Challenge.query.filter(Challenge.challenger==self).count()

    @hybrid_property
    def num_challenges_received(self):
        return Challenge.query.filter(Challenge.challenged==self).count()

    @hybrid_property
    def num_challenges(self):
        return self.num_challenges_received + self.num_challenges_submitted

    def __repr__(self):
        return 'Player(%s, %d, %s)' %  \
            (self.name, self.rating, self.time_created)


class Game(db.Model):
    """A game played between two ping pong players."""

    __tablename__ = 'game'
    id = db.Column(db.Integer, primary_key=True)

    winner_id = db.Column(db.Integer, db.ForeignKey('player.id'))
    winner = db.relationship(
        Player,
        foreign_keys=[winner_id],
        backref=db.backref('won_games')
    )

    loser_id = db.Column(db.Integer, db.ForeignKey('player.id'))
    loser = db.relationship(
        Player,
        foreign_keys=[loser_id],
        backref=db.backref('lost_games')
    )

    winner_score = db.Column('winner_score', db.Integer)
    loser_score = db.Column('loser_score', db.Integer)

    time_created = db.Column('time_created', db.DateTime)

    def __repr__(self):
        return ('Game(%s beat %s %d-%d on %s)' % 
            (self.winner, self.loser, self.winner_score, self.loser_score,
             self.time_created))


class Challenge(db.Model):
    """A challenge issued by one player to another.

    Note that the `game` field references a Game if this challenge has been
    played and is None otherwise.
    """

    __tablename__ = 'challenge'

    id = db.Column(db.Integer, primary_key=True)

    challenger_id = db.Column(db.Integer, db.ForeignKey('player.id'))
    challenger = db.relationship(
        Player,
        foreign_keys=[challenger_id],
        backref=db.backref('challenges_submitted')
    )

    challenged_id = db.Column(db.Integer, db.ForeignKey('player.id'))
    challenged = db.relationship(
        Player,
        foreign_keys=[challenged_id],
        backref=db.backref('challenges_received')
    )

    time_created = db.Column('time_created', db.DateTime)

    game_id = db.Column(db.Integer, db.ForeignKey('game.id'))
    game = db.relationship(Game, backref=db.backref('challenge', uselist=False))

    def __repr__(self):
        return '<Challenge(%s vs %s)>' %  \
            (self.challenger.name, self.challenged.name)


        if self.is_completed:
            return 'Challenge completed: ', self.game
        else:
            return 'Challenge(%s vs %s issued on %s)' % \
                (self.challenger.name, self.challenged.name, self.time_created)

    @hybrid_property
    def is_completed(self):
        """Return True iff a game has been played by these players after the
        challenge."""
        return self.game is not None


#from peewee import Model
#from peewee import CharField, ForeignKeyField, DateTimeField, BooleanField, IntegerField

from flask.ext.sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Player(db.Model):
    """TODO: docstring"""
    __tablename__ = 'players'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column('name', db.String(30))
    rating = db.Column('rating', db.Integer)
    time_added = db.Column('time_added', db.DateTime)

    @property
    def won_games(self):
        return self.won_games.all()

    @property
    def num_wins(self):
        return self.won_games.count()

    @property
    def lost_games(self):
        return self.lost_games.all()

    @property
    def num_losses(self):
        return self.lost_games.count()

    def __repr__(self):
        return 'Player(%s, %d, %s)' % (self.name, self.rating, self.time_added)


class Game(db.Model):
    """TODO: docstring"""
    __tablename__ = 'games'
    id = db.Column(db.Integer, primary_key=True)

    winner_id = db.Column(db.Integer, db.ForeignKey('player.id'))
    winner = db.relationship(
        'Player',
        backref=db.backref('won_games', lazy='dynamic')
    )

    loser_id = db.Column(db.Integer, db.ForeignKey('player.id'))
    loser = db.relationship(
        'Player',
        backref=db.backref('lost_games', lazy='dynamic')
    )

    winner_score = db.Column('winner_score', db.Integer)
    loser_score = db.Column('loser_score', db.Integer)

    time_added = db.Column('time_added', db.DateTime)

    @property
    def time_added_str(self):
        return str(self.time_added)

    def __repr__(self):
        return ('Game(%s beat %s %d-%d on %s)' % 
            (self.winner, self.loser, self.winner_score, self.loser_score,
             self.time_added))

class Challenge(db.Model):
    """A challenge issued by one player to another.

    Note that the `game` field references a Game if this challenge has been
    played and is None otherwise.
    """
    __tablename__ = 'challenges'

    id = db.Column(db.Integer, primary_key=True)

    challenger_id = db.Column(db.Integer, db.ForeignKey('player.id'))
    challenger = db.relationship(
        'Player',
        backref=db.backref('challenges_submitted')
    )

    challenged_id = db.Column(db.Integer, db.ForeignKey('player.id'))
    challenged = db.relationship(
        'Player',
        backref=db.backref('challenges_accepted')
    )

    time_added = db.Column('time_added', db.DateTime)

    game_id = db.Column(db.Integer, db.ForeignKey('game.id'))
    game = db.relationship(
        'Game',
        backref=db.backref('challenges')
    )

    def __repr__(self):
        if self.is_completed:
            return 'Challenge completed: ', self.game
        else:
            return 'Challenge(%s vs %s issued on %s)' % \
                (self.challenger.name, self.challenged.name, self.time_added)

    @property
    def is_completed(self):
        """TODO: docstring"""
        return self.game is not None


from peewee import Model
from peewee import CharField, ForeignKeyField, DateTimeField, BooleanField, IntegerField

from db import db


class Player(Model):
    """TODO: docstring"""
    # TODO: use the name as the PK?
    name = CharField(max_length=30, unique=True, help_text="Player's username")

    rating = IntegerField(help_text='ELO rating')
    time_added = DateTimeField()

    class Meta:
        database = db

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

    def __unicode__(self):
        return 'Player(%s, %d, %s)' % (self.name, self.rating, self.time_added)


class Game(Model):
    """TODO: docstring"""
    winner = ForeignKeyField(Player, related_name='won_games')
    loser = ForeignKeyField(Player, related_name='lost_games')
    winner_score = IntegerField()
    loser_score = IntegerField()
    time_added = DateTimeField()

    @property
    def time_added_str(self):
        return str(self.time_added)

    class Meta:
        database = db

    def __unicode__(self):
        return ('Game(%s beat %s %d-%d on %s)' % 
            (self.winner, self.loser, self.winner_score, self.loser_score,
             self.time_added))


class Challenge(Model):
    """A challenge issued by one player to another.

    Note that the `game` field references a Game if this challenge has been
    played and is None otherwise.
    """
    challenger = ForeignKeyField(Player, related_name='challenges_submitted')
    challenged = ForeignKeyField(Player, related_name='challenges_accepted')

    game = ForeignKeyField(
        Game,
        null=True, 
        help_text='References the completed game'
    )
    time_added = DateTimeField()

    class Meta:
        database = db

    def __unicode__(self):
        if self.is_completed:
            return 'Challenge completed: ', self.game
        else:
            return 'Challenge(%s vs %s issued on %s)' % \
                (self.challenger.name, self.challenged.name, self.time_added)

    @property
    def is_completed(self):
        """TODO: docstring"""
        return self.game is not None

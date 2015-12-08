
from marshmallow import Schema, fields

import util


class _MyDateTime(fields.Field):
    def _serialize(self, value, attr, obj):
        return util.format_datetime(value)

    def _deserialize(self, value):
        return util.parse_datetime(value)

class PlayerSchema(Schema):
    name = fields.Str()
    rating = fields.Int()
    num_wins = fields.Int()
    num_losses = fields.Int()
    time_created = _MyDateTime()

player_schema = PlayerSchema()
players_schema = PlayerSchema(many=True)


class GameSchema(Schema):
    id = fields.Int(dump_only=True)
    winner = fields.Str(attribute='winner.name')
    loser = fields.Str(attribute='loser.name')
    winner_score = fields.Int()
    loser_score = fields.Int()
    time_created = _MyDateTime()

games_schema = GameSchema(many=True)

class ChallengeSchema(Schema):
    id = fields.Int(dump_only=True)
    challenger = fields.Str(attribute='challenger.name')
    challenged = fields.Str(attribute='challenged.name')
    time_created = _MyDateTime()
    game_id = fields.Int(dump_only=True)

challenges_schema = ChallengeSchema(many=True)

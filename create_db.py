
from db import db

from models import Challenge, Game, Player

db.create_tables([Challenge, Game, Player])

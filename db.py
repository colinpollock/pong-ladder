from peewee import Model, SqliteDatabase

from util import config

db = SqliteDatabase(config['db_file'])
db.connect()

"""This is the entry point for running the ladder service API.

The app will be configured to run in a particular environment, specified by the
`FLASK_ENV` environment variable.
"""

import os

from flask.ext.restful import Api
from flask import Flask
from flask_environments import Environments

from models import db
from resource import (PlayerListResource, PlayerResource, GameListResource,
                      ChallengeListResource)


def create_app():
    """Return a Flask app configured for the correct env (test, dev, prod)."""
    app = Flask(__name__)
    env = Environments(app)
    env.from_yaml(os.path.join(os.getcwd(), 'config.yaml'))

    api = Api(app)
    api.add_resource(PlayerListResource, '/players')
    api.add_resource(PlayerResource, '/players/<string:name>')
    api.add_resource(GameListResource, '/games')
    api.add_resource(ChallengeListResource, '/challenges')

    db.init_app(app)

    return app

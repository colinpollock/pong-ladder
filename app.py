import os

from flask.ext.restful import Api
from flask import Flask, jsonify, request, current_app
from flask_environments import Environments

from resource import (PlayerListResource, PlayerResource, GameListResource,
    ChallengeListResource)

from models import db


def create_app():
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


if __name__ == '__main__':
    app = create_app()
    app.run(port=app.config['PORT'], debug=app.config['DEBUG'])

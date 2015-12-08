Ladder
======

This is a small Flask service for running a ping pong ladder. It supports the
creation of players, games, and challenges.

Each player has a rating, and when a new game is added the two players' ratings
are updated according to the [Elo rating system][1].

You can directly interact with the service over HTTP (see below), but there is
also an IRC bot client that talks to the service located within the `clients/`
directory.

## Setting up ##
In `config.yaml` you can change the port where the service runs. You can also
change the path for the SQLite DB file. The service uses SQLAlchemy so other
databases should work but I haven't tested them. Running `make` will build a
[virtual environment][3] and install dependencies, so virtualenv is required.


# Example Usage #
To run tests run `make test`. To run the service in dev run `make run-dev`. The
service's port when running in dev is specified in `config.yaml`, and defaults
to 6789.

Once the service is running you can interact with it using curl. The example
session below uses [httpie][2].

```bash
$ http post 'localhost:6789/players' name=colin
$ http post 'localhost:6789/players' name=kumanan
$ http GET 'localhost:6789/players'
[
    {
        "name": "kumanan",
        "num_losses": 1,
        "num_wins": 1,
        "rating": 1202,
        "time_created": "2015-12-08T06:22:59"
    },
    {
        "name": "colin",
        "num_losses": 1,
        "num_wins": 1,
        "rating": 1198,
        "time_created": "2015-12-08T06:22:55"
    }
]

$ http post 'localhost:6789/games' winner=kumanan loser=colin winner_score=21 loser_score=11
$ http post 'localhost:6789/games' winner=colin loser=kumanan winner_score=11 loser_score=9
$ http GET 'localhost:6789/games'
[
    {
        "id": 2,
        "loser": "kumanan",
        "loser_score": 9,
        "time_created": "2015-12-08T06:24:39",
        "winner": "colin",
        "winner_score": 11
    },
    {
        "id": 1,
        "loser": "colin",
        "loser_score": 11,
        "time_created": "2015-12-08T06:23:33",
        "winner": "kumanan",
        "winner_score": 21
    }
]

$ http post 'localhost:6789/challenges' challenger=kumanan challenged=colin
$ http get 'localhost:6789/challenges'
[
    {
        "challenged": "colin",
        "challenger": "kumanan",
        "game_id": null,
        "id": 1,
        "time_created": "2015-12-08T06:27:57"
    }
]
```


# TODO #
* Cleanup
  * Use marshmallow for deserializing POST bodies
    * https://webargs.readthedocs.org/en/latest/advanced.html#advanced
  * Thread config values through (e.g. default initial rating)
* Cosmetic
  * Order imports correctly
  * Write doc strings
  * run pylint etc
* Bot
  * Have the irc bot say "No X" when there are no players or games
  * Send helpful message when service 500s
  * Handle challenges
* Logging
  * log every message that includes pongbot
  * Log IRC connection errors
  * Log service communication errors


[1]: https://en.wikipedia.org/wiki/Elo_rating_system
[2]: https://github.com/jkbrzt/httpie
[3]: https://virtualenv.readthedocs.org/en/latest

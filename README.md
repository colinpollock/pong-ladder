Ladder
======

This is a small Flask service for running a ping pong ladder. The only client
currently is an IRC bot, also living in this repo. The service and DB code is
abstracted out of the IRC bot so that other clients (e.g. Slack bot) can also
connect to it over HTTP.

# TODO #
* Pass number of wins and losses through with each player
  * Django generated a backref for the related_name, so I could
    reference the games from the player

* Use name as pk
* Put `to_entity` munging code in model classes
* Write tests
* Use restful API flask. flask.ext.restful
  * Validation of args

* doc strings
* Logging
  * log every message that includes pongbot
  * Log IRC connection errors
  * Log service communication errors

* Standard config reader?

* PEP8 comments
* order imports correctly
* run pylint etc


# Example Usage #

## Setting up ##
* Dependencies
* Running the service

* Running the bot
python ircbot.py --bot-name=pongbot --irc-host='irc.freenode.net' --irc-port=6667 --channel=ppong --service-host=localhost --service-port=8000

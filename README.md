Ladder
======

This is a small Flask service for running a ping pong ladder. The only client
currently is an IRC bot, also living in this repo. The service and DB code is
abstracted out of the IRC bot so that other clients (e.g. Slack bot) can also
connect to it over HTTP.

# Example Usage #
TODO

## Setting up ##
TODO


# TODO #
* Fix the package structure and
* Cleanup
  * Thread config values through (e.g. default initial rating)
* Cosmetic
  * Order imports correctly
  * Write doc strings
  * run pylint etc
* Bot
  * Have the irc bot say "No X" when there are no players or games
* Logging
  * log every message that includes pongbot
  * Log IRC connection errors
  * Log service communication errors

* Run on heroku
  * Change over to postgres?



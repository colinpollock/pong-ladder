# TODO #
* Bot
  * Have the irc bot say "No X" when there are no players or games
  * Handle showing challenges
  * Handle 'show my games'
  * Have open challenges ping the challenged player periodically
  * Get maintainer out of config for 'contact the maintainer'
* Logging
  * log every message that includes pongbot
  * Log IRC connection errors
  * Log service communication errors
* Cleanup
  * Use marshmallow for deserializing POST bodies
    * https://webargs.readthedocs.org/en/latest/advanced.html#advanced
  * Thread config values through (e.g. default initial rating)

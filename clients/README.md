Clients
=======

This directory contains clients for interacting with the ladder service.
Currently the only client is an IRC bot.

### IRC Bot ###
After building the environment (`make test`) you can run this IRC bot. Assuming
you're running the service at localhost:6789 and want to connect to the channel
"pong" on freenode run the following command:
```bash
venv/bin/python clients/ircbot.py \
    --irc-host=irc.freenode.net \
    --irc-port=6667 \
    --channel pong \
    --bot-name pongbot \
    --service-host localhost \
    --service-port 6789
```

"""An IRC bot for interacting with the Flask ladder service.

Commands:
* ```commands```: displays usage help and the available commands
* ```add player PLAYER```: add a new player
* ```PLAYER1 beat PLAYER2 SCORE1 to SCORE2```: add a new game
* ```ladder```: display all players ordered by their ratings
"""

import argparse
import functools
import re
import sys
import simplejson as json

import requests
from twisted.words.protocols import irc
from twisted.internet import protocol, reactor, ssl


def handles_service_errors(func):
    """Decorator that will return a error message when the service errors.

    This is meant to annotate any method that (a) has a call to the service and
    (b) returns strings that are send to channel.

    This decorator will only work for methods within `LadderBot`.
    """
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except requests.exceptions.RequestException:
            return self._make_service_error_message()

    return wrapper


class LadderBot(irc.IRCClient):
    """A bot that connects to an IRC channel to manage a ping pong ladder."""

    def process_command(self, command):
        """Identify the command, talk to ladder service, and return a list of
        messages to be sent back to the channel.
        """
        _log_info('COMMAND: %s' % command)
        help_pat = re.compile(r'help|commands', re.IGNORECASE)
        player_pat = re.compile(r'add\s+player\s+(?P<name>\w+)')
        ladder_pat = re.compile(r'ladder|ratings|rankings')
        game_pat = re.compile(r"""
            (?P<winner>\w+)
            \s+
            beat
            \s+
            (?P<loser>\w+)
            \s+
            (?P<winner_score>\d+)
            \s*
            (to|-)
            \s*
            (?P<loser_score>\d+)
        """, re.VERBOSE)

        if help_pat.match(command):
            return self.get_help()

        if ladder_pat.match(command):
            return self.get_ladder()

        match_ = player_pat.match(command)
        if match_:
            return self.add_player(match_.groupdict()['name'])

        match_ = game_pat.match(command)
        if match_:
            data = match_.groupdict()
            return self.add_game(data['winner'], data['loser'],
                                 data['winner_score'],
                                 data['loser_score'])

        return ['Command not recognized! Type "pongbot help" for more info.']

    @handles_service_errors
    def add_player(self, player_name):
        """Add a new player"""
        response = self._post('/players', {'name': player_name})
        return self._make_message(
            response,
            lambda: ['Added player {0}'.format(player_name)]
        )

    @handles_service_errors
    def add_game(self, winner, loser, winner_score, loser_score):
        """Add a new game."""

        data = {
            'winner': winner,
            'loser': loser,
            'winner_score': winner_score,
            'loser_score': loser_score,
        }

        response = self._post('/games', data)
        return self._make_message(response, lambda: ['Added game'])

    @handles_service_errors
    def get_ladder(self):
        """Return the players ordered by rating."""
        response = self._get('/players')

        if not response.ok:
            return [self._error_message()]

        def _make_line((rank, player)):
            return '[%d] %s %d-%d (%d)' % (
                rank,
                player['name'].encode('ascii'),
                player['num_wins'],
                player['num_losses'],
                player['rating']
            )

        return self._make_message(
            response,
            lambda: map(_make_line, enumerate(response.json(), start=1))
        )

    def get_help(self):
        """Display help information about using the bot and available commands.
        """
        return [
            'Type "%s: COMMAND". Commands are:' % self.nickname,
            'Add a player: add player PLAYER_NAME',
            'Add a game: WINNER_NAME beat LOSER_NAME WINNER_SCORE-LOSER_SCORE',
            'Show all players ordered by rating: ladder'
        ]

    ###########################################################################
    # Helpers
    ###########################################################################
    @property
    def maintainer_name(self):
        return self.factory.maintainer_name

    @property
    def nickname(self):
        return self.factory.nickname

    @property
    def password(self):
        return self.factory.server_password

    @property
    def _api_url(self):
        return self.factory.api_url

    @property
    def _service_url(self):
        return 'http://%s:%d' % (self.service_host, self.service_port)

    def signedOn(self):
        _log_info('Signed on')
        self.join(self.factory.channel)

    def joined(self, channel):
        _log_info('Joined channel "%s" as "%s"' % (channel, self.nickname))

    def privmsg(self, user, channel, message):
        """Respond to a message in the channel if the bot is mentioned."""
        _log_info('privMsg from %s in channel %s: "%s"' %
                  (user, channel, message))
        pat = re.compile(r"""
            \s*
            (?P<nick>%s|%s)
            (\s+|:)
            \s*
            (?P<command>.*)
        """ % (self.nickname, self.nickname.lower()), re.VERBOSE)
        match = pat.match(message)
        if match is None:
            _log_info('No action for "%s"' % message)
            return

        data = match.groupdict()
        response = self.process_command(data['command'])

        for line in response:
            self.msg(channel, line)

    def _post(self, endpoint, data):
        """Post JSON data to the service.

        Note that this is just a pass-through and that no exceptions are
        handled here.
        """
        return requests.post(
            self._api_url + endpoint,
            data=json.dumps(data),
            headers={'Content-Type': 'application/json'}
        )

    def _get(self, endpoint):
        """Make a GET request to the specified endpoint and return response."""
        return requests.get(self._api_url + endpoint)

    def _make_service_error_message(self):
        return [
            'Error: contact the maintainer {0}'.format(
                self.maintainer_name
            )
        ]

    def _make_message(self, http_response, build_success_messages):
        """Make a response message to send to the IRC channel.

        Args:
            http_response - the response sent from the ladder service.
            build_success_messages - if the HTTP request sent to the ladder
                service was succesful then this function is called. The
                function generates a list of strings to be sent by the IRC bot
                back to the channel. Note that this is a function rather than
                just the actual message string(s) because building the message
                may require the http request to have been successful and that's
                not checked until this method.

        Returns:
            A list of strings to be sent to the IRC channel.
        """
        if http_response.ok:
            return build_success_messages()
        elif http_response.status_code == 500:
            return self._make_service_error_message()
        else:
            return ['Error: {0}'.format(str(http_response.json()))]


class LadderBotFactory(protocol.ClientFactory):
    protocol = LadderBot

    def __init__(
        self,
        channel,
        nickname,
        service_host,
        service_port,
        server_password,
        maintainer_name
    ):
        self.channel = channel
        self.nickname = nickname
        self.server_password = server_password
        self.maintainer_name = maintainer_name

        self.api_url = 'http://%s:%d' % (service_host, service_port)

    def clientConnectionLost(self, connector, reason):
        _log_error('lost connection (%s), reconnecting' % reason)

    def clientConnectionFailed(self, connector, reason):
        _log_error('could not connect: %s' % reason)


def _log_info(message):
    print >> sys.stderr, 'INFO:', message


def _log_error(message):
    print >> sys.stderr, 'ERROR:', message


def main(args):
    bot_factory = LadderBotFactory(
        args.channel,
        args.bot_name,
        args.service_host,
        args.service_port,
        args.server_password,
        args.maintainer_name
    )

    if args.use_ssl:
        reactor.connectSSL(
            args.irc_host,
            args.irc_port,
            bot_factory,
            ssl.ClientContextFactory()
        )

    else:
        reactor.connectTCP(args.irc_host, args.irc_port, bot_factory)

    try:
        reactor.run()
    except EOFError:
        reactor.stop()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('--irc-host', required=True)
    parser.add_argument('--irc-port', type=int, required=True)

    parser.add_argument('--use-ssl', action='store_true', default=False)
    parser.add_argument('--server-password', required=False)

    parser.add_argument(
        '--channel',
        required=True,
        help='IRC channel. E.g. "#pingpong".'
    )
    parser.add_argument('--bot-name', required=True)
    parser.add_argument('--service-host', required=True)
    parser.add_argument('--service-port', type=int, required=True)

    parser.add_argument('--maintainer-name', default='<UNKNOWN>')

    main(parser.parse_args(sys.argv[1:]))

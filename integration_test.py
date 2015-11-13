"""TEST PLAN

To test the ladder service I'll set up tests by calling the service and then
verify either by inspecting the return value or error or by checking the state
in the database.


# Tests #
* add_player
  * validation
    * returns exception with message when 
  * this actually creates a player w/ the desired attributes
  * can't add player with used name. should raise exception
  * newly added player should have the default rating
  * newly added player should have a recent time_added

* show_players
  * should return all of the players
  * should be ordered by rating and then on number of games played
    * new players with no games should be ordered by their join dates
    * players with equal ratings should be ordered by number of games
    * players should be ordered by rating

* add game
  * needs all four args
  * score validation; throw exception when it doesn't work with helpful message
  * both players have to exist
  * the winner and loser can't be the same person

  * a new game should actually be created
  * winner's and loser's ratings should be updated correctly
  * any outstanding challenges should be associated with this game

* show games
  * if 'player' arg is passed we only show games where that player was winner or
    loser
  * games are ordered by recency
  * all games added are shown
  * each game has the things we expect in it

* add challenge
  * both players have to exist
  * a challenge b/w these two players can't already exist
  * challenger != challenged

* show challenges
  * the expected number of challenges exists
  * if 'player' is present we only show challenges involving that player
  * we only show open challenges
  * challenges are ordered by recency
  * each challenge has the stuff we expect it to

"""
from ladderservice import app
from util import config

port = config['api_service_port']
app.run(port=port)


base_url = 'http://localhost:%d/api/' % port
player_url = base_url + 'player/'
game_url = base_url + 'game/'
challenge_url = base_url + 'challenge/'

def get(url, params):
    param_strs = ['?']
    for idx, (param, value) in enumerate(params):
        char = '?' if idx == 0 else '&'
        param_strs.append(char + '%s=%s' % (param, value))
    url = url + ''.join(param_str)

    return requests.get(url)

def post(url, json_):
    return requests.post(url, json=json_)







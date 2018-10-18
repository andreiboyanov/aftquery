#coding=utf-8

import re
import sys
import urllib
import argparse
from pprint import pprint
from bs4 import BeautifulSoup as bs4

from aftquery.parser.aft import clubs as aft_clubs
from aftquery.parser.aft import players as aft_players
from aftquery.parser.aft.common import _get_name_and_id

players = dict()
clubs = dict()


def parse_player_ranking_matches(html):
    soup = bs4(html, "html.parser")
    current_ranking_element = soup.find_all(text=re.compile('Classement actuel'))[0].strip()
    current_ranking = current_ranking_element.split(':')[1].strip()
    future_ranking_element = soup.find_all(text=re.compile('du nouveau classement:'))[0].strip()
    future_ranking = current_ranking_element.split(':')[1].strip()

    print(future_ranking_element, future_ranking)
    print(current_ranking_element, current_ranking)

    matches_table = soup.find(id="matchs_table").find_all('tbody')[0]
    for row in matches_table.find_all('tr'):
        cells = row.find_all('td')
        match = dict(
            win=cells[0].text == 'V',
            date=cells[1].text,
            tournament=cells[2].text,
            oponent_url=cells[3].a["href"],
            oponent_name=cells[3].a.text,
            oponent_ranking=cells[4].text,
            oponent_new_ranking=cells[5].text,
            match_score=cells[6].text,
        )
        print(match)


def get_matches(player_id, name=None, type='single', year=None):
    if name is None:
        player_details = get_player_details(player_id)
        name = player_details['name']
    last_name, first_name = name.split()
    url = 'https://www.classement-tennis.be/matchs/{}_{}_{}.html'.format(player_id, first_name, last_name)
    html = urllib.urlopen(url).read()
    parse_player_ranking_matches(html)


def search_players(region=1, name=u"",
                   male=True, female=True, club_id=""):
    for players_chunk in aft_players.search_players(region, name, male, female, club_id):
        players.update(players_chunk)
        pprint(players_chunk)


def search_clubs(region=1):
    for club in aft_clubs.search_clubs(region):
        clubs[club["id"]] = club
    pprint(clubs)


def main(argv):
    parser = argparse.ArgumentParser(description="Search for francophone tennis players in Belgium")
    parser.add_argument("--players", action="store_true", help="Search for players")
    parser.add_argument("--clubs", action="store_true", help="Search for clubs")
    parser.add_argument("--player-name", default="", help="Filter players by name")
    parser.add_argument(
        "--player-id", default=[], nargs="*", action="append",
        help="Get player details by ID. Multiple instances of this argument are accepted.")
    parser.add_argument("--club-id", default="")
    parser.add_argument('--show-matches', action='store_true', help="Show player's matches")
    arguments = parser.parse_args(argv)
    if arguments.player_id:
        for player_ids in arguments.player_id:
            for player_id in player_ids:
                player_details = get_player_details(player_id)
                if arguments.show_matches:
                    get_matches(player_id, name=player_details['name'])
    elif arguments.players or arguments.club_id:
        search_players(club_id=arguments.club_id, name=arguments.player_name)
    elif arguments.clubs:
        search_clubs()
    else:
        print("Without concrete request I'll search for all players in AFT.")
        search_clubs()
        for club_id in clubs:
            search_players(club_id=club_id)

if __name__ == "__main__":
    main(sys.argv[1:])

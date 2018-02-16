#encoding: utf-8
import re
import sys
import urllib
import os.path
import urlparse
import argparse
from pprint import pprint
from bs4 import BeautifulSoup as bs4

PLAYER_INFO_LABELS = dict({
    u"Né le": "birth date",
    u"Nationalité": "nationality",
    u"Sexe": "sex",
    u"Classement simple": "single ranking",
    u"Valeur double": "double points",
    u"Première affiliation": "first affiliation",
    u"Actif depuis le": "active from",
    u"Club": "club",
})

players = dict()
clubs = dict()


def _get_name_and_id(name_and_id):
    first_bracket_index = name_and_id.find('(')
    _name = name_and_id[:first_bracket_index-1]
    _id = name_and_id[first_bracket_index+1:-1]
    return _name, _id

def _extract_club_id_from_href(href):
    club_detail_url = '/MyAFT/Clubs/Detail/'
    url_len = len(club_detail_url)
    return href[url_len:url_len+4]


def _get_sex_from_image(info_element):
    try:
        sex_image_url = info_element.find_all("image")[0].get("src")
        sex_file_name = os.path.basename(urlparse.urlsplit(sex_image_url).path)
        return os.path.splitext(sex_file_name)[0]
    except IndexError:
        return ""


def _extract_value_from_ranking_text(text):
    return text[:text.find(" - ")]


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


def parse_player_details(html):
    player_details = dict()
    soup = bs4(html, "html.parser")
    detail_body = soup.find_all("div", "detail-body player", limit=1)[0]

    title = detail_body.find(id="player-title").text
    first_bracket = title.find('(')
    player_details["name"] = title[:first_bracket-1]
    player_details["id"] = title[first_bracket+1:-1]

    try:
        player_details["image"] = detail_body.find_all("img", recursive=False, limit=1)[0].get("src")
    except IndexError:
        player_details["image"] = None

    info = detail_body.find(id="colInfo").dl
    current_label = None
    for info_element in info.find_all():
        if info_element.name == "dt":
            current_label = info_element.text[:-1]
        elif info_element.name == "dd":
            if current_label not in PLAYER_INFO_LABELS:
                player_details[current_label] = info_element.text
                continue
            if current_label == "Sexe":
                player_details[PLAYER_INFO_LABELS[current_label]] = _get_sex_from_image(info_element)
            else:
                player_details[PLAYER_INFO_LABELS[current_label]] = info_element.text
    player_details["single ranking"] = _extract_value_from_ranking_text(player_details["single ranking"])
    player_details["double points"] = _extract_value_from_ranking_text(player_details["double points"])

    print(u"".format(player_details["name"]))
    print(u"=" * len(player_details["name"]))
    for label, value in player_details.items():
        if label != "image":
            print(u"{}: {}".format(label, value))
    print("\n")
    return player_details


def parse_players(html):
    soup = bs4(html, "html.parser")
    count = 0
    for player in soup.find_all('dl'):
        fields = player.find_all('dd')
        player_name, player_id = _get_name_and_id(fields[0].a.text)
        new_player = dict(
            name=player_name,
            id=player_id,
            single_ranking=fields[1].text,
            double_ranking=fields[2].text[len('Valeur double: '):],
            club_name=fields[3].text,
            club_id=_extract_club_id_from_href(fields[3].a['href']))
        players[player_id] = new_player
        count += 1
        print("PLAYER", new_player)
    return count


def parse_clubs(html):
    soup = bs4(html)
    count = 0
    for club in soup.find_all('dl'):
        club_name, club_id = _get_name_and_id(club.a.text)
        new_club = dict(name=club_name, id=club_id)
        clubs[club_id] = new_club
        count += 1
        print("CLUB", new_club)
    return count


def get_player_details(player_id):
    url = "http://www.aftnet.be/MyAFT/Players/Detail/{}".format(player_id)
    html = urllib.urlopen(url).read()
    player = parse_player_details(html)
    return player


def search_players(total_records=0, region=1, name=u"",
                   male=True, female=True, club_id=""):
    if total_records == 0:
        url = "http://www.aftnet.be/MyAFT/Players/SearchPlayers"
    else:
        url = "http://www.aftnet.be/MyAFT/Players/LoadMoreResults"
    data = {
        "Regions": str(region),
        "currentTotalRecords": total_records,
        "sortExpression": "",
        "AffiliationNumberFrom": "",
        "AffiliationNumberTo": "",
        "NameFrom": name,
        "NameTo": "",
        "BirthDateFrom": "",
        "BirthDateTo": "",
        "SingleRankingIdFrom": "1",
        "SingleRankingIdTo": "24",
        "Male": male,
        "Female": female,
        "ClubId": str(club_id),
    }

    webdata = urllib.urlencode(data)
    html = urllib.urlopen(url, webdata).read()
    new_players_count = parse_players(html)
    print("Added {} players. They are now {}"
          "".format(new_players_count, total_records+new_players_count))
    if new_players_count < 10:
        return
    search_players(
        total_records + new_players_count,
        region=region, name=name,
        male=male, female=female, club_id=club_id
    )


def search_clubs(region=1):
    url = "http://www.aftnet.be/MyAFT/Clubs/SearchClubs"

    data = {
        "City": "",
        "ClubIdFrom": "",
        "ClubIdTo": "",
        "ClubLabels": "",
        "CourtIndoor": False,
        "CourtOutdoor": False,
        "IndoorLighting": False,
        "IndoorNumberOfCourts": "",
        "IndoorSurface": "",
        "Latitude": "",
        "Longitude": "",
        "NameFrom": "",
        "NameTo": "",
        "OutdoorLighting": False,
        "OutdoorNumberOfCourts": "",
        "OutdoorSurface": "",
        "Radius": "",
        "StreetNumber": "",
        "ZipCode": "",
        "ZipCodeFrom": "",
        "ZipCodeTo": "",
        "regions": str(region),
    }
    webdata = urllib.urlencode(data)
    html = urllib.urlopen(url, webdata).read()
    new_clubs_count = parse_clubs(html)
    print("Found {} clubs.".format(new_clubs_count))



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

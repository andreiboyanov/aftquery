#coding=utf-8

import re
import sys
import requests
import os.path
import urlparse
import argparse
from pprint import pprint
from bs4 import BeautifulSoup as bs4

from aftquery.parser.aft.common import _get_name_and_id

PLAYER_INFO_LABELS = dict({
    u"Né le": "birth date",
    u"Nationalité": "nationality",
    u"Sexe": "sex",
    u"Classement simple": "single ranking",
    u"Valeur double": "double points",
    u"Première affiliation": "first affiliation",
    u"Actif depuis le": "active from",
    u"Club": "club"
})


def _extract_value_from_ranking_text(text):
    return text[:text.find(" - ")]


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


def parse_player_details(html):
    player_details = dict()
    soup = bs4(html, "html.parser")
    try:
        detail_body = soup.find_all("div", "detail-body player", limit=1)[0]
    except IndexError:
        return {}

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

    print(u"{}".format(player_details["name"]))
    print(u"=" * len(player_details["name"]))
    for label, value in player_details.items():
        if label != "image":
            print(u"{}: {}".format(label, value))
    print("\n")
    return player_details


def parse_players(html):
    soup = bs4(html, "html.parser")
    players = dict()
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
    return players


def get_player_details(player_id):
    url = "http://www.aftnet.be/MyAFT/Players/Detail/{}".format(player_id)
    html = requests.get(url).text
    player = parse_player_details(html)
    return player


def search_players(region=1, name=u"",
                   male=True, female=True, club_id=""):

    session = requests.Session()

    def search_player_chunks(total_records=0, region=1, name=u"",
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

        request = session.post(url, data=data)
        html = request.text
        new_players = parse_players(html)
        return new_players

    total_players_count = 0
    while True:
        new_players = search_player_chunks(
            total_players_count,
            region=region, name=name,
            male=male, female=female, club_id=club_id
        )
        new_players_count = len(new_players)
        total_players_count += new_players_count
        yield new_players
        if len(new_players) < 10:
            break

        


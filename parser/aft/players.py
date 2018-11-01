# coding=utf-8

import requests
import os.path
import urllib.parse
from bs4 import BeautifulSoup as bs4

from aftquery.parser.aft.common import _get_name_and_id

PLAYER_INFO_LABELS = dict(
    {
        u"Né le": "birth date",
        u"Nationalité": "nationality",
        u"Sexe": "sex",
        u"Classement simple": "single ranking",
        u"Classement simple interclubs": "single interclub ranking",
        u"Valeur double": "double points",
        u"Première affiliation": "first affiliation",
        u"Actif depuis le": "active from",
        u"Club": "club",
    }
)


def _extract_value_from_ranking_text(text):
    return text[: text.find(" - ")]


def _extract_club_id_from_href(href):
    club_detail_url = "/MyAFT/Clubs/Detail/"
    url_len = len(club_detail_url)
    return href[url_len : url_len + 4]


def _get_sex_from_image(info_element):
    try:
        sex_image_url = info_element.find_all("image")[0].get("src")
        sex_file_name = os.path.basename(urllib.parse.urlsplit(sex_image_url).path)
        return os.path.splitext(sex_file_name)[0]
    except IndexError:
        return ""


def get_first_and_family_name(name):
    name_index = 0
    for name_character in name:
        if name_character.islower():
            if name_index > 0:
                name_index -= 1
            break
        name_index += 1
    family_name = name[:name_index].strip()
    first_name = name[name_index:]
    return first_name, family_name


def parse_player_details(html):
    player_details = dict()
    soup = bs4(html, "html.parser")
    try:
        detail_body = soup.find_all("div", "detail-body player", limit=1)[0]
    except IndexError:
        return {}

    title = detail_body.find(id="player-title").text
    first_bracket = title.find("(")
    player_details["name"] = title[: first_bracket - 1]
    player_details["id"] = title[first_bracket + 1 : -1]

    try:
        player_details["image"] = detail_body.find_all("img", recursive=False, limit=1)[
            0
        ].get("src")
    except IndexError:
        player_details["image"] = None

    info = detail_body.find(id="colInfo").dl
    current_label = None
    for info_element in info.find_all():
        if info_element.name == "dt":
            current_label = info_element.text[:-1].strip()
        elif info_element.name == "dd":
            if current_label not in PLAYER_INFO_LABELS:
                player_details[current_label] = info_element.text.strip()
                continue
            if current_label == "Sexe":
                player_details[PLAYER_INFO_LABELS[current_label]] = _get_sex_from_image(
                    info_element
                )
            else:
                player_details[PLAYER_INFO_LABELS[current_label]] = info_element.text.strip()
    player_details["double points"] = _extract_value_from_ranking_text(
        player_details["double points"]
    )

    return player_details


def parse_tournament_and_date(info_element):
    tournament_type = tournament_date = tournament_name = None
    name_start_index = 0
    tournament_or_meeting_id = None
    tournament_type_image_url = info_element.find("image").get("src")
    if "tounoi-icon.png" in tournament_type_image_url:
        tournament_type = "tournament"
        name_start_index = info_element.text.index("Tournoi ") + len("Tournoi ")
        details_url = info_element.find(
            "a", {"title": "Plus d'info sur le tournoi"}
        ).get("data-url")
        last_slash_index = details_url.rindex("/")
        tournament_or_meeting_id = details_url[last_slash_index+1:]
    elif "ic-icon.png" in tournament_type_image_url:
        tournament_type = "interclub"
        name_start_index = info_element.text.index("vs ") + len("vs ")
        details_url = info_element.find("a", {"title": "Détail de la rencontre"}).get(
            "data-url"
        )
        parsed_url = urllib.parse.urlparse(details_url)
        tournament_or_meeting_id = urllib.parse.parse_qs(parsed_url.query)["meetingId"][
            0
        ]
    if tournament_type is not None:
        tournament_name_and_data = (
            info_element.text[name_start_index:].strip().split(" le")
        )
        tournament_name = tournament_name_and_data[0]
        try:
            tournament_date = tournament_name_and_data[1].strip()
        except IndexError:
            tournament_date = None
    return tournament_or_meeting_id, tournament_type, tournament_name, tournament_date


def parse_player_name_and_ranking(info_element):
    """
    The following element contains information about the opponent:
    name, ranking and a link to his details page. I take the ID of
    the opponent from that link The format of the element text is like this:
    "Contre\nMOERENHOUDT Nathan (NC)"
    """
    try:
        name_and_ranking = info_element.text.strip()
        name_end_index = name_and_ranking.index("(")
        player_name = name_and_ranking[: name_end_index].strip()
        player_ranking = name_and_ranking[name_end_index + 1 : -1]
    except ValueError:
        player_name = None
        player_ranking = None
    details_url = info_element.get("data-url")
    player_id = details_url[details_url.rindex("/") + 1 :]
    return player_id, player_name, player_ranking


def parse_score(info_element, sets_delimiter="-"):
    result = info_element.text.strip()
    set_scores = result.split(sets_delimiter)
    try:
        score = [list(map(int, set_score.split("/"))) for set_score in set_scores]
    except ValueError:
        score = None
    return score, result


def parse_single_match(info_elements):
    match_data = dict()
    tournament_data = parse_tournament_and_date(info_elements[0])
    if tournament_data[1] == "tournament":
        match_data["tournament id"], match_data["tournament type"], match_data[
            "tournament name"
        ], match_data["date"] = tournament_data
    else:
        match_data["interclub meeting id"], match_data["tournament type"], match_data[
            "tournament name"
        ], match_data["date"] = tournament_data

    # The name of the category, like "Simples Jeunes Gens - 13 II (2005-2006)"
    match_data["category"] = info_elements[1].text.strip()

    current_index = 2
    if info_elements[current_index].text.strip().startswith("Contre"):
        opponent_info = parse_player_name_and_ranking(info_elements[current_index].find("a"))
        match_data["opponent id"], match_data["opponent name"], match_data[
            "opponent ranking"
        ] = opponent_info
        current_index += 1
    else:
        match_data["opponent id"] = match_data["opponent name"] = match_data[
            "opponent ranking"
        ] = None

    try:
        score = parse_score(info_elements[current_index])
    except IndexError:
        score = None, None
    match_data["score"], match_data["text score"] = score

    return match_data


def parse_double_match(info_elements):
    match_data = dict()
    tournament_data = parse_tournament_and_date(info_elements[0])
    if tournament_data[1] == "tournament":
        match_data["tournament id"], match_data["tournament type"], match_data[
            "tournament name"
        ], match_data["date"] = tournament_data
    else:
        match_data["interclub meeting id"], match_data["tournament type"], match_data[
            "tournament name"
        ], match_data["date"] = tournament_data

    # The name of the category, like "Simples Jeunes Gens - 13 II (2005-2006)"
    match_data["category"] = info_elements[1].text.strip()

    current_index = 2
    if info_elements[current_index].text.strip().startswith("Avec"):
        partner_info = parse_player_name_and_ranking(info_elements[2].find("a"))
        match_data["partner id"], match_data["partner name"], match_data[
            "partner ranking"
        ] = partner_info
        current_index += 2
    else:
        match_data["partner id"] = match_data["partner name"] = match_data[
            "partner ranking"
        ] = None
        current_index += 1

    if info_elements[current_index].text.strip().startswith("Contre"):
        opponent_info_elements = info_elements[current_index].find_all("a")
        opponent_info = parse_player_name_and_ranking(opponent_info_elements[0])
        match_data["opponent 1 id"], match_data["opponent 1 name"], match_data[
            "opponent 1 ranking"
        ] = opponent_info
        opponent_info = parse_player_name_and_ranking(opponent_info_elements[1])
        match_data["opponent 2 id"], match_data["opponent 2 name"], match_data[
            "opponent 2 ranking"
        ] = opponent_info
        current_index += 2
    else:
        match_data["opponent 1 id"] = match_data["opponent 1 name"] = match_data[
            "opponent 1 ranking"
        ] = None
        match_data["opponent 2 id"] = match_data["opponent 2 name"] = match_data[
            "opponent 2 ranking"
        ] = None
        current_index += 1

    try:
        score = parse_score(info_elements[current_index])
    except IndexError:
        score = None, None
    match_data["score"], match_data["text score"] = score

    return match_data


def parse_matches(html, match_type="single"):
    assert match_type in ("single", "double")
    soup = bs4(html, "html.parser")
    matches = list()
    victory_div_id = "collapse_player_vicdef_victory_{}".format(match_type[0].upper())
    victory_div = soup.find("div", {"id": victory_div_id})
    if victory_div is not None:
        for match_element in victory_div.find_all("dl"):
            match_info_elements = match_element.find_all("dd")
            if match_type == "single":
                match_data = parse_single_match(match_info_elements)
            else:
                match_data = parse_double_match(match_info_elements)
            match_data["result"] = "victory"
            matches.append(match_data)
    defeat_div_id = "collapse_player_vicdef_defeat_{}".format(match_type[0].upper())
    defeat_div = soup.find("div", {"id": defeat_div_id})
    if defeat_div is not None:
        for match_element in defeat_div.find_all("dl"):
            match_info_elements = match_element.find_all("dd")
            if match_type == "single":
                match_data = parse_single_match(match_info_elements)
            else:
                match_data = parse_double_match(match_info_elements)
            match_data["result"] = "defeat"
            matches.append(match_data)
    return matches


def parse_players(html):
    soup = bs4(html, "html.parser")
    players = dict()
    for player in soup.find_all("dl"):
        fields = player.find_all("dd")
        player_name, player_id = _get_name_and_id(fields[0].a.text)
        new_player = dict(
            name=player_name,
            id=player_id,
            single_ranking=fields[1].text,
            double_ranking=fields[2].text[len("Valeur double: ") :],
            club_name=fields[3].text,
            club_id=_extract_club_id_from_href(fields[3].a["href"]),
        )
        players[player_id] = new_player
    return players


def get_player_details(player_id):
    url = "http://www.aftnet.be/MyAFT/Players/Detail/{}".format(player_id)
    html = requests.get(url).text
    player = parse_player_details(html)
    return player


def get_player_matches(player_id):
    url = "http://www.aftnet.be//MyAFT/Players/VictoryDefeatSingle?numFed={}".format(
        player_id
    )
    html = requests.get(url).text
    single_matches = parse_matches(html, match_type="single")
    url = "http://www.aftnet.be//MyAFT/Players/VictoryDefeatDouble?numFed={}".format(
        player_id
    )
    html = requests.get(url).text
    double_matches = parse_matches(html, match_type="double")
    return single_matches, double_matches


def search_players(region=1, name=u"", male=True, female=True, club_id=""):

    session = requests.Session()

    def search_player_chunks(
        total_records=0, region=1, name=u"", male=True, female=True, club_id=""
    ):
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
            region=region,
            name=name,
            male=male,
            female=female,
            club_id=club_id,
        )
        new_players_count = len(new_players)
        total_players_count += new_players_count
        yield new_players
        if len(new_players) < 10:
            break

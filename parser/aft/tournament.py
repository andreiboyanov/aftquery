import json
import urllib.parse
import urllib.request
from datetime import datetime
from calendar import monthrange
from bs4 import BeautifulSoup as bs4

from .players import parse_player_name_and_ranking, parse_score


def parse_category(element):
    category = {"_id": element["value"], "name": element.text}
    return category


def parse_categories_dropdown(html):
    soup = bs4(html, features="html.parser")
    for category in soup.find_all("option")[1:]:
        try:
            yield parse_category(category)
        except KeyError:
            pass


def get_all_categories():
    url = (
        "http://www.aftnet.be/MyAFT/Competitions/GetCompetitionTournamentsCategoriesDdl"
    )
    html = urllib.request.urlopen(url).read()
    yield from parse_categories_dropdown(html)


def parse_tournament(tournament):
    result = dict()
    info_elements = tournament.find_all("dd")
    name_and_date = info_elements[0].text.strip()
    try:
        delimiter_index = name_and_date.rindex(" ")
        result["name"] = name_and_date[:delimiter_index]
        result["date"] = name_and_date[delimiter_index + 1 :]
    except ValueError:
        result["name"] = ""
        result["date"] = name_and_date

    tournament_details_url = info_elements[0].find("a").get("data-url")
    result["_id"] = tournament_details_url.split("/")[-1]

    category_text = info_elements[1].text.strip()
    if "inscri" in category_text:
        result["tournament category"] = ""
    else:
        result["tournament category"] = category_text

    criterium = info_elements[2].text.strip()
    if criterium:
        result["criterium"] = criterium
    return result


def parse_tournaments(html):
    soup = bs4(html, features="html.parser")
    for tournament in soup.find_all("dl"):
        yield parse_tournament(tournament)


def get_season_weeks(month):
    url = (
        "http://www.aftnet.be/MyAFT/Competitions/GetSeasonWeeksDdl?firstDayOfMonth=?firstDayOfMonth={}"
        "&tabName=NearMyPlace"
        "".format(month)
    )
    web_data = urllib.parse.urlencode(
        {"firstDyaOfMonth": month, "tabName": "NearMyPlace"}
    )
    html = urllib.request.urlopen(url, web_data.encode("utf-8")).read()

    soup = bs4(html, features="html.parser")
    weeks = list()
    for week_element in soup.find_all("option")[1:]:
        weeks.append(week_element["value"])
    return weeks


def get_tournaments_for_current_year():
    current_year = datetime.now().year
    previous_year = current_year - 1
    months = [
        (
            "01/{}/{}".format(month, previous_year),
            "{}/{}/{}".format(
                monthrange(previous_year, month)[1], month, previous_year
            ),
        )
        for month in [11, 12]
    ]
    months += [
        (
            "01/{}/{}".format(month, current_year),
            "{}/{}/{}".format(monthrange(current_year, month)[1], month, current_year),
        )
        for month in range(1, 13)
    ]
    processed_ids = list()
    for region in range(1, 10):
        for month in months:
            url = "http://www.aftnet.be/MyAFT/Competitions/TournamentSearchResultData"
            query = urllib.parse.urlencode(
                {
                    "Region": str(region),
                    "SearchByGeoloc": "false",
                    "PeriodStartDate": month[0],
                    "PeriodEndDate": month[1],
                }
            )

            html = urllib.request.urlopen(url, query.encode("utf-8")).read()
            tournaments = parse_tournaments(html)
            for tournament in tournaments:
                if tournament["_id"] not in processed_ids:
                    processed_ids.append(tournament["_id"])
                    yield tournament


def parse_player_info(info_element):
    player_id, name, ranking = parse_player_name_and_ranking(info_element.strong.a)
    club_text = info_element.text
    club_name = club_text[club_text.rfind("(") + 1 : club_text.rfind(")")]
    winner_icon = info_element.find("img", src="/MyAFT/Content/Images/checkIcon.png")
    winner = winner_icon is not None
    return player_id, name, ranking, club_name, winner


def parse_category_info(info_element):
    name = info_element.text.strip()
    category_url = urllib.parse.urlparse(info_element.a["data-url"])
    category_id = None
    return name, category_id


def parse_single_matches(tournament_id, soup):
    for match_element in soup.find_all("dl", {"class": "grid-data-item"}):
        info_elements = match_element.find_all("dd")
        player_1_id, player_1_name, player_1_ranking, player_1_club, player_1_won = parse_player_info(
            info_elements[0]
        )
        player_2_id, player_2_name, player_2_ranking, player_2_club, player_2_won = parse_player_info(
            info_elements[2]
        )
        category_name, category_id = parse_category_info(info_elements[4])
        tournament_stage = info_elements[5].text.strip()
        match_date_and_time = info_elements[6].text.strip()
        score, result = parse_score(info_elements[7], " ")
        match = {
            "player 1 id": player_1_id,
            "player 1 name": player_1_name,
            "player 1 ranking": player_1_ranking,
            "player 1 club": player_1_club,
            "player 2 id": player_2_id,
            "player 2 name": player_2_name,
            "player 2 ranking": player_2_ranking,
            "player 2 club": player_2_club,
            "tournament id": tournament_id,
            "tournament stage": tournament_stage,
            "category id": category_id,
            "category name": category_name,
            "date and time": match_date_and_time,
            "score": score,
            "text score": result,
            "winner": 1 if player_1_won else 2,
        }
        yield match


def get_tournament_matches(tournament_id):
    matches = list()
    url = "http://www.aftnet.be/MyAFT/Competitions/SearchTournamentMatches"
    query = {
        "idTournoi": tournament_id,
        "meetingDateFrom": "01/11/2017",
        "meetingDateTo": "31/12/2018",
        "numFedOrName": "",
        "clubIdOrName": "",
        "singleOrDouble": "S",
    }
    html = urllib.request.urlopen(
        url, urllib.parse.urlencode(query).encode("utf-8")
    ).read()
    soup = bs4(html, features="html.parser")
    single_matches_element = soup.find("div", {"id": "collapse_result_matches_single"})
    if single_matches_element:
        matches += list(parse_single_matches(tournament_id, single_matches_element))
        page_count_element = single_matches_element.find(
            "div", {"id": "divActionBottomMatchesResult_S"}
        )
        if page_count_element is not None:
            page_count = page_count_element.a["data-totalpages"]
        else:
            page_count = 1
        for page_number in range(2, int(page_count) + 1):
            url = "http://www.aftnet.be/MyAFT/Competitions/GetTournamentMatchesResultByPage"
            query.update(pageNumber=page_number)
            html = urllib.request.urlopen(
                url, urllib.parse.urlencode(query).encode("utf-8")
            ).read()
            soup = bs4(html, features="html.parser")
            matches += list(parse_single_matches(tournament_id, soup))
    return matches


def parse_tournament_category_from_dropdown(category_element):
    category_id_and_draws = category_element["value"].split("|")
    try:
        category_id, draw_types = category_id_and_draws
    except ValueError:
        category_id, draw_types = category_id_and_draws[0], ""
    category_name, category_rankings = category_element.text.strip().split("(")
    category_rankings = category_rankings[:-1]
    return {
        "_id": category_id,
        "name": category_name,
        "rankings": category_rankings,
        "draw types": draw_types,
    }


def parse_tournament_category(category_element):
    category_id = category_element["id"].split("-")[1]
    info_elements = category_element.find_all("dd")
    category_name = info_elements[0].text.strip()
    category_rankings = info_elements[1].text.strip()
    is_for_criterium = info_elements[2].input["checked"] == "checked"
    return {
        "_id": category_id,
        "name": category_name,
        "rankings": category_rankings,
        "criterium": is_for_criterium,
    }


def parse_tournament_categories(html):
    soup = bs4(html, features="html.parser")
    category_elements = soup.find("select", {"id": "drawCategory"}).find_all("option")[
        1:
    ]
    for category_element in category_elements:
        yield parse_tournament_category_from_dropdown(category_element)


def parse_tournament_category_draws(tournament_id, category):
    for draw_type in category["draw types"]:
        url = "http://www.aftnet.be/MyAFT/Competitions/GetTournamentDrawData"
        query = {
            "idTournoi": tournament_id,
            "idCategory": category["_id"],
            "drawType": draw_type,
            "selectedRoundIndex": "",
            "selectedRowIndex": "",
        }
        response = urllib.request.urlopen(
            url, urllib.parse.urlencode(query).encode("utf-8")
        ).read()
        draw_data = json.loads(response.decode())
        draw_rounds = json.loads(draw_data["drawData"])
        draw_round_names = json.loads(draw_data["roundNames"])
        for round_index, draw_round in enumerate(draw_rounds):
            for match in draw_round:
                if len(match) < 2:
                    break
                player_1, player_2 = match
                if player_1["id"] == "virtual_final_team":
                    break
                match_score = list(
                    zip(player_1["score"].split("-"), player_2["score"].split("-"))
                )
                match_score = [
                    (int(set_score[0]), int(set_score[1])) for set_score in match_score if set_score != ("", "")
                ]
                match_description = {
                    "_id": player_2["matchId"],
                    "tournament id": tournament_id,
                    "category id": category["_id"],
                    "category name": category["name"],
                    "category rankings": category["rankings"],
                    "draw type": draw_type,
                    "round": round_index + 1,
                    "player 1 id": player_1["id"],
                    "player 1 name": player_1["name"],
                    "player 1b id": player_1["idB"],
                    "player 1b name": player_1["nameB"],
                    "player 1 seed": player_1["seed"],
                    "player 1 won": player_1["statusWin"] == "V",
                    "player 1 has stats": player_1["hasStats"],
                    "player 1 result type": player_1["resultType"],
                    "player 1 draw position": player_1["drawPosition"],
                    "player 2 id": player_2["id"],
                    "player 2 name": player_2["name"],
                    "player 2b id": player_2["idB"],
                    "player 2b name": player_2["nameB"],
                    "player 2 seed": player_2["seed"],
                    "player 2 won": player_2["statusWin"] == "V",
                    "player 2 has stats": player_2["hasStats"],
                    "player 2 result type": player_2["resultType"],
                    "player 2 draw position": player_2["drawPosition"],
                    "winner": 1 if player_1["statusWin"] == "V" else 2,
                    "player 1 win status": player_1["statusWin"],
                    "player 2 win status": player_2["statusWin"],
                    "score": match_score,
                }
                yield match_description


def get_tournament_draws(tournament_id):
    url = "http://www.aftnet.be/MyAFT/Competitions/TournamentDraw?idTournoi={}".format(
        tournament_id
    )
    html = urllib.request.urlopen(url).read()
    categories = list(parse_tournament_categories(html))
    for category in categories:
        yield from parse_tournament_category_draws(tournament_id, category)

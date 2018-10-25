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
    for month in months:

        url = "http://www.aftnet.be/MyAFT/Competitions/TournamentSearchResultData"
        query = urllib.parse.urlencode(
            {
                "Region": "1,3,4,6",
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
    category_id = category_url.path.split("/")[-1]
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

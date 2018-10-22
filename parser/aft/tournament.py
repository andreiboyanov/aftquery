import urllib.parse
import urllib.request
from datetime import datetime
from bs4 import BeautifulSoup as bs4


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
        result["date"] = name_and_date[delimiter_index + 1:]
    except ValueError:
        result["name"] = ""
        result["date"] = name_and_date

    tournament_details_url = info_elements[0].find("a").get("data-url")
    result["_id"] = tournament_details_url.split("/")[-1]

    result["tournament category"] = info_elements[1].text.strip()
    criterium = info_elements[2].text.strip()
    if criterium:
        result["criterium"] = criterium
    return result


def parse_tournaments(html):
    soup = bs4(html, features="html.parser")
    for tournament in soup.find_all("dl"):
        yield parse_tournament(tournament)


def get_tournaments_for_current_year():
    current_year = datetime.now().year
    previous_year = current_year - 1
    months = ["01/{}/{}".format(month, previous_year) for month in [11, 12]]
    months += ["01/{}/{}".format(month, current_year) for month in range(1, 13)]
    processed_ids = list()
    for month in months:
        url = (
            "http://www.aftnet.be/MyAFT/Competitions/GetCompetitionsTournamentsByRegionResult?firstDayOfMonth={}"
            "".format(month)
        )
        html = urllib.request.urlopen(url).read()
        for tournament in parse_tournaments(html):
            if tournament["_id"] not in processed_ids:
                processed_ids.append(tournament["_id"])
                yield tournament

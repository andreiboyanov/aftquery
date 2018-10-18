import urllib.parse
import urllib.request
from bs4 import BeautifulSoup as bs4

from .common import _get_name_and_id


def parse_clubs(html):
    soup = bs4(html, features="html.parser")
    for club in soup.find_all('dl'):
        club_name, club_id = _get_name_and_id(club.a.text)
        new_club = dict(name=club_name, id=club_id)
        yield new_club


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
    webdata = urllib.parse.urlencode(data)
    html = urllib.request.urlopen(url, webdata.encode("utf-8")).read()
    for club in parse_clubs(html):
        yield club


import re
import urllib.parse
import urllib.request
from bs4 import BeautifulSoup as bs4


def get_ranking_prevision(player_id, first_name, last_name):
    url = "https://www.classement-tennis.be/joueur/{}_{}_{}.html".format(
        player_id,
        urllib.parse.quote(first_name),
        urllib.parse.quote(last_name)
    )

    html = urllib.request.urlopen(url).read()
    soup = bs4(html, features="html.parser")
    prevision_element = soup.find(string=re.compile("Notre prédiction du nouveau classement: .*"))
    if not prevision_element:
        return None
    new_ranking = prevision_element.split(":")[1].strip()
    return new_ranking

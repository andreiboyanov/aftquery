import re
import urllib.parse
import urllib.request
from bs4 import BeautifulSoup as bs4


def get_ranking_prevision(player_id):
    url = "https://www.classement-tennis.be/calcul.html?aft_id={}".format(player_id)

    html = urllib.request.urlopen(url).read()
    soup = bs4(html, features="html.parser")
    prevision_element = soup.find(string=re.compile("Notre prédiction du nouveau classement: .*"))
    if not prevision_element:
        return None
    new_ranking = prevision_element.split(":")[1].strip()
    return new_ranking

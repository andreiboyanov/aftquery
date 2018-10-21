import sys
from datetime import datetime
import pymongo
from aftquery.parser.aft import players as aft_players

import traceback
import logging
logging.basicConfig(filename='logs/{}.log'.format(datetime.now()),level=logging.DEBUG)

def pull_player_matches(db, player_id, year):
    single_matches, double_matches = aft_players.get_player_matches(player_id=player_id)
    matches_label = "matches.{}".format(year)
    db.players.update_one(
        {"_id": player_id},
        {
            "$set": {
                matches_label: {
                    "single": single_matches,
                    "double": double_matches,
                }
            }
        },
    )


def main(arguments):
    client = pymongo.MongoClient()
    db = client.aft_collector
    current_year = datetime.now().year
    if len(arguments) >= 1:
        query = {'_id': arguments[0]}
    else:
        query = {'matches': {"$exists": False}}
    all_players = db.players.find(query)
    current_index = 1
    all_players_count = all_players.count()
    for player in all_players:

        player_id = player["_id"]
        player_name = player["name"]
        try:
            pull_player_matches(db, player_id, current_year)
            print("({}/{})".format(current_index, all_players_count), player_id, player_name, "...pulled from aft")
            current_index += 1
        except Exception as error:
            logging.error("{} {} ==> {}".format(player_id, player_name, error))
            logging.debug(traceback.format_exc())


if __name__ == "__main__":
    main(sys.argv[1:])


import sys
import argparse
import pymongo
from datetime import datetime
from aftquery.parser.classement_tennis import ranking

import logging

logging.basicConfig(
    filename="logs/{}_get_ranking_prevision.log".format(datetime.now()),
    level=logging.DEBUG,
)


def set_player_ranking(db, player, year, index, count):
    name_chunks = player["name"].split(" ")
    first_name = name_chunks[-1]
    last_name = "_".join(name_chunks[:-1])
    new_ranking = ranking.get_ranking_prevision(player["_id"], first_name, last_name)
    if new_ranking:
        print(
            "{}/{}".format(index, count),
            player["_id"],
            player["name"],
            player["single_ranking"],
            new_ranking,
        )
        db.players.find_one_and_update(
            filter={"_id": player["_id"]},
            update={
                "$currentDate": {"last_updated": True},
                "$set": {"ranking.{}.single".format(year): new_ranking},
            },
            upsert=True,
        )
    else:
        print(
            "{}/{}".format(index, count),
            player["_id"],
            player["name"],
            player["single_ranking"],
            "New ranking not found",
        )
        logging.error(
            "%s %s %s %s",
            player["_id"],
            player["name"],
            player["single_ranking"],
            "New ranking not found",
        )


def main(arguments):
    client = pymongo.MongoClient()
    db = client.aft_collector
    next_year = datetime.now().year + 1
    if arguments.player_id:
        player = db.players.find({"_id": arguments.player_id})[0]
        set_player_ranking(db, player, next_year, 1, 1)
        return

    all_players = db.players.find(
        {}, {"_id": True, "name": True, "single_ranking": True}, no_cursor_timeout=True
    )
    count = all_players.count()
    for index, player in enumerate(all_players):
        set_player_ranking(db, player, next_year, index, count)
    all_players.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        "Get the prevision for the next year ranking from classement-tennis.be"
    )
    parser.add_argument("-p", "--player-id", help="Get ranking for given player only")
    arguments = parser.parse_args(sys.argv[1:])
    main(arguments)

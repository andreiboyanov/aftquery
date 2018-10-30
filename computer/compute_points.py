import sys
import argparse
import pymongo
from datetime import datetime

import logging

logging.basicConfig(
    filename="logs/{}_get_ranking_prevision.log".format(datetime.now()),
    level=logging.DEBUG,
)


def compute_interclub_points(db, player, year):
    interclub_points = dict(
        participation=0,
        victory=0,
        details=list(),
    )
    single_interclub_matches = [
        match
        for match in player.matches[year]["single"]
        if match["match_type"] == "interclub"
    ]
    double_interclub_matches = [
        match
        for match in player.matches[year]["double"]
        if match["match_type"] == "interclub"
    ]
    player_ranking = player.classement_tennis["2019"]["single"]


def compute_player_points(db, player, year):
    points = {"summary": {}, "details": {}}
    return points


def compute_and_save_player_points(db, player, year, index, count):
    points = compute_player_points(db, player, year)
    if points:
        print(
            "{}/{}".format(index, count),
            player["_id"],
            player["name"],
            player["single_ranking"],
            points,
        )
        db.players.find_one_and_update(
            filter={"_id": player["_id"]},
            update={
                "$currentDate": {"ranking.previsions.last_updated": True},
                "$set": {"ranking.previsions.{}.single".format(year): points},
            },
            upsert=True,
        )
    else:
        print(
            "{}/{}".format(index, count),
            player["_id"],
            player["name"],
            player["single_ranking"],
            "Points could not be calculated.",
        )
        logging.error(
            "%s %s %s %s",
            player["_id"],
            player["name"],
            player["single_ranking"],
            "Points could not be calculated",
        )


def main(arguments):
    client = pymongo.MongoClient()
    db = client.aft_collector
    year = arguments.year or datetime.now().year
    if arguments.player_id:
        player = db.players.find({"_id": arguments.player_id})[0]
        compute_and_save_player_points(db, player, year, 1, 1)
        return

    if arguments.update:
        all_players = db.players.find(
            {"ranking.previsions.{}.single".format(year): {"$exists": False}},
            {"_id": True, "name": True, "single_ranking": True},
            no_cursor_timeout=True,
        )
    else:
        all_players = db.players.find(
            {},
            {"_id": True, "name": True, "single_ranking": True},
            no_cursor_timeout=True,
        )
    count = all_players.count()
    for index, player in enumerate(all_players):
        compute_and_save_player_points(db, player, year, index, count)
    all_players.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Compute players'points")
    parser.add_argument("-p", "--player-id", help="Get ranking for given player only")
    parser.add_argument(
        "-y",
        "--year",
        help="Compute ranking for the given year. Defaults to the current year",
    )
    parser.add_argument(
        "-u",
        "--update",
        action="store_true",
        help="Skip players which already have a points calculated for the next year.",
    )
    arguments = parser.parse_args(sys.argv[1:])
    main(arguments)

import sys
import argparse
import pymongo
from datetime import datetime
from .aft_rules.ranking_points import SINGLE_RANKING_POINTS

import logging

logging.basicConfig(
    filename="logs/{}_get_ranking_prevision.log".format(datetime.now()),
    level=logging.DEBUG,
)


def compute_interclub_points(db, player, year):
    interclub_points = dict(
        participation=0,
        victory=0,
        details=dict(participations=dict(), victories=list()),
    )
    interclub_matches = db.interclub_matches.find(
        {"$or": [{"player 1 id": player["_id"]}, {"player 1b id": player["_id"]}]}
    )
    player_ranking = player["classement_tennis"]["2019"]["single"]
    for match in interclub_matches:
        meeting_id = match["interclub meeting id"]
        if match["match type"] == "single":
            opponent_id = match["player 2 id"]
            if opponent_id is not None:
                opponent = db.players.find_one({"_id": opponent_id})
                try:
                    points_won = SINGLE_RANKING_POINTS[
                        opponent["classement_tennis"]["2019"]["single"]
                    ]
                    interclub_points["details"]["victories"].append(
                        {
                            "tournament type": "interclub",
                            "match type": "single",
                            "match id": match["_id"],
                            "victory_points": points_won,
                        }
                    )
                except KeyError:
                    logging.error(
                        "Unknown ranking {} of player {} ({})".format(
                            opponent["details.single ranking"],
                            opponent["name"],
                            opponent_id,
                        )
                    )
            else:
                logging.warning(
                    "Player {} ({}) had no opponent for the match {} "
                    "during the interclubs meeting {}".format(
                        player["name"],
                        player["_id"],
                        match["_id"],
                        meeting_id,
                    )
                )
        if meeting_id not in interclub_matches["details"]["participations"]:
            meeting_matches = db.interclub_matches.find(
                {
                    "interclub meeting id": meeting_id,
                    "opponent team": match["opponent team"]
                }
            )
            team_players = set()
            for meeting_match in meeting_matches:
                team_players.add(meeting_match["player 1 id"])
                if "player 1b id" in meeting_match:
                    team_players.add(meeting_match["player 1b id"])
                players_count = len(team_players)
                try:
                    interclub_points["details"]["participations"][meeting_id] = SINGLE_RANKING_POINTS[player_ranking] * players_count
                except KeyError:
                    logging.error(
                        "Unknown ranking {} of player {} ({})".format(
                            player_ranking,
                            player["name"],
                            player["_id"],
                        )
                    )


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

import sys
import argparse
import pymongo
from datetime import datetime

import logging
import traceback

logging.basicConfig(
    filename="logs/{}_get_extract_interclub.log".format(datetime.now()),
    level=logging.DEBUG,
)


def create_double_interclub_match(db, player, year, match):
    year = str(year)
    player_1 = player
    player_1_ranking = (
        player_1["classement_tennis"]["2019"]["single"]
        if "classement_tennis" in player_1
        else None
    )
    double_match = {
        "_id": "{}_double_{}".format(match["interclub meeting id"], player_1["_id"]),
        "interclub meeting id": match["interclub meeting id"],
        "date": match["date"],
        "opponents team": match["tournament name"],
        "category name": match["category"],
        "match type": "double",
        "player 1 id": player_1["_id"],
        "player 1 name": player_1["name"],
        "player 1 ranking": player_1_ranking,
        "winner": 1 if match["result"] == "victory" else 2,
        "score": match["score"],
    }

    player_1b = db.players.find_one({"_id": match["partner id"]})
    if player_1b is None:
        logging.warning(
            "Could not find the partner for the double match of {} {} in the interclub meting {}".format(
                player["_id"], player["name"], match["interclub meeting id"]
            )
        )
    else:
        player_1b_ranking = (
            player_1b["classement_tennis"]["2019"]["single"]
            if "classement_tennis" in player_1b
            else None
        )

        double_match.update(
            {
                "player 1b id": player_1b["_id"],
                "player 1b name": player_1b["name"],
                "player 1b ranking": player_1b_ranking,
            }
        )

    player_2 = db.players.find_one({"_id": match["opponent 1 id"]})
    if player_2 is None:
        logging.warning(
            "Could not find the opponent for the double match of {} {} in the interclub meting {}".format(
                player["_id"], player["name"], match["interclub meeting id"]
            )
        )
    else:
        player_2_ranking = (
            player_2["classement_tennis"]["2019"]["single"]
            if "classement_tennis" in player_2
            else None
        )
        double_match.update(
            {
                "player 2 id": player_2["_id"],
                "player 2 name": player_2["name"],
                "player 2 ranking": player_2_ranking,
            }
        )

        player_2b = db.players.find_one({"_id": match["opponent 2 id"]})
        if player_2b is None:
            logging.warning(
                "Could not find the partner for the double match of {} {} in the interclub meting {}".format(
                    player_2["_id"], player_2["name"], match["interclub meeting id"]
                )
            )
        else:
            player_2b_ranking = (
                player_2b["classement_tennis"]["2019"]["single"]
                if "classement_tennis" in player_2b
                else None
            )
            opponent_match = [
                opponent_match
                for opponent_match in player_2["matches"][year]["double"]
                if opponent_match["tournament type"] == "interclub"
                and opponent_match["interclub meeting id"]
                == match["interclub meeting id"]
                and (
                    opponent_match["opponent 1 id"] == player["_id"]
                    or opponent_match["opponent 2 id"] == player["_id"]
                )
            ]
            if opponent_match:
                players_team = opponent_match[0]["tournament name"]
            else:
                players_team = None
                logging.warning(
                    "Could not find the the double match of {} {} in the interclub meting {} "
                    "against {} {} in the opponent's records".format(
                        player_2["_id"],
                        player_2["name"],
                        match["interclub meeting id"],
                        player_2["_id"],
                        player_2["name"],
                    )
                )
            double_match.update(
                {
                    "players team": players_team,
                    "player 2 id": player_2["_id"],
                    "player 2 name": player_2["name"],
                    "player 2 ranking": player_2_ranking,
                    "player 2b id": player_2b["_id"],
                    "player 2b name": player_2b["name"],
                    "player 2b ranking": player_2b_ranking,
                }
            )
    return double_match


def create_single_interclub_match(db, player, year, match):
    player_1 = player
    player_1_ranking = (
        player_1["classement_tennis"]["2019"]["single"]
        if "classement_tennis" in player_1
        else None
    )
    single_match = {
        "_id": "{}_single_{}".format(match["interclub meeting id"], player_1["_id"]),
        "interclub meeting id": match["interclub meeting id"],
        "date": match["date"],
        "opponents team": match["tournament name"],
        "category name": match["category"],
        "match type": "single",
        "player 1 id": player_1["_id"],
        "player 1 name": player_1["name"],
        "player 1 ranking": player_1_ranking,
        "winner": 1 if match["result"] == "victory" else 2,
        "score": match["score"],
    }

    player_2 = db.players.find_one({"_id": match["opponent id"]})
    if player_2 is None:
        logging.warning(
            "Could not find the opponent for the single match of {} {} in the interclub meting {}".format(
                player["_id"], player["name"], match["interclub meeting id"]
            )
        )
    else:
        player_2_ranking = (
            player_2["classement_tennis"]["2019"]["single"]
            if "classement_tennis" in player_2
            else None
        )
        opponent_match = [
            opponent_match
            for opponent_match in player_2["matches"][year]["single"]
            if opponent_match["tournament type"] == "interclub"
            and opponent_match["interclub meeting id"] == match["interclub meeting id"]
            and opponent_match["opponent id"] == player["_id"]
        ]
        if opponent_match:
            players_team = opponent_match[0]["tournament name"]
        else:
            players_team = None
            logging.warning(
                "Could not find the the single match of {} {} in the interclub meting {} "
                "against {} {} in the opponent's records".format(
                    player_2["_id"],
                    player_2["name"],
                    match["interclub meeting id"],
                    player_2["_id"],
                    player_2["name"],
                )
            )
        single_match.update(
            {
                "players team": players_team,
                "player 2 id": player_2["_id"] if player_2 is not None else "",
                "player 2 name": player_2["name"] if player_2 is not None else "",
                "player 2 ranking": player_2_ranking,
            }
        )
    return single_match


def extract_interclub_matches(db, player, year, index, count):
    print(
        "{}/{}".format(index, count),
        player["_id"],
        player["name"],
        player["single_ranking"],
    )

    db.interclub_matches.delete_many({"player 1 id": player["_id"]})
    for match in player["matches"][year]["single"]:
        try:
            if match["tournament type"] == "interclub":
                single_match = create_single_interclub_match(db, player, year, match)
                db.interclub_matches.insert_one(single_match)
        except:
            logging.error(
                "Couldn't proceed with player {} {}".format(
                    player["_id"], player["name"]
                )
            )
            logging.debug(traceback.format_exc())
    for match in player["matches"][year]["double"]:
        try:
            if match["tournament type"] == "interclub":
                same_match = db.interclub_matches.find(
                    {
                        "interclub meeting id": match["interclub meeting id"],
                        "player 1b id": player["_id"],
                    }
                )
                if same_match.count() > 0:
                    continue
                double_match = create_double_interclub_match(db, player, year, match)
                db.interclub_matches.insert_one(double_match)
        except:
            logging.error(
                "Couldn't proceed with player {} {}".format(
                    player["_id"], player["name"]
                )
            )
            logging.debug(traceback.format_exc())
    db.players.find_and_modify(
        query={"_id": player["_id"]},
        update={
            "$currentDate": {"last_exported_interclubs": True},
        },
        upsert=False,
    )

def main(arguments):
    client = pymongo.MongoClient()
    db = client.aft_collector
    year = arguments.year or str(datetime.now().year)
    if arguments.player_id:
        player = db.players.find({"_id": arguments.player_id})[0]
        extract_interclub_matches(db, player, year, 1, 1)
        return

    if arguments.update:
        query = {
                "last_exported_interclubs": {"$exists": False}
        }
    else:
        query = {}
    all_players = db.players.find(
        query,
        {
            "_id": True,
            "name": True,
            "single_ranking": True,
            "matches": True,
            "classement_tennis": True,
        },
        no_cursor_timeout=True,
    )
    count = all_players.count()
    for index, player in enumerate(all_players):
        if "matches" not in player:
            continue
        extract_interclub_matches(db, player, year, index, count)
    all_players.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        "Create a separate collection with interclub matches extracting the from the players collection"
    )
    parser.add_argument(
        "-p", "--player-id", help="Extract interclub matches for given player only"
    )
    parser.add_argument(
        "-y",
        "--year",
        help="Extract matches for the specified year. Defaults to the current year.",
    )
    parser.add_argument(
        "-u",
        "--update",
        action="store_true",
        help="Skip players that already have interclub matches in the database.",
    )
    arguments = parser.parse_args(sys.argv[1:])
    main(arguments)

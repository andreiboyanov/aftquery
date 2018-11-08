import re
import sys
import argparse
import pymongo
from datetime import datetime
from aftquery.computer.aft_rules.ranking_points import SINGLE_RANKING_POINTS

import logging

logging.basicConfig(
    filename="logs/{}_get_ranking_prevision.log".format(datetime.now()),
    level=logging.DEBUG,
)


def compute_interclub_points(db, player, year):
    interclub_points = dict(total=0, details=dict())
    interclub_matches = db.interclub_matches.find(
        {"$or": [{"player 1 id": player["_id"]}, {"player 1b id": player["_id"]}]}
    )
    try:
        player_ranking = player["classement_tennis"]["2019"]["single"]
    except KeyError:
        player_ranking = player["single_ranking"]
    try:
        player_points = SINGLE_RANKING_POINTS[player_ranking]
    except KeyError:
        player_points = 0
        logging.error(
            "Unknown ranking {} of player {} ({})".format(
                player_ranking, player["name"], player["_id"]
            )
        )
    for match in interclub_matches:
        meeting_id = match["interclub meeting id"]
        if meeting_id not in interclub_points["details"]:
            interclub_points["details"][meeting_id] = dict(participation=0, victory=0)
        if match["match type"] == "single" and match["winner"] == 1:
            if "player 2 id" in match:
                opponent_id = match["player 2 id"]
                opponent = db.players.find_one({"_id": opponent_id})
                try:
                    points_won = SINGLE_RANKING_POINTS[
                        opponent["classement_tennis"]["2019"]["single"]
                    ]
                    interclub_points["details"][meeting_id]["victory"] += points_won
                except KeyError:
                    logging.error(
                        "Unknown ranking {} of player {} ({})".format(
                            opponent["classement_tennis"]["2019"]["single"],
                            opponent["name"],
                            opponent_id,
                        )
                    )
            else:
                logging.warning(
                    "Player {} ({}) had no opponent for the match {} "
                    "during the interclubs meeting {}".format(
                        player["name"], player["_id"], match["_id"], meeting_id
                    )
                )
        interclub_points["details"][meeting_id]["participation"] += player_points
    for meeting_id in interclub_points["details"]:
        interclub_points["details"][meeting_id]["total"] = (
            interclub_points["details"][meeting_id]["victory"]
            + interclub_points["details"][meeting_id]["participation"]
        )
    ordered_totals = sorted(
        [meeting["total"] for meeting in interclub_points["details"].values()],
        reverse=True,
    )
    interclub_points["total"] = sum(ordered_totals[:5])
    return interclub_points


def compute_player_points(db, player, year):
    points = {
        "summary": None,
        "details": {
            "interclubs": compute_interclub_points(db, player, year),
            "tournaments": compute_tournament_points(db, player, year),
        },
    }
    points["summary"] = {
        "interclubs": points["details"]["interclubs"]["total"],
        "total": points["details"]["interclubs"]["total"],
    }
    return points


def get_draw_details(db, player_id, category_id):
    category_details = dict(victory=0, participation=0, stage=0, matches=list())
    rounds = db.aft_tournament_draws.aggregate(
        [
            {"$match": {"category id": category_id}},
            {"$group": {"_id": "$draw type", "max round": {"$max": "$round"}}},
        ]
    )
    category_players_1 = db.aft_tournament_draws.distinct(
        "player 1 id", {"category id": category_id, "player 1 id": {"$ne": ""}}
    )
    category_players_2 = db.aft_tournament_draws.distinct(
        "player 2 id", {"category id": category_id, "player 2 id": {"$ne": ""}}
    )
    category_players_count = len(set(category_players_1 + category_players_2))
    draw_rounds = {draw_round["_id"]: draw_round["max round"] for draw_round in rounds}
    reverse_round = max_reverse_round = sum(draw_rounds.values())
    reverse_rounds = dict()
    for draw_type in [
        round_type for round_type in "EPQF" if round_type in draw_rounds.keys()
    ]:
        reverse_rounds[draw_type] = dict()
        for round_index in range(1, draw_rounds[draw_type] + 1):
            reverse_rounds[draw_type][round_index] = reverse_round
            reverse_round -= 1
    for draw_type in [
        round_type for round_type in "EPQF" if round_type in draw_rounds.keys()
    ]:
        category_matches = db.aft_tournament_draws.find(
            {
                "$or": [{"player 1 id": player_id}, {"player 2 id": player_id}],
                "category id": category_id,
                "draw type": draw_type,
                "players count": category_players_count,
            }
        )
        category_matches.sort([("round", pymongo.ASCENDING)])
        for match in category_matches:
            match_details = {
                "_id": match["_id"],
                "round": reverse_rounds[draw_type][match["round"]],
                "category id": match["category id"],
                "category name": match["category name"],
            }
            if player_id == match["player 1 id"]:
                match_details.update({"victory": match["winner"] == 1})
                opponent_id = match["player 2 id"].strip()
                opponent_name = match["player 2 name"].strip()
            else:
                match_details.update({"victory": match["winner"] == 2})
                opponent_id = match["player 1 id"]
                opponent_name = match["player 1 name"]
            if opponent_name == "Bye":
                opponent_ranking = None
            else:
                opponent = db.players.find_one({"_id": opponent_id})
                if opponent is None:
                    opponent_ranking = None
                    logging.warning(
                        "Could not find the opponent {} ({}) in the match {}"
                        "".format(opponent_name, opponent_id, match["_id"])
                    )
                elif "classement_tennis" in opponent:
                    opponent_ranking = opponent["classement_tennis"]["2019"]["single"]
                elif "single ranking" in opponent["details"]:
                    opponent_ranking = opponent["details"]["single ranking"]
                else:
                    opponent_ranking = opponent["single_ranking"]
            match_details.update(
                {
                    "opponent id": opponent_id,
                    "opponent points": SINGLE_RANKING_POINTS[opponent_ranking]
                    if opponent_ranking is not None
                    else 0,
                }
            )
            category_details["matches"].append(match_details)
        matches = category_details["matches"]
        if len(matches) == 0:
            return category_details
        if len(matches) == 1 and matches[0]["round"] == max_reverse_round:
            return category_details
        for match in category_details["matches"]:
            category_details["participation"] += 2
            category_details["victory"] += match["opponent points"]
            category_details["stage"] = get_stage_for_round(
                match["round"], match["category name"]
            )

    return category_details


def get_stage_for_round(round, category_name):
    return 0


def compute_tournament_points(db, player, year):
    player_id = player["_id"]
    tournament_points = dict(total=0, details=dict())
    categories = db.aft_tournament_draws.distinct(
        "category id",
        filter={
            "$or": [{"player 1 id": player_id}, {"player 2 id": player_id}],
            "category name": re.compile("^S[DM].*"),
        },
    )
    for category_id in categories:
        category_details = get_draw_details(db, player_id, category_id)


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
                "$currentDate": {"ranking.points.last_updated": True},
                "$set": {"ranking.points.{}.single".format(year): points},
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

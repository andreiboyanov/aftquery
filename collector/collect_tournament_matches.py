import sys
import argparse
from datetime import datetime
import pymongo
from aftquery.parser.aft import tournament as aft_tournament

import traceback
import logging

logging.basicConfig(
    filename="logs/{}_collect_tournament_matches.log".format(datetime.now()),
    level=logging.DEBUG,
)


def print_tournament(tournament, index, count, skip=False):
    print(
        "{}/{}".format(index, count),
        tournament["_id"],
        tournament["name"],
        tournament["date"],
        "...skipping" if skip else "",
    )


def process_tournament_matches(db, tournament, update_only, index, tournaments_count):
    tournament_id = tournament["_id"]
    if (update_only and db.aft_matches.count_documents({"tournament id": tournament["_id"]}) > 0):
        print_tournament(tournament, index, tournaments_count, skip=True)
        return
    print_tournament(tournament, index, tournaments_count)
    db.aft_matches.delete_many({"tournament id": tournament_id})
    matches = aft_tournament.get_tournament_matches(tournament_id)
    if matches:
        print("Adding {} matches to the database".format(len(matches)))
        db.aft_matches.insert_many(matches)


def process_tournament_draws(db, tournament, update_only, index, tournaments_count):
    tournament_id = tournament["_id"]
    if (update_only and db.aft_tournament_draws.count_documents({"tournament id": tournament["_id"]}) > 0):
        print_tournament(tournament, index, tournaments_count, skip=True)
        return
    print_tournament(tournament, index, tournaments_count)
    db.aft_tournament_draws.delete_many({"tournament id": tournament_id})
    matches = list(aft_tournament.get_tournament_draws(tournament_id))
    if matches:
        print("Adding {} matches to the database".format(len(matches)))
        db.aft_tournament_draws.insert_many(matches)


def main(arguments):
    client = pymongo.MongoClient()
    db = client.aft_collector

    if arguments.draws:
        process_tournament = process_tournament_draws
    else:
        process_tournament = process_tournament_matches

    if arguments.tournament_id:
        tournament = db.aft_tournaments.find_one({"_id": arguments.tournament_id})
        print_tournament(tournament, 1, 1)
        process_tournament(db, arguments.tournament_id)
        return

    all_tournaments = db.aft_tournaments.find({}, no_cursor_timeout=True)
    tournaments_count = all_tournaments.count()
    for index, tournament in enumerate(all_tournaments):
        try:
            process_tournament(db, tournament, arguments.update, index, tournaments_count)
        except Exception as error:
            print(
                "{} {} {} ==> {}".format(
                    tournament["_id"], tournament["name"], tournament["date"], error
                )
            )
            logging.error(
                "{} {} {} ==> {}".format(
                    tournament["_id"], tournament["name"], tournament["date"], error
                )
            )
            logging.debug(traceback.format_exc())
    all_tournaments.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        "Pull all matches for a given tournament or for all tournaments"
    )
    parser.add_argument(
        "-t", "--tournament-id", help="Get matches only for this tournament"
    )
    parser.add_argument(
        "-d", "--draws", action="store_true", help="Parse draws instead of tournament matches"
    )
    parser.add_argument(
        "-u",
        "--update",
        action="store_true",
        help="Skip tournaments that already have matches in the database.",
    )
    arguments = parser.parse_args(sys.argv[1:])
    main(arguments)

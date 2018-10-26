import sys
from datetime import datetime
import pymongo
from aftquery.parser.aft import tournament as aft_tournament

import traceback
import logging

logging.basicConfig(
    filename="logs/{}_collect_tournament_matches.log".format(datetime.now()),
    level=logging.DEBUG,
)


def add_tournament_matches(db, tournament_id):
    db.aft_matches.delete_many({"tournament id": tournament_id})
    matches = aft_tournament.get_tournament_matches(tournament_id)
    if matches:
        db.aft_matches.insert_many(matches)


def main(arguments):

    client = pymongo.MongoClient()
    db = client.aft_collector

    if len(arguments) > 0:
        add_tournament_matches(db, arguments[0])
    all_tournaments = db.aft_tournaments.find({}, no_cursor_timeout=True)
    for index, tournament in enumerate(all_tournaments):
        try:
            print(
                "{}/{}".format(index, all_tournaments.count()),
                tournament["_id"],
                tournament["name"],
                tournament["date"],
            )
            add_tournament_matches(db, tournament["_id"])
        except Exception as error:
            logging.error(
                "{} {} {} ==> {}".format(
                    tournament["_id"], tournament["name"], tournament["date"], error
                )
            )
            logging.debug(traceback.format_exc())
    all_tournaments.close()


if __name__ == "__main__":
    main(sys.argv[1:])

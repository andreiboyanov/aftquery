import sys
import pymongo
from aftquery.parser.aft import tournament as aft_tournament


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
    all_tournaments = db.aft_tournaments.find()
    for index, tournament in enumerate(all_tournaments):
        print(
            "{}/{}".format(index, all_tournaments.count()),
            tournament["_id"],
            tournament["name"],
            tournament["date"],
        )
        add_tournament_matches(db, tournament["_id"])


if __name__ == "__main__":
    main(sys.argv[1:])

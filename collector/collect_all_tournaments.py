import sys
import argparse
import pymongo
from aftquery.parser.aft import tournament


def main(arguments):
    client = pymongo.MongoClient()
    db = client.aft_collector
    if arguments.categories:
        db.aft_categories.remove({})
        categories = tournament.get_all_categories()
        db.aft_categories.insert_many(categories)

    for tour in tournament.get_tournaments_for_current_year():
        print(tour["_id"], tour["name"], tour["date"])
        db.aft_tournaments.find_and_modify(
            query={"_id": tour["_id"]},
            update={
                "$currentDate": {"last_updated": True},
                "$set": tour,
            },
            upsert=True,
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Pull all tournaments for the current year from aftnet.be")
    parser.add_argument("-c", "--categories", help="Pull also all tournament categories")
    arguments = parser.parse_args(sys.argv[1:])
    main(arguments)

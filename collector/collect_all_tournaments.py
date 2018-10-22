import sys
import pymongo
from aftquery.parser.aft import tournament


def main(arguments):

    client = pymongo.MongoClient()
    db = client.aft_collector
    # db.aft_categories.remove({})
    # categories = tournament.get_all_categories()
    # db.aft_categories.insert_many(categories)

    for tour in tournament.get_tournaments_for_current_year():
        db.aft_tournaments.find_and_modify(
            query={"_id": tour["_id"]},
            update={
                "$currentDate": {"last_updated": True},
                "$set": tour,
            },
            upsert=True,
        )


if __name__ == "__main__":
    main(sys.argv[1:])

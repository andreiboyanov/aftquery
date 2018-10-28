import sys
import pymongo
from aftquery.parser.aft import clubs as aft_clubs


def main(arguments):
    client = pymongo.MongoClient()
    db = client.aft_collector
    for region in [1, 3, 4, 6]:
        for club in aft_clubs.search_clubs(region=region):
            club_id = club["id"]
            db.clubs.find_and_modify(
                query={"_id": club_id},
                update={
                    "$currentDate": {"last_updated": True},
                    "$set": {
                        "_id": club_id,
                        "name": club["name"],
                        "region": region,
                    },
                },
                upsert=True,
            )


if __name__ == "__main__":
    main(sys.argv[1:])

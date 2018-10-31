import sys
import pymongo
from aftquery.parser.aft import players as aft_players


def main(arguments):
    client = pymongo.MongoClient()
    db = client.aft_collector
    all_players = db.players.find({'details': {'$exists': False}}, no_cursor_timeout=True)
    count = all_players.count()
    for index, player in enumerate(all_players):
        player_id = player["_id"]
        print("{}/{}".format(index, count), player_id, player["name"])
        player_details = aft_players.get_player_details(player_id=player_id)
        db.players.find_and_modify(
            query={"_id": player_id},
            update={
                "$currentDate": {"last_updated_details": True},
                "$set": {
                    "details": player_details,
                },
            },
            upsert=False,
        )
    all_players.close()


if __name__ == "__main__":
    main(sys.argv[1:])


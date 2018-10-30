import sys
import pymongo
from aftquery.parser.aft import players as aft_players


def main(arguments):
    client = pymongo.MongoClient()
    db = client.aft_collector
    for club in db.clubs.find():
        club_id = club["_id"]
        print(club_id, club["name"])
        for players_chunk in aft_players.search_players(
            club_id=club_id, region=club["region"]
        ):
            for player_id, player in players_chunk.items():
                print(club_id, player_id, player["name"])
                db.players.find_and_modify(
                    query={"_id": player_id},
                    update={
                        "$currentDate": {"last_updated": True},
                        "$set": {
                            "_id": player_id,
                            "name": player["name"],
                            "club_id": player["club_id"],
                            "club_name": player["club_name"],
                            "single_ranking": player["single_ranking"],
                            "double_points": player["double_ranking"],
                        },
                    },
                    upsert=True,
                )


if __name__ == "__main__":
    main(sys.argv[1:])

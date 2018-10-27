import sys
import pymongo


def main(arguments):
    client = pymongo.MongoClient()
    db = client.aft_collector

    all_players = db.players.find({}, no_cursor_timeout=True)
    for player in all_players:
        player_matches = [
            match
            for match in player["matches"]["2018"]["single"]
            if match["tournament type"] == "tournament"
            and match["text score"] is not None
        ]
        aft_matches_cursor = db.aft_matches.find(
            {"$or": [{"player 1 id": player["_id"]}, {"player 2 id": player["_id"]}]}
        )
        aft_matches = [match for match in aft_matches_cursor]
        tournaments_from_player = set(
            [match["tournament id"] for match in player_matches]
        )
        tournaments_from_aft_matches = set(
            [match["tournament id"] for match in aft_matches]
        )
        if len(tournaments_from_player) != len(tournaments_from_aft_matches):
            print(
                "Player {} - {} has inconsistency in the tournaments number ({} != {})".format(
                    player["_id"],
                    player["name"],
                    len(tournaments_from_player),
                    len(tournaments_from_aft_matches),
                )
            )
        if len(player_matches) != len(aft_matches):
            print(
                "Player {} - {} has inconsistency in the number of matches ({} != {})".format(
                    player["_id"], player["name"], len(player_matches), len(aft_matches)
                )
            )
    all_players.close()


if __name__ == "__main__":
    main(sys.argv[1:])

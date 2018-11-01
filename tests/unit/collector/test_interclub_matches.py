from aftquery.collector.extract_interclub_matches_from_players import (
    create_double_interclub_match,
    create_single_interclub_match,
)


def test_create_double_interclub_match(sousmarin_db):
    player = sousmarin_db.players.find_one({"_id": "1086664"})
    for match in player["matches"]["2018"]["double"]:
        if match["tournament type"] == "interclub":
            interclub_match = create_double_interclub_match(sousmarin_db, player, "2018", match)
            assert len(interclub_match["_id"]) >= 21
            assert interclub_match["interclub meeting id"] == match["interclub meeting id"]
            assert interclub_match["score"] == match["score"]
            assert interclub_match["opponents team"] == match["tournament name"]


def test_create_single_interclub_match(sousmarin_db):
    player = sousmarin_db.players.find_one({"_id": "1095130"})
    for match in player["matches"]["2018"]["single"]:
        if match["tournament type"] == "interclub":
            interclub_match = create_single_interclub_match(sousmarin_db, player, "2018", match)
            assert len(interclub_match["_id"]) >= 22
            assert interclub_match["interclub meeting id"] == match["interclub meeting id"]
            assert interclub_match["score"] == match["score"]
            assert interclub_match["opponents team"] == match["tournament name"]

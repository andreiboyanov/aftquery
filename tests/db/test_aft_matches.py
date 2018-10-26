def test_player_matches_compare_to_aft_matches(sousmarin_db):
    tested_player_id = "1095130"
    player = sousmarin_db.players.find_one(
        {"_id": tested_player_id}, {"matches.2018.single": True}
    )
    player_matches = [
        match
        for match in player["matches"]["2018"]["single"]
        if match["tournament type"] == "tournament"
    ]
    aft_matches = sousmarin_db.aft_matches.find(
        {"$or": [{"player 1 id": tested_player_id}, {"player 2 id": tested_player_id}]}
    )
    tournaments_from_player = set([match["tournament id"] for match in player_matches])
    tournaments_from_aft_matches = set(
        [match["tournament id"] for match in aft_matches]
    )
    missing_tournaments_in_aft_matches = (
        tournaments_from_player - tournaments_from_aft_matches
    )
    matches_from_missing_tournaments = [
        match
        for match in player_matches
        if match["tournament id"] in missing_tournaments_in_aft_matches
    ]
    assert len(tournaments_from_player) == len(tournaments_from_aft_matches)
    assert len(player_matches) == len(list(aft_matches))

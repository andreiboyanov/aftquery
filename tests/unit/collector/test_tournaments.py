from aftquery.collector.collect_tournament_matches import (
    process_tournament_matches,
    process_tournament_draws,
)


# def test_process_tournament_matches(sousmarin_db):
#     process_tournament_matches(sousmarin_db, "313277", False, 1, 1)
#     assert sousmarin_db.aft_matches.count_documents({"tournament id": "313277"}) == 16


def test_process_tournament_draws(sousmarin_db):
    tournament = sousmarin_db.aft_tournaments.find_one({"_id": "313669"})
    process_tournament_draws(sousmarin_db, tournament, False, 1, 1)
    assert sousmarin_db.aft_tournament_draws.count_documents({"tournament id": "313669"}) == 238


def test_process_tournament_draws_check_winner_parsing(sousmarin_db):
    tournament = sousmarin_db.aft_tournaments.find_one({"_id": "313227"})
    process_tournament_draws(sousmarin_db, tournament, False, 1, 1)
    match = sousmarin_db.aft_tournament_draws.find_one({
        "tournament id": "313227",
        "category id": "594346",
        "draw type": "Q",
        "round": 2,
        "player 1 id": "3000848"
    })
    assert match["score"] == [[6, 2], [6, 1]]
    assert match["winner"] == 1

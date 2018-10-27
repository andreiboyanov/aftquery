from aftquery.collector.collect_tournament_matches import (
    process_tournament_matches,
    process_tournament_draws,
)


def test_process_tournament_matches(sousmarin_db):
    process_tournament_matches(sousmarin_db, "313277")
    assert sousmarin_db.aft_matches.count_documents({"tournament id": "313277"}) == 16


def test_process_tournament_draws(sousmarin_db):
    process_tournament_draws(sousmarin_db, "313669")
    assert sousmarin_db.aft_tournament_draws.count_documents({"tournament id": "313669"}) == 238

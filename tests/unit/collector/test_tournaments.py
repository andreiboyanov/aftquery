from aftquery.collector.collect_tournament_matches import add_tournament_matches


def test_add_tournament_matches(sousmarin_db):
    add_tournament_matches(sousmarin_db, "313277")
    assert sousmarin_db.aft_matches.count_documents({"tournament id": "313277"}) == 16

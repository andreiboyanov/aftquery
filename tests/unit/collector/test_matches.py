from datetime import datetime
from aftquery.collector.update_player_matches import pull_player_matches


def test_pull_player_matches(sousmarin_db):
    current_year = datetime.now().year
    pull_player_matches(sousmarin_db, "1095130", current_year)
    assert sousmarin_db.players.count_documents({"_id": "1095130", "matches": {"$exists": True}}) > 0

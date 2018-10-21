from datetime import datetime
from aftquery.collector.update_player_matches import pull_player_matches


def test_pull_player_matches(sousmarin_db):
    current_year = datetime.now().year
    pull_player_matches(sousmarin_db, "1095130", current_year)
    assert sousmarin_db.matches.count_documents({"player_id": "1095130", "year": current_year}) > 0
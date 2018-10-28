from aftquery.collector.get_ranking_prediction import set_player_ranking


def test_set_player_ranking(sousmarin_db):
    player = sousmarin_db.players.find({"_id": "1095130"})[0]
    set_player_ranking(sousmarin_db, player, 2019)
    player = sousmarin_db.players.find({"_id": "1095130"})[0]
    assert player["ranking"]["2019"]["single"] == "C30.4"
    player = sousmarin_db.players.find({"_id": "1000250"})[0]
    set_player_ranking(sousmarin_db, player, 2019)
    player = sousmarin_db.players.find({"_id": "1000250"})[0]
    assert player["ranking"]["2019"]["single"] == "C30.3"

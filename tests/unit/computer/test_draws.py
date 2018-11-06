from aftquery.computer.compute_points import compute_tournament_points


def test_compute_tournament_points(sousmarin_db):
    player = sousmarin_db.players.find_one({"_id": "3000848"})
    points = compute_tournament_points(sousmarin_db, player, 2018)
    assert isinstance(points, dict)

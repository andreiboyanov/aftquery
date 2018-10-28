from aftquery.parser.classement_tennis.ranking import get_ranking_prevision


def test_get_ranking_prevision():
    player_id = "1095130"
    new_ranking = get_ranking_prevision(player_id, "Andrei", "BOYANOV")
    assert new_ranking == "C30.4"

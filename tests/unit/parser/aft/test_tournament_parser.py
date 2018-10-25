from aftquery.parser.aft.tournament import get_all_categories, get_tournaments_for_current_year, get_tournament_matches


def test_get_all_categories():
    categories = list(get_all_categories())
    assert len(categories) > 55


def test_get_tournaments_for_current_year():
    tournaments = list(get_tournaments_for_current_year())
    assert len(tournaments) > 55
    for tournament in tournaments:
        assert int(tournament["_id"]) > 0


def test_get_tournament_matches():
    matches = get_tournament_matches("313277")
    assert isinstance(matches, list)
    assert len(matches) == 16
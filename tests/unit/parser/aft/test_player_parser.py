from aftquery.parser.aft import players


def test_get_player_details():
    andrei = players.get_player_details("1095130")
    assert isinstance(andrei, dict)
    assert andrei["name"] == "BOYANOV Andrei"
    assert andrei["id"] == "1095130"
    assert andrei["image"].startswith("data:")
    assert andrei["nationality"] == "BULGARIE (BG)"
    assert andrei["sex"] == "male"
    assert andrei["club"] == "BRUSSELS (1008)"
    for key in ['single ranking', 'double points', 'first affiliation', 'active from', ]:
        assert key in andrei


def test_get_player_matches():
    for player_id in ["1087460", "1095130", "6048420"]:
        single_matches, double_matches = players.get_player_matches(player_id)
        assert isinstance(single_matches, list)
        assert isinstance(double_matches, list)
        for match in double_matches:
            assert match["partner id"] is not None
            assert match["opponent 1 id"] != match["opponent 2 id"]
            assert match["tournament type"] in ["tournament", "interclub"]
            if match["tournament type"] == "tournament":
                assert len(match["tournament id"]) == 6
            else:
                assert len(match["interclub meeting id"]) == 6

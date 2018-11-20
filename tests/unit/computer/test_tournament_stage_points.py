from aftquery.computer.aft_rules.tournament_stage_points import (
    BELGIAN_CIRCUIT_DAMES,
    BELGIAN_CIRCUIT_MONSIEURS,
    DAMES,
    DAMES_25,
    DAMES_35,
    DAMES_45,
    MONSIEURS,
    MONSIEURS_35,
    MONSIEURS_45,
    MONSIEURS_55,
)


def test_tournament_points_verify_acsending_order():
    for main_category in (
        BELGIAN_CIRCUIT_DAMES,
        BELGIAN_CIRCUIT_MONSIEURS,
        DAMES,
        DAMES_25,
        DAMES_35,
        DAMES_45,
        MONSIEURS,
        MONSIEURS_35,
        MONSIEURS_45,
        MONSIEURS_55,
    ):
        last_points = -1
        for category in main_category.values():
            limits = category[0]
            assert (limits[0] == -1 and limits[1]) or limits[1] == -1 or limits[0] < limits[1]
            for points in category[1]:
                assert points > last_points

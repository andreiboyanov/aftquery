import json


def test_get_club_by_id(sousmarin):
    response = sousmarin.get("/club/1008")
    club = json.loads(response.data)
    assert response.status_code == 200
    assert club["_id"] == "1008"
    assert club["name"] == "BRUSSELS"

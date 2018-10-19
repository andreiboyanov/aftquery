import json


def test_get_club_by_id(sousmarin):
    response = sousmarin.get("/club/1008")
    assert response.status_code == 200
    club = json.loads(response.data.decode("utf-8"))
    assert club["_id"] == "1008"
    assert club["name"] == "BRUSSELS"

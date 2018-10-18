import json


def test_get_user_by_id(sousmarin):
    response = sousmarin.get("/player/1095130")
    assert response.status_code == 200
    player = json.loads(response.data)
    assert player["_id"] == "1095130"
    assert player["name"] == "BOYANOV Andrei"
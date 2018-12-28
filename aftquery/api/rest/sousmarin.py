from flask import Flask, jsonify
from flask_pymongo import PyMongo


app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://localhost:27017/aft_collector"
mongo = PyMongo(app)


@app.route("/player/<player_id>", methods=['GET'])
def get_player(player_id):
    players = mongo.db.players
    player = players.find_one({'_id': player_id})
    return jsonify(player)


@app.route("/club/<club_id>", methods=['GET'])
def get_club(club_id):
    clubs = mongo.db.clubs
    club = clubs.find_one({'_id': club_id})
    return jsonify(club)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7777)


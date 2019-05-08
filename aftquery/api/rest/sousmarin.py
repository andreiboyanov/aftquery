from flask import Flask, jsonify
from flask_pymongo import PyMongo
from flask_restplus import Resource, Api


app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://localhost:27017/aft_collector"
mongo = PyMongo(app)
api = Api(app)


@api.route("/player/<string:player_id>")
class Player(Resource):
    def get(self, player_id):
        players = mongo.db.players
        player = players.find_one({'_id': player_id})
        return jsonify(player)


@api.route("/club/<string:club_id>")
class Club(Resource):
    def get(self, club_id):
        clubs = mongo.db.clubs
        club = clubs.find_one({'_id': club_id})
        return jsonify(club)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7777, debug=True)

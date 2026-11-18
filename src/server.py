"""
server.py - Flask back end for the Car Workshop Service Log.

The Tkinter window sends HTTP requests here.
Flask checks the values, uses CarDB (SQLite) and replies with JSON.
Run it first:  python src/server.py
"""

import sqlite3

from flask import Flask, jsonify

from database import CarDB


app = Flask(__name__)
db = CarDB()
db.createTable()  # create the table at start-up if it is missing


@app.route("/cars", methods=["GET"])
def listCars():
    """JSON route: return all saved cars (used by the window and report.py)."""
    try:
        cars = db.getAll()
    except sqlite3.Error:
        return jsonify({"error": "Database error"}), 500
    return jsonify({"cars": cars})


@app.route("/cars/<int:car_id>", methods=["GET"])
def getCar(car_id):
    """Return one car, or 404 if the ID is unknown."""
    try:
        car = db.getOne(car_id)
    except sqlite3.Error:
        return jsonify({"error": "Database error"}), 500
    if car is None:
        return jsonify({"error": "Car not found"}), 404
    return jsonify(car)


if __name__ == "__main__":
    app.run(port=5050)

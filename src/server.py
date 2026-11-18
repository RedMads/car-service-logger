"""
server.py - Flask back end for the Car Workshop Service Log.

The Tkinter window sends HTTP requests here.
Flask checks the values, uses CarDB (SQLite) and replies with JSON.
Run it first:  python src/server.py
"""

import sqlite3

from flask import Flask, jsonify, request

from database import CarDB


app = Flask(__name__)
db = CarDB()
db.createTable()  # create the table at start-up if it is missing

# Allowed choices (the window shows the same lists)
SERVICES = ["Oil change", "Brakes", "Tires", "AC", "Engine", "Other"]
STATUSES = ["Waiting", "Done"]
MAX_COST = 100000

# Friendly names used in error messages
FIELD_LABELS = {
    "car_name": "Car name",
    "owner": "Owner",
    "service": "Service",
    "cost": "Cost",
    "status": "Status",
}


def checkCarForm(form):
    """Check the form values sent by the window.

    Returns (data, None) if everything is valid,
    or (None, error_message) if something is wrong.
    """
    # 1. Read every field and remove extra spaces
    data = {
        "car_name": form.get("car_name", "").strip(),
        "owner": form.get("owner", "").strip(),
        "service": form.get("service", "").strip(),
        "cost": form.get("cost", "").strip(),
        "status": form.get("status", "").strip(),
    }

    # 2. No field may be empty
    for field_name, value in data.items():
        if value == "":
            return None, f"{FIELD_LABELS[field_name]} is required"

    # 3. Cost must be a number between 0 and MAX_COST
    try:
        data["cost"] = float(data["cost"])
    except ValueError:
        return None, "Cost must be a number"
    if data["cost"] < 0 or data["cost"] > MAX_COST:
        return None, f"Cost must be between 0 and {MAX_COST}"

    # 4. Service and status must be one of the allowed choices
    if data["service"] not in SERVICES:
        return None, "Unknown service"
    if data["status"] not in STATUSES:
        return None, "Status must be Waiting or Done"

    return data, None


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


@app.route("/cars/add", methods=["POST"])
def addCar():
    """Check the values, then save a new car."""
    data, error = checkCarForm(request.form)
    if error:
        return jsonify({"error": error}), 400
    try:
        db.add(data["car_name"], data["owner"], data["service"],
               data["cost"], data["status"])
    except sqlite3.Error:
        return jsonify({"error": "Database error"}), 500
    return jsonify({"message": "Car added"}), 201


@app.route("/cars/<int:car_id>/edit", methods=["POST"])
def editCar(car_id):
    """Check the values, then change one car (404 if the ID is unknown)."""
    data, error = checkCarForm(request.form)
    if error:
        return jsonify({"error": error}), 400
    try:
        found = db.edit(car_id, data["car_name"], data["owner"],
                        data["service"], data["cost"], data["status"])
    except sqlite3.Error:
        return jsonify({"error": "Database error"}), 500
    if not found:
        return jsonify({"error": "Car not found"}), 404
    return jsonify({"message": "Car updated"})


@app.route("/cars/<int:car_id>/delete", methods=["POST"])
def deleteCar(car_id):
    """Delete one car (404 if the ID is unknown)."""
    try:
        found = db.delete(car_id)
    except sqlite3.Error:
        return jsonify({"error": "Database error"}), 500
    if not found:
        return jsonify({"error": "Car not found"}), 404
    return jsonify({"message": "Car deleted"})


if __name__ == "__main__":
    app.run(port=5050)

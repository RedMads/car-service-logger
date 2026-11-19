"""
server.py - Flask back end for the Car Workshop Service Log.

The Tkinter window sends HTTP requests here.
Flask checks the values, uses CarDB (SQLite) and replies with JSON.
Run it first:  python src/server.py
"""

import re
import sqlite3

from flask import Flask, jsonify, request

from database import CarDB


app = Flask(__name__)
db = CarDB()
db.createTable()  # create the table at start-up if it is missing

# Allowed status choices (the window shows the same list).
# Service is free text: the window offers a list, and "Other" lets the user type one.
STATUSES = ["Waiting", "Done"]
MAX_SERVICE_LENGTH = 40
MAX_COST = 100000
MAX_ODOMETER = 2000000  # km

# Saudi plate: 1 to 4 numbers, a space, then 3 English letters, like "1234 ABC".
# The space is optional when typing; the server always saves it with one space.
PLATE_PATTERN = re.compile(r"^([1-9][0-9]{0,3}) ?([A-Z]{3})$")

# Friendly names used in error messages
FIELD_LABELS = {
    "car_name": "Car name",
    "plate": "Plate",
    "odometer": "Odometer",
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
        "plate": form.get("plate", "").strip().upper(),
        # Commas are allowed when typing, like "120,000"
        "odometer": form.get("odometer", "").strip().replace(",", ""),
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

    # 4. Plate must look like "1234 ABC" (saved in this exact form)
    match = PLATE_PATTERN.match(data["plate"])
    if match is None:
        return None, "Plate must be 1-4 numbers then 3 letters, like 1234 ABC"
    data["plate"] = f"{match.group(1)} {match.group(2)}"

    # 5. Odometer must be a whole number of km between 0 and MAX_ODOMETER
    try:
        data["odometer"] = int(data["odometer"])
    except ValueError:
        return None, "Odometer must be a whole number (km)"
    if data["odometer"] < 0 or data["odometer"] > MAX_ODOMETER:
        return None, f"Odometer must be between 0 and {MAX_ODOMETER} km"

    # 6. Service can be typed by the user, so only limit its length
    if len(data["service"]) > MAX_SERVICE_LENGTH:
        return None, f"Service must be {MAX_SERVICE_LENGTH} characters or less"

    # 7. Status must be one of the allowed choices
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
        db.add(data["car_name"], data["plate"], data["odometer"], data["owner"],
               data["service"], data["cost"], data["status"])
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
        found = db.edit(car_id, data["car_name"], data["plate"], data["odometer"],
                        data["owner"], data["service"], data["cost"], data["status"])
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


@app.route("/total", methods=["GET"])
def getTotal():
    """Extra feature: total cost of all services."""
    try:
        total = db.totalCost()
    except sqlite3.Error:
        return jsonify({"error": "Database error"}), 500
    return jsonify({"total": total})


@app.route("/stats", methods=["GET"])
def getStats():
    """Extra feature: numbers and chart data for the Statistics window."""
    try:
        stats = db.getStats()
    except sqlite3.Error:
        return jsonify({"error": "Database error"}), 500
    return jsonify(stats)


if __name__ == "__main__":
    app.run(port=5050)

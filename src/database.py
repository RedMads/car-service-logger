"""
database.py - All SQLite work for the Car Workshop Service Log.

The class CarDB holds every SQL query of the project.
Every method opens its own connection, does one job, and closes it.
"""

import os
import sqlite3
from datetime import date


# The database file lives next to this script, so it is always the same file
# no matter which folder the program is started from.
DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cars.db")


class CarDB:
    """Adds, reads, edits and deletes car records in SQLite."""

    def __init__(self, db_file=DB_FILE):
        # Remember which file to use
        self.db_file = db_file

    def connect(self):
        """Open a new connection. Rows can be read like dicts."""
        connection = sqlite3.connect(self.db_file)
        connection.row_factory = sqlite3.Row
        return connection

    def createTable(self):
        """Create the cars table only if it is missing (keeps old records)."""
        connection = self.connect()
        try:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS cars (
                    id       INTEGER PRIMARY KEY AUTOINCREMENT,
                    car_name TEXT NOT NULL,
                    plate    TEXT NOT NULL DEFAULT '',
                    odometer  INTEGER NOT NULL DEFAULT 0,
                    owner    TEXT NOT NULL,
                    service  TEXT NOT NULL,
                    cost     REAL NOT NULL,
                    status   TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT ''
                )
            """)

            # Older databases were made before the plate and odometer columns
            # existed, so add them (old cars get an empty plate and 0 km)
            columns = []
            for row in connection.execute("PRAGMA table_info(cars)").fetchall():
                columns.append(row["name"])

            if "mileage" in columns and "odometer" not in columns:
                # The odometer column used to be called mileage: rename it, keep the values
                connection.execute("ALTER TABLE cars RENAME COLUMN mileage TO odometer")
                columns.append("odometer")
            if "plate" not in columns:
                connection.execute(
                    "ALTER TABLE cars ADD COLUMN plate TEXT NOT NULL DEFAULT ''"
                )
            if "odometer" not in columns:
                connection.execute(
                    "ALTER TABLE cars ADD COLUMN odometer INTEGER NOT NULL DEFAULT 0"
                )
            if "created_at" not in columns:
                connection.execute(
                    "ALTER TABLE cars ADD COLUMN created_at TEXT NOT NULL DEFAULT ''"
                )
                # Cars saved before dates existed get today's date
                connection.execute(
                    "UPDATE cars SET created_at = ? WHERE created_at = ''",
                    (date.today().isoformat(),),
                )
            connection.commit()
        finally:
            # Always close the connection, even if an error happened
            connection.close()

    def getAll(self):
        """Return every car as a list of dicts (empty list if none)."""
        connection = self.connect()
        try:
            rows = connection.execute("SELECT * FROM cars ORDER BY id").fetchall()
            cars = []
            for row in rows:
                cars.append(dict(row))
            return cars
        finally:
            connection.close()

    def getOne(self, car_id):
        """Return one car as a dict, or None if the ID does not exist."""
        connection = self.connect()
        try:
            row = connection.execute(
                "SELECT * FROM cars WHERE id = ?", (car_id,)
            ).fetchone()
            if row is None:
                return None
            return dict(row)
        finally:
            connection.close()

    def add(self, car_name, plate, odometer, owner, service, cost, status):
        """Insert a new car record."""
        connection = self.connect()
        try:
            connection.execute(
                "INSERT INTO cars (car_name, plate, odometer, owner, service, cost, status, "
                "created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (car_name, plate, odometer, owner, service, cost, status,
                 date.today().isoformat()),  # the day the car was added, like 2026-11-20
            )
            connection.commit()
        finally:
            connection.close()

    def edit(self, car_id, car_name, plate, odometer, owner, service, cost, status):
        """Change one car. Return True if found, False if the ID is unknown."""
        connection = self.connect()
        try:
            cursor = connection.execute(
                "UPDATE cars SET car_name = ?, plate = ?, odometer = ?, owner = ?, "
                "service = ?, cost = ?, status = ? WHERE id = ?",
                (car_name, plate, odometer, owner, service, cost, status, car_id),
            )
            connection.commit()
            # rowcount is 0 when no row had this ID
            return cursor.rowcount > 0
        finally:
            connection.close()

    def delete(self, car_id):
        """Remove one car. Return True if found, False if the ID is unknown."""
        connection = self.connect()
        try:
            cursor = connection.execute("DELETE FROM cars WHERE id = ?", (car_id,))
            connection.commit()
            return cursor.rowcount > 0
        finally:
            connection.close()

    def totalCost(self):
        """Extra feature: the sum of all costs (0 if there are no cars)."""
        connection = self.connect()
        try:
            row = connection.execute("SELECT SUM(cost) AS total FROM cars").fetchone()
            # SUM gives NULL (None) for an empty table, so use 0 instead
            if row["total"] is None:
                return 0
            return row["total"]
        finally:
            connection.close()

    def getStats(self):
        """Extra feature: the summary numbers and chart data for the Statistics window."""
        connection = self.connect()
        try:
            # COALESCE turns NULL (empty table) into 0.
            # NULLIF(odometer, 0) skips cars with no odometer reading in the average.
            summary = connection.execute("""
                SELECT COUNT(*)                              AS cars,
                       COALESCE(SUM(status = 'Waiting'), 0)  AS waiting,
                       COALESCE(SUM(status = 'Done'), 0)     AS done,
                       COALESCE(SUM(cost), 0)                AS total_cost,
                       COALESCE(AVG(cost), 0)                AS average_cost,
                       COALESCE(AVG(NULLIF(odometer, 0)), 0) AS average_odometer
                FROM cars
            """).fetchone()

            # The model is the car name. Grouping by LOWER(TRIM()) makes "Toyota " and
            # "toyota" one model; MIN(TRIM(car_name)) shows the capitalised spelling
            # (capital letters sort first), so "GMC Yukon" stays "GMC Yukon".
            cars_by_model = self.getPairs(connection, """
                SELECT MIN(TRIM(car_name)), COUNT(*)
                FROM cars GROUP BY LOWER(TRIM(car_name))
                ORDER BY COUNT(*) DESC, LOWER(TRIM(car_name)) LIMIT 10
            """)
            # Average odometer per model (cars with 0 km are skipped)
            odometer_by_model = self.getPairs(connection, """
                SELECT MIN(TRIM(car_name)), AVG(odometer)
                FROM cars WHERE odometer > 0 GROUP BY LOWER(TRIM(car_name))
                ORDER BY AVG(odometer) DESC, LOWER(TRIM(car_name)) LIMIT 10
            """)
            # How many cars got each service
            cars_by_service = self.getPairs(connection, """
                SELECT service, COUNT(*)
                FROM cars GROUP BY service ORDER BY COUNT(*) DESC, service
            """)
            # Newest 14 days, then turned back to oldest-first for the chart
            cost_by_day = self.getPairs(connection, """
                SELECT created_at, SUM(cost)
                FROM cars GROUP BY created_at ORDER BY created_at DESC LIMIT 14
            """)
            cost_by_day.reverse()

            return {
                "summary": dict(summary),
                "cars_by_model": cars_by_model,
                "odometer_by_model": odometer_by_model,
                "cars_by_service": cars_by_service,
                "cost_by_day": cost_by_day,
            }
        finally:
            connection.close()

    def getPairs(self, connection, sql):
        """Run a 2-column query and return [[label, value], ...]."""
        pairs = []
        for row in connection.execute(sql).fetchall():
            pairs.append([row[0], row[1]])
        return pairs

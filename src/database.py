"""
database.py - All SQLite work for the Car Workshop Service Log.

The class CarDB holds every SQL query of the project.
Every method opens its own connection, does one job, and closes it.
"""

import os
import sqlite3


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
                    owner    TEXT NOT NULL,
                    service  TEXT NOT NULL,
                    cost     REAL NOT NULL,
                    status   TEXT NOT NULL
                )
            """)
            connection.commit()
        finally:
            # Always close the connection, even if an error happened
            connection.close()

    def getAll(self):
        """Return every car as a list of dicts (empty list if none)."""
        connection = self.connect()
        try:
            rows = connection.execute("SELECT * FROM cars ORDER BY id").fetchall()
            return [dict(row) for row in rows]
        finally:
            connection.close()

    def getOne(self, car_id):
        """Return one car as a dict, or None if the ID does not exist."""
        connection = self.connect()
        try:
            row = connection.execute(
                "SELECT * FROM cars WHERE id = ?", (car_id,)
            ).fetchone()
            return dict(row) if row else None
        finally:
            connection.close()

    def add(self, car_name, owner, service, cost, status):
        """Insert a new car record."""
        connection = self.connect()
        try:
            connection.execute(
                "INSERT INTO cars (car_name, owner, service, cost, status) "
                "VALUES (?, ?, ?, ?, ?)",
                (car_name, owner, service, cost, status),
            )
            connection.commit()
        finally:
            connection.close()

    def edit(self, car_id, car_name, owner, service, cost, status):
        """Change one car. Return True if found, False if the ID is unknown."""
        connection = self.connect()
        try:
            cursor = connection.execute(
                "UPDATE cars SET car_name = ?, owner = ?, service = ?, "
                "cost = ?, status = ? WHERE id = ?",
                (car_name, owner, service, cost, status, car_id),
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
            return row["total"] or 0
        finally:
            connection.close()

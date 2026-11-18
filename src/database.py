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
        with self.connect() as connection:
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
        connection.close()

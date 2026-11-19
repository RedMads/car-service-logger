"""
report.py - Writes a text report of all saved cars using one thread.

Flask must be running first. Then run:  python src/report.py
The report is saved as report.txt next to this script.
"""

import json
import os
import socket
from threading import Thread
from urllib.error import HTTPError, URLError
from urllib.request import urlopen


CARS_URL = "http://127.0.0.1:5050/cars"
REPORT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "report.txt")


def getCars():
    """Ask Flask's JSON route for the cars.

    Returns (cars, None) on success or (None, error_message) on failure.
    """
    try:
        with urlopen(CARS_URL, timeout=5) as reply:
            data = json.loads(reply.read().decode("utf-8"))
            return data["cars"], None
    except HTTPError as error:
        error_data = json.loads(error.read().decode("utf-8"))
        return None, error_data.get("error", "Unknown server error")
    except URLError:
        return None, "Cannot connect to the server. Is Flask running?"
    except socket.timeout:
        return None, "The server took too long to reply."


def writeReport(cars, file_name, result):
    """Runs inside the thread: write the cars to a UTF-8 text file.

    result is a dict shared with the main thread.
    result["saved"] becomes True if the file was written, else False.
    """
    try:
        with open(file_name, "w", encoding="utf-8") as report_file:
            report_file.write("Car Workshop Report\n")
            report_file.write("===================\n")

            if len(cars) == 0:
                report_file.write("No cars saved.\n")
            else:
                total = 0
                for number, car in enumerate(cars, start=1):
                    report_file.write(
                        f"{number}. {car['car_name']} | {car['plate'] or '-'} | {car['mileage']:,} km | {car['owner']} | "
                        f"{car['service']} | {car['cost']:.2f} SAR | {car['status']}\n"
                    )
                    total += car["cost"]
                report_file.write(f"\nNumber of cars: {len(cars)}\n")
                report_file.write(f"Total cost: {total:.2f} SAR\n")

        result["saved"] = True
    except OSError:
        result["saved"] = False


def main():
    # 1. Get the records from Flask
    cars, error = getCars()
    if error:
        print(error)
        return

    # 2. Start one thread that writes the report
    result = {"saved": False}
    report_thread = Thread(target=writeReport, args=(cars, REPORT_FILE, result))
    report_thread.start()

    # 3. Wait for the thread to finish, then say if it worked
    report_thread.join()
    if result["saved"]:
        print(f"Report saved to {REPORT_FILE}")
    else:
        print("Could not save the report")


if __name__ == "__main__":
    main()

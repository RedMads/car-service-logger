"""
client.py - Tkinter window for the Car Workshop Service Log.

The window never touches the database.
It only sends HTTP requests to Flask and shows the JSON replies.
Start the server first, then run:  python src/client.py
"""

import json
import socket
import tkinter as tk
from tkinter import ttk
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen


SERVER = "http://127.0.0.1:5050"

# Same choices as the server
SERVICES = ["Oil change", "Brakes", "Tires", "AC", "Engine", "Other"]
STATUSES = ["Waiting", "Done"]


def sendRequest(path, values=None):
    """Send one request to Flask.

    GET if values is None, POST if values is a dict.
    Returns (data, None) on success or (None, error_message) on failure.
    """
    url = SERVER + path

    # POST needs the values as bytes; GET sends no body
    if values is not None:
        body = urlencode(values).encode("utf-8")
    else:
        body = None

    try:
        with urlopen(url, data=body, timeout=5) as reply:
            data = json.loads(reply.read().decode("utf-8"))
            return data, None
    except HTTPError as error:
        # Flask replied with 400/404/500: read its JSON error message
        error_data = json.loads(error.read().decode("utf-8"))
        return None, error_data.get("error", "Unknown server error")
    except URLError:
        return None, "Cannot connect to the server. Is Flask running?"
    except socket.timeout:
        return None, "The server took too long to reply."


class WorkshopApp:
    """The main window: inputs, buttons, table and messages."""

    def __init__(self, root):
        self.root = root
        self.root.title("Car Workshop Service Log")

        self.buildForm()
        self.buildTable()
        self.buildMessages()

        # Load the records as soon as the window opens
        self.loadCars()

    def buildForm(self):
        """Labels and input boxes at the top of the window."""
        form = ttk.Frame(self.root, padding=10)
        form.pack(fill="x")

        ttk.Label(form, text="Car name:").grid(row=0, column=0, sticky="w")
        self.car_name_entry = ttk.Entry(form, width=25)
        self.car_name_entry.grid(row=0, column=1, padx=5, pady=3)

        ttk.Label(form, text="Owner:").grid(row=0, column=2, sticky="w")
        self.owner_entry = ttk.Entry(form, width=25)
        self.owner_entry.grid(row=0, column=3, padx=5, pady=3)

        ttk.Label(form, text="Service:").grid(row=1, column=0, sticky="w")
        self.service_box = ttk.Combobox(form, values=SERVICES, state="readonly", width=22)
        self.service_box.grid(row=1, column=1, padx=5, pady=3)
        self.service_box.set(SERVICES[0])

        ttk.Label(form, text="Cost (SAR):").grid(row=1, column=2, sticky="w")
        self.cost_entry = ttk.Entry(form, width=25)
        self.cost_entry.grid(row=1, column=3, padx=5, pady=3)

        ttk.Label(form, text="Status:").grid(row=2, column=0, sticky="w")
        self.status_box = ttk.Combobox(form, values=STATUSES, state="readonly", width=22)
        self.status_box.grid(row=2, column=1, padx=5, pady=3)
        self.status_box.set(STATUSES[0])

    def buildTable(self):
        """The table (Treeview) that lists the saved cars."""
        columns = ("id", "car_name", "owner", "service", "cost", "status")
        headings = ("ID", "Car", "Owner", "Service", "Cost (SAR)", "Status")

        self.table = ttk.Treeview(self.root, columns=columns, show="headings", height=10)
        for column, heading in zip(columns, headings):
            self.table.heading(column, text=heading)
            self.table.column(column, width=110)
        self.table.column("id", width=40)
        self.table.pack(fill="both", expand=True, padx=10)

    def buildMessages(self):
        """A label at the bottom that shows success and error messages."""
        self.message_label = ttk.Label(self.root, text="", padding=10)
        self.message_label.pack(fill="x")

    def showMessage(self, text):
        """Show a short message at the bottom of the window."""
        self.message_label.config(text=text)

    def loadCars(self):
        """GET /cars and fill the table."""
        data, error = sendRequest("/cars")
        if error:
            self.showMessage(error)
            return

        # Remove the old rows, then add one row per car
        self.table.delete(*self.table.get_children())
        for car in data["cars"]:
            self.table.insert("", "end", values=(
                car["id"], car["car_name"], car["owner"],
                car["service"], f"{car['cost']:.2f}", car["status"],
            ))


if __name__ == "__main__":
    root = tk.Tk()
    WorkshopApp(root)
    root.mainloop()

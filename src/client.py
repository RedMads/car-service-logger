"""
client.py - Tkinter window for the Car Workshop Service Log.

The window never touches the database.
It only sends HTTP requests to Flask and shows the JSON replies.
Start the server first, then run:  python src/client.py
"""

import json
import socket
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
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

        # ID of the row the user clicked (None = nothing selected)
        self.selected_id = None

        self.buildForm()
        self.buildButtons()
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

        ttk.Label(form, text="Plate (1234 ABC):").grid(row=0, column=2, sticky="w")
        self.plate_entry = ttk.Entry(form, width=25)
        self.plate_entry.grid(row=0, column=3, padx=5, pady=3)

        ttk.Label(form, text="Owner:").grid(row=1, column=0, sticky="w")
        self.owner_entry = ttk.Entry(form, width=25)
        self.owner_entry.grid(row=1, column=1, padx=5, pady=3)

        ttk.Label(form, text="Service:").grid(row=1, column=2, sticky="w")
        self.service_box = ttk.Combobox(form, values=SERVICES, state="readonly", width=22)
        self.service_box.grid(row=1, column=3, padx=5, pady=3)
        self.service_box.set(SERVICES[0])
        # Remember the last good service, so Cancel in the "Other" popup can go back to it
        self.last_service = SERVICES[0]
        self.service_box.bind("<<ComboboxSelected>>", self.onServiceSelect)

        ttk.Label(form, text="Cost (SAR):").grid(row=2, column=0, sticky="w")
        self.cost_entry = ttk.Entry(form, width=25)
        self.cost_entry.grid(row=2, column=1, padx=5, pady=3)

        ttk.Label(form, text="Status:").grid(row=2, column=2, sticky="w")
        self.status_box = ttk.Combobox(form, values=STATUSES, state="readonly", width=22)
        self.status_box.grid(row=2, column=3, padx=5, pady=3)
        self.status_box.set(STATUSES[0])

    def buildButtons(self):
        """One row of action buttons."""
        buttons = ttk.Frame(self.root, padding=(10, 0))
        buttons.pack(fill="x")

        ttk.Button(buttons, text="Add", command=self.addCar).pack(side="left", padx=3)
        ttk.Button(buttons, text="Update", command=self.updateCar).pack(side="left", padx=3)
        ttk.Button(buttons, text="Delete", command=self.deleteCar).pack(side="left", padx=3)
        ttk.Button(buttons, text="Clear", command=self.clearForm).pack(side="left", padx=3)
        ttk.Button(buttons, text="Refresh", command=self.loadCars).pack(side="left", padx=3)

    def buildTable(self):
        """The table (Treeview) that lists the saved cars."""
        columns = ("id", "car_name", "plate", "owner", "service", "cost", "status")
        headings = ("ID", "Car", "Plate", "Owner", "Service", "Cost (SAR)", "Status")

        self.table = ttk.Treeview(self.root, columns=columns, show="headings", height=10)
        for column, heading in zip(columns, headings):
            self.table.heading(column, text=heading)
            self.table.column(column, width=110)
        self.table.column("id", width=40)
        self.table.pack(fill="both", expand=True, padx=10, pady=10)

        # When the user clicks a row, copy it into the inputs
        self.table.bind("<<TreeviewSelect>>", self.onSelect)

    def buildMessages(self):
        """Total cost label and a message label at the bottom."""
        self.total_label = ttk.Label(self.root, text="Total cost: 0.00 SAR",
                                     font=("TkDefaultFont", 11, "bold"), padding=(10, 0))
        self.total_label.pack(fill="x")

        self.message_label = ttk.Label(self.root, text="", padding=10)
        self.message_label.pack(fill="x")

    def showMessage(self, text):
        """Show a success message at the bottom of the window."""
        self.message_label.config(text=text, foreground="green")

    def showError(self, text):
        """Show an error at the bottom and in a popup box."""
        self.message_label.config(text=text, foreground="red")
        messagebox.showerror("Error", text)

    def checkSelected(self):
        """Return True if a car is selected, otherwise show an error."""
        if self.selected_id is None:
            self.showError("Please select a car first")
            return False
        return True

    def loadCars(self):
        """GET /cars and fill the table."""
        data, error = sendRequest("/cars")
        if error:
            self.showError(error)
            return

        # Remove the old rows, then add one row per car
        self.table.delete(*self.table.get_children())
        if len(data["cars"]) == 0:
            # Show a note inside the table (keeps the last message visible)
            self.table.insert("", "end", values=("", "No cars yet", "", "", "", "", ""))
        for car in data["cars"]:
            self.table.insert("", "end", values=(
                car["id"], car["car_name"], car["plate"], car["owner"],
                car["service"], f"{car['cost']:.2f}", car["status"],
            ))

        # The total changes whenever the list changes
        self.loadTotal()

    def loadTotal(self):
        """Extra feature: GET /total and show it under the table."""
        data, error = sendRequest("/total")
        if error:
            self.showError(error)
            return
        self.total_label.config(text=f"Total cost: {data['total']:.2f} SAR")


    def getFormValues(self):
        """Read the inputs into a dict (the server checks them)."""
        return {
            "car_name": self.car_name_entry.get(),
            "plate": self.plate_entry.get(),
            "owner": self.owner_entry.get(),
            "service": self.service_box.get(),
            "cost": self.cost_entry.get(),
            "status": self.status_box.get(),
        }

    def addCar(self):
        """POST /cars/add with the form values."""
        data, error = sendRequest("/cars/add", self.getFormValues())
        if error:
            self.showError(error)
            return
        self.showMessage(data["message"])
        self.clearForm()
        self.loadCars()

    def updateCar(self):
        """POST /cars/<id>/edit for the selected car."""
        if not self.checkSelected():
            return
        data, error = sendRequest(f"/cars/{self.selected_id}/edit", self.getFormValues())
        if error:
            self.showError(error)
            if error == "Car not found":
                self.clearForm()
                self.loadCars()
            return
        self.showMessage(data["message"])
        self.loadCars()

    def deleteCar(self):
        """Ask for confirmation, then POST /cars/<id>/delete."""
        if not self.checkSelected():
            return
        car_name = self.car_name_entry.get()
        if not messagebox.askyesno("Confirm", f"Delete car {self.selected_id} ({car_name})?"):
            return

        data, error = sendRequest(f"/cars/{self.selected_id}/delete", {})
        if error:
            self.showError(error)
            if error == "Car not found":
                self.clearForm()
                self.loadCars()
            return
        self.showMessage(data["message"])
        self.clearForm()
        self.loadCars()

    def onSelect(self, event):
        """Fill the inputs with the clicked row."""
        selection = self.table.selection()
        if not selection:
            return
        row_values = self.table.item(selection[0])["values"]
        if row_values[0] == "":
            return  # the "No cars yet" row is not a real car

        self.selected_id = row_values[0]
        self.car_name_entry.delete(0, "end")
        self.car_name_entry.insert(0, row_values[1])
        self.plate_entry.delete(0, "end")
        self.plate_entry.insert(0, row_values[2])
        self.owner_entry.delete(0, "end")
        self.owner_entry.insert(0, row_values[3])
        self.service_box.set(row_values[4])
        self.last_service = str(row_values[4])
        self.cost_entry.delete(0, "end")
        self.cost_entry.insert(0, row_values[5])
        self.status_box.set(row_values[6])

    def onServiceSelect(self, event):
        """If the user picks "Other", open a popup to type the service name."""
        if self.service_box.get() != "Other":
            self.last_service = self.service_box.get()
            return

        typed = simpledialog.askstring("Other service", "Type the service:",
                                       parent=self.root)
        if typed is None or typed.strip() == "":
            # Cancel or empty: go back to the service chosen before
            self.service_box.set(self.last_service)
            return
        self.service_box.set(typed.strip())
        self.last_service = typed.strip()

    def clearForm(self):
        """Empty the inputs and forget the selected car."""
        self.selected_id = None
        self.car_name_entry.delete(0, "end")
        self.plate_entry.delete(0, "end")
        self.owner_entry.delete(0, "end")
        self.cost_entry.delete(0, "end")
        self.service_box.set(SERVICES[0])
        self.last_service = SERVICES[0]
        self.status_box.set(STATUSES[0])
        self.table.selection_remove(self.table.selection())


if __name__ == "__main__":
    root = tk.Tk()
    WorkshopApp(root)
    root.mainloop()

"""
filter_window.py - The Filter popup of the Car Workshop Service Log.

It is opened by the "Filter" button in client.py.
The user picks a car model, a service and a status ("All" = no filter),
then Apply sends the choice back to the main window, which reloads the table.
"""

import tkinter as tk
from tkinter import ttk


ALL = "All"


class FilterWindow:
    """A small popup with three drop-down lists and Apply / Show all buttons."""

    def __init__(self, parent, models, services, statuses, current, on_apply):
        """
        models, services, statuses: the choices for each list (without "All")
        current: the filter in use now, like {"model": "Toyota Camry", "service": "", ...}
        on_apply: function called with the new filter dict
        """
        self.on_apply = on_apply

        self.window = tk.Toplevel(parent)
        self.window.title("Filter")
        self.window.resizable(False, False)
        self.window.transient(parent)  # stay on top of the main window

        form = ttk.Frame(self.window, padding=15)
        form.pack()

        self.model_box = self.addChoice(form, 0, "Car model:", models, current["model"])
        self.service_box = self.addChoice(form, 1, "Service:", services, current["service"])
        self.status_box = self.addChoice(form, 2, "Status:", statuses, current["status"])

        buttons = ttk.Frame(form, padding=(0, 10, 0, 0))
        buttons.grid(row=3, column=0, columnspan=2, sticky="e")
        ttk.Button(buttons, text="Show all", command=self.showAll).pack(side="left", padx=3)
        ttk.Button(buttons, text="Apply", command=self.apply).pack(side="left", padx=3)

    def addChoice(self, form, row, label, choices, selected):
        """One label and one read-only drop-down list. "" means "All"."""
        ttk.Label(form, text=label).grid(row=row, column=0, sticky="w", pady=3)
        box = ttk.Combobox(form, values=[ALL] + choices, state="readonly", width=28)
        box.grid(row=row, column=1, padx=5, pady=3)
        box.set(selected if selected else ALL)
        return box

    def apply(self):
        """Send the chosen filter to the main window and close the popup."""
        filters = {}
        for name, box in (("model", self.model_box), ("service", self.service_box),
                          ("status", self.status_box)):
            filters[name] = "" if box.get() == ALL else box.get()
        self.on_apply(filters)
        self.window.destroy()

    def showAll(self):
        """Remove every filter."""
        self.on_apply({"model": "", "service": "", "status": ""})
        self.window.destroy()

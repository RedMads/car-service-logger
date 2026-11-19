"""
stats_window.py - The Statistics window of the Car Workshop Service Log.

It is opened by the "Statistics" button in client.py.
It gets its numbers from Flask (GET /stats) and draws simple bar charts
on a Tkinter Canvas, so no extra library is needed.
"""

import tkinter as tk
from tkinter import ttk


CHART_WIDTH = 620
CHART_HEIGHT = 300
BAR_COLOR = "#3f7cbf"


class StatsWindow:
    """A window with one tab for the summary and one tab per chart."""

    def __init__(self, parent, stats):
        self.window = tk.Toplevel(parent)
        self.window.title("Statistics")

        tabs = ttk.Notebook(self.window, padding=10)
        tabs.pack(fill="both", expand=True)

        tabs.add(self.buildSummary(tabs, stats["summary"]), text="Summary")
        # Models are saved in lowercase, so show them as "Toyota".
        # Days are saved as "2026-11-20", so show only "11-20" to save space.
        tabs.add(self.buildChart(tabs, "Number of cars per model",
                                 stats["cars_by_model"], "{:.0f}", str.title),
                 text="Cars per model")
        tabs.add(self.buildChart(tabs, "Average odometer per model (km)",
                                 stats["odometer_by_model"], "{:,.0f}", str.title),
                 text="Odometer per model")
        tabs.add(self.buildChart(tabs, "Number of cars per service",
                                 stats["cars_by_service"], "{:.0f}"),
                 text="Services")
        tabs.add(self.buildChart(tabs, "Total cost per day, last 14 days (SAR)",
                                 stats["cost_by_day"], "{:,.0f}", lambda day: day[5:]),
                 text="Cost over time")

    def buildSummary(self, parent, summary):
        """A small two-column table of the main numbers."""
        frame = ttk.Frame(parent, padding=15)
        rows = [
            ("Number of cars", f"{summary['cars']}"),
            ("Waiting", f"{summary['waiting']}"),
            ("Done", f"{summary['done']}"),
            ("Total cost", f"{summary['total_cost']:,.2f} SAR"),
            ("Average cost per car", f"{summary['average_cost']:,.2f} SAR"),
            ("Average odometer *", f"{summary['average_odometer']:,.0f} km"),
        ]
        for row_number, (name, value) in enumerate(rows):
            ttk.Label(frame, text=name + ":").grid(row=row_number, column=0,
                                                   sticky="w", pady=4)
            ttk.Label(frame, text=value, font=("TkDefaultFont", 11, "bold")).grid(
                row=row_number, column=1, sticky="w", padx=20, pady=4)

        ttk.Label(frame, text="* cars with an odometer of 0 km are not counted",
                  foreground="gray").grid(row=len(rows), column=0, columnspan=2,
                                          sticky="w", pady=(12, 0))
        return frame

    def buildChart(self, parent, title, pairs, value_format, make_label=str):
        """A frame with a title and a bar chart of [[label, value], ...].

        value_format is the text shown above each bar, like "{:,.0f}".
        make_label changes how each label is shown (by default it is kept as it is).
        """
        frame = ttk.Frame(parent, padding=10)
        ttk.Label(frame, text=title, font=("TkDefaultFont", 11, "bold")).pack(anchor="w")

        canvas = tk.Canvas(frame, width=CHART_WIDTH, height=CHART_HEIGHT,
                           background="white", highlightthickness=0)
        canvas.pack(pady=5)

        labels = [make_label(str(label)) for label, _ in pairs]
        values = [value for _, value in pairs]
        drawBarChart(canvas, labels, values, value_format)
        return frame


def drawBarChart(canvas, labels, values, value_format):
    """Draw one bar per value, with the value above and the label below it."""
    if len(values) == 0:
        canvas.create_text(CHART_WIDTH / 2, CHART_HEIGHT / 2,
                           text="No data yet", fill="gray")
        return

    # Room around the bars for the numbers (top) and the labels (bottom)
    top, bottom, side = 30, 40, 20
    chart_height = CHART_HEIGHT - top - bottom
    slot_width = (CHART_WIDTH - 2 * side) / len(values)
    bar_width = slot_width * 0.6
    biggest = max(values) or 1  # "or 1" avoids dividing by 0 when all values are 0

    # Base line
    canvas.create_line(side, top + chart_height, CHART_WIDTH - side, top + chart_height)

    for index, (label, value) in enumerate(zip(labels, values)):
        middle = side + slot_width * index + slot_width / 2
        bar_top = top + chart_height - (value / biggest) * chart_height

        canvas.create_rectangle(middle - bar_width / 2, bar_top,
                                middle + bar_width / 2, top + chart_height,
                                fill=BAR_COLOR, outline="")
        canvas.create_text(middle, bar_top - 10, text=value_format.format(value))
        # Long labels are cut so they do not overlap the next bar (about 7 px per letter)
        max_letters = max(3, int(slot_width // 7))
        short_label = label if len(label) <= max_letters else label[:max_letters - 1] + "…"
        canvas.create_text(middle, top + chart_height + 15, text=short_label)

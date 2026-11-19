"""
stats_window.py - The Statistics window of the Car Workshop Service Log.

It is opened by the "Statistics" button in client.py.
It gets its numbers from Flask (GET /stats) and draws simple bar charts
on a Tkinter Canvas, so no extra library is needed.
"""

import tkinter as tk
from tkinter import font, ttk


MAX_BARS = 14          # the longest list (cost per day, last 14 days)
ROW_HEIGHT = 26        # pixels for one bar and its label
BAR_HEIGHT = 18
PADDING = 10
MAX_LABEL_WIDTH = 200  # longer labels are cut with "…"
CHART_WIDTH = 640
CHART_HEIGHT = MAX_BARS * ROW_HEIGHT + 2 * PADDING
BAR_COLOR = "#3f7cbf"
TEXT_FONT = None       # set when the first window opens (Tk must exist first)


class StatsWindow:
    """A window with one tab for the summary and one tab per chart."""

    def __init__(self, parent, stats):
        global TEXT_FONT
        TEXT_FONT = font.nametofont("TkDefaultFont")  # used to measure label widths
        self.window = tk.Toplevel(parent)
        self.window.title("Statistics")

        tabs = ttk.Notebook(self.window, padding=10)
        tabs.pack(fill="both", expand=True)

        tabs.add(self.buildSummary(tabs, stats["summary"]), text="Summary")
        tabs.add(self.buildChart(tabs, "Number of cars per model",
                                 stats["cars_by_model"], "{:.0f}"),
                 text="Cars per model")
        tabs.add(self.buildChart(tabs, "Average odometer per model (km)",
                                 stats["odometer_by_model"], "{:,.0f}"),
                 text="Odometer per model")
        tabs.add(self.buildChart(tabs, "Number of cars per service",
                                 stats["cars_by_service"], "{:.0f}"),
                 text="Services")
        tabs.add(self.buildChart(tabs, "Total cost per day, last 14 days (SAR)",
                                 stats["cost_by_day"], "{:,.0f}"),
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

    def buildChart(self, parent, title, pairs, value_format):
        """A frame with a title and a bar chart of [[label, value], ...].

        value_format is the text shown after each bar, like "{:,.0f}".
        """
        frame = ttk.Frame(parent, padding=10)
        ttk.Label(frame, text=title, font=("TkDefaultFont", 11, "bold")).pack(anchor="w")

        canvas = tk.Canvas(frame, width=CHART_WIDTH, height=CHART_HEIGHT,
                           background="white", highlightthickness=0)
        canvas.pack(pady=5)

        labels = [str(label) for label, _ in pairs]
        values = [value for _, value in pairs]
        drawBarChart(canvas, labels, values, value_format)
        return frame


def fitText(text, max_width):
    """Cut text with "…" so it is not wider than max_width pixels."""
    if TEXT_FONT.measure(text) <= max_width:
        return text
    while len(text) > 1 and TEXT_FONT.measure(text + "…") > max_width:
        text = text[:-1]
    return text + "…"


def drawBarChart(canvas, labels, values, value_format):
    """Draw one horizontal bar per value: label on the left, value after the bar.

    Horizontal bars give every label a full line, so long names never overlap.
    """
    if len(values) == 0:
        canvas.create_text(CHART_WIDTH / 2, CHART_HEIGHT / 2,
                           text="No data yet", fill="gray")
        return

    value_texts = [value_format.format(value) for value in values]

    # Width of the label column = the longest label (but not more than MAX_LABEL_WIDTH)
    label_width = min(MAX_LABEL_WIDTH, max(TEXT_FONT.measure(label) for label in labels))
    # Room after the longest bar for its number
    value_width = max(TEXT_FONT.measure(text) for text in value_texts) + 10

    left = PADDING + label_width + 10            # where the bars start
    longest_bar = CHART_WIDTH - left - value_width - PADDING
    biggest = max(values) or 1                   # "or 1" avoids dividing by 0

    for index, (label, value, value_text) in enumerate(zip(labels, values, value_texts)):
        middle = PADDING + ROW_HEIGHT * index + ROW_HEIGHT / 2
        bar_end = left + (value / biggest) * longest_bar

        canvas.create_text(left - 10, middle, text=fitText(label, label_width),
                           anchor="e", font=TEXT_FONT)
        canvas.create_rectangle(left, middle - BAR_HEIGHT / 2, bar_end,
                                middle + BAR_HEIGHT / 2, fill=BAR_COLOR, outline="")
        canvas.create_text(bar_end + 5, middle, text=value_text,
                           anchor="w", font=TEXT_FONT)

    # Line where the bars start
    canvas.create_line(left, PADDING, left, PADDING + ROW_HEIGHT * len(values))

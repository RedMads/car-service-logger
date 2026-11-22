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


class StatsWindow:
    """A window with one tab for the summary and one tab per chart."""

    def __init__(self, parent, stats):
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
        for row_number in range(len(rows)):
            name, value = rows[row_number]
            ttk.Label(frame, text=name + ":").grid(row=row_number, column=0,
                                                   sticky="w", pady=4)
            ttk.Label(frame, text=value, font=("TkDefaultFont", 11, "bold")).grid(
                row=row_number, column=1, sticky="w", padx=20, pady=4)

        ttk.Label(frame, text="* cars with an odometer of 0 km are not counted",
                  foreground="gray").grid(row=len(rows), column=0, columnspan=2,
                                          sticky="w", pady=(12, 0))
        return frame

    def buildChart(self, parent, title, pairs, value_format):
        """A tab with a title and a bar chart; value_format is like "{:,.0f}"."""
        frame = ttk.Frame(parent, padding=10)
        ttk.Label(frame, text=title, font=("TkDefaultFont", 11, "bold")).pack(anchor="w")

        canvas = tk.Canvas(frame, width=CHART_WIDTH, height=CHART_HEIGHT,
                           background="white", highlightthickness=0)
        canvas.pack(pady=5)

        labels = []
        values = []
        for label, value in pairs:
            labels.append(str(label))
            values.append(value)
        drawBarChart(canvas, labels, values, value_format)
        return frame


def fitText(text, max_width, text_font):
    """Cut text with "…" so it is not wider than max_width pixels."""
    if text_font.measure(text) <= max_width:
        return text
    while len(text) > 1 and text_font.measure(text + "…") > max_width:
        text = text[:-1]
    return text + "…"


def drawBarChart(canvas, labels, values, value_format):
    """Draw one horizontal bar per value: label on the left, number after the bar."""
    # Horizontal bars give every label its own line, so long names never overlap
    if len(values) == 0:
        canvas.create_text(CHART_WIDTH / 2, CHART_HEIGHT / 2,
                           text="No data yet", fill="gray")
        return

    # The window's normal font, used to measure how wide each text is
    text_font = font.nametofont("TkDefaultFont")

    value_texts = []
    for value in values:
        value_texts.append(value_format.format(value))

    # Width of the label column = the longest label (but not more than MAX_LABEL_WIDTH)
    longest_label = 0
    for label in labels:
        longest_label = max(longest_label, text_font.measure(label))
    label_width = min(MAX_LABEL_WIDTH, longest_label)

    # Room after the longest bar for its number
    longest_value = 0
    for text in value_texts:
        longest_value = max(longest_value, text_font.measure(text))
    value_width = longest_value + 10

    left = PADDING + label_width + 10            # where the bars start
    longest_bar = CHART_WIDTH - left - value_width - PADDING
    biggest = max(values)
    if biggest == 0:
        biggest = 1                              # avoids dividing by 0

    for index in range(len(values)):
        middle = PADDING + ROW_HEIGHT * index + ROW_HEIGHT / 2
        bar_end = left + (values[index] / biggest) * longest_bar

        label = fitText(labels[index], label_width, text_font)
        canvas.create_text(left - 10, middle, text=label, anchor="e", font=text_font)
        canvas.create_rectangle(left, middle - BAR_HEIGHT / 2, bar_end,
                                middle + BAR_HEIGHT / 2, fill=BAR_COLOR, outline="")
        canvas.create_text(bar_end + 5, middle, text=value_texts[index],
                           anchor="w", font=text_font)

    # Line where the bars start
    canvas.create_line(left, PADDING, left, PADDING + ROW_HEIGHT * len(values))

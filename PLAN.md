# PLAN.md — Car Workshop Service Log

Advanced Programming 462 — Individual Project
Tkinter (front end) ↔ Flask (back end) ↔ SQLite (storage)

> **Main rule for implementation: KEEP IT SIMPLE.**
> The student must explain every line during the presentation and code check.
> No extra libraries, no fancy patterns, no over-engineering. Short functions, clear names, comments in plain English.

---

## 1. What the system is

A small desktop app for a **car workshop**. When a customer brings a car in, the employee records:

- the car (e.g. `Camry 2020`)
- the owner (e.g. `Ahmed`)
- the service (e.g. `Oil change`)
- the cost in SAR (e.g. `150`)
- the status: `Waiting` or `Done`

The employee can **add, view, edit and delete** records from a Tkinter window.
Records are saved in SQLite, so they are still there after the app is closed.

**Extra feature:** a **Total cost** label that shows the sum of all service costs (from one SQL `SUM` query).

**Who it helps:** small workshops that still write cars on paper.

---

## 2. How the parts connect

```
 ┌──────────────┐   HTTP request   ┌──────────────┐    SQL     ┌──────────────┐
 │   Tkinter    │ ───────────────► │    Flask     │ ─────────► │    SQLite    │
 │  client.py   │ ◄─────────────── │  server.py   │ ◄───────── │   cars.db    │
 │  (window)    │   JSON reply     │ + database.py│   rows     │   (file)     │
 └──────────────┘                  └──────────────┘            └──────────────┘
```

- **client.py** — the window. It never touches the database. It only sends HTTP requests to Flask using `urllib`.
- **server.py** — Flask app on port **5050**. Checks input, calls the database class, replies with JSON.
- **database.py** — class `CarDB`. All SQL lives here.
- **report.py** — separate terminal script. Gets records from Flask and writes a text report using a thread.

### One complete action (Add)

1. User fills the boxes and clicks **Add**.
2. `client.py` sends a POST to `http://127.0.0.1:5050/cars/add` with the values.
3. `server.py` checks the values. If bad → JSON error with status **400**.
4. If good → `CarDB.add(...)` runs `INSERT ... VALUES (?, ?, ?, ?, ?)`.
5. Flask replies `{"message": "Car added"}`.
6. Window shows a success message and refreshes the table.

---

## 3. Project files

```
Final_project/
├── database.py        # class CarDB (all SQLite work)
├── server.py          # Flask routes + input checks
├── client.py          # Tkinter window + HTTP requests
├── report.py          # thread + text report
├── requirements.txt   # flask
├── README.md          # setup, run steps, topic locations, tests, credits
├── .gitignore         # venv/, __pycache__/, cars.db (optional), report.txt
└── PLAN.md            # this file
```

Only one external package: **Flask**. Everything else (`tkinter`, `sqlite3`, `urllib`, `json`, `socket`, `threading`) comes with Python.

---

## 4. Database — `database.py`

### Table

```sql
CREATE TABLE IF NOT EXISTS cars (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    car_name TEXT NOT NULL,
    owner    TEXT NOT NULL,
    service  TEXT NOT NULL,
    cost     REAL NOT NULL,
    status   TEXT NOT NULL
);
```

`CREATE TABLE IF NOT EXISTS` → creates the table only if missing, keeps existing records.

### Class `CarDB`

```python
class CarDB:
    def __init__(self, db_file="cars.db")
    def connect(self)                 # returns a new sqlite3 connection (row_factory = sqlite3.Row)
    def create_table(self)
    def get_all(self)                 # list of dicts
    def get_one(self, car_id)         # dict or None
    def add(self, car_name, owner, service, cost, status)
    def edit(self, car_id, car_name, owner, service, cost, status)   # returns True/False (found or not)
    def delete(self, car_id)          # returns True/False
    def total_cost(self)              # number (0 if empty)
```

Rules:
- **Every method opens its own connection**, does its work, `commit()` if it changed data, and closes it. Use `with` or `try/finally` so it always closes.
- **Always use `?` placeholders**, never f-strings in SQL.
- `edit` and `delete` use `cursor.rowcount` to know if the ID existed (0 → unknown record).
- Rows are converted to plain dicts: `[dict(row) for row in rows]` (list of dicts = collections topic).

Each method should be about 3–8 lines.

---

## 5. Server — `server.py`

```python
app = Flask(__name__)
db = CarDB()
db.create_table()          # runs at start-up

SERVICES = ["Oil change", "Brakes", "Tires", "AC", "Engine", "Other"]
STATUSES = ["Waiting", "Done"]
```

### Routes

| Method | Route                  | What it does                        | Replies                         |
|--------|------------------------|-------------------------------------|---------------------------------|
| GET    | `/cars`                | list all cars (JSON route for report) | 200 `{"cars": [...]}`         |
| GET    | `/cars/<int:car_id>`   | one car                             | 200 car / 404 not found         |
| POST   | `/cars/add`            | add a car                           | 201 message / 400 error         |
| POST   | `/cars/<int:car_id>/edit`   | edit a car                     | 200 / 400 / 404                 |
| POST   | `/cars/<int:car_id>/delete` | delete a car                   | 200 / 404                       |
| GET    | `/total`               | extra feature: total cost           | 200 `{"total": 550.0}`          |

- `GET` for reading, `POST` for add/edit/delete (as required).
- Values are read with `request.form`.
- All replies are JSON using `jsonify(...)`.

### One validation function (used by add and edit)

```python
def check_car_form(form):
    """Returns (data_dict, None) if valid, or (None, error_message) if not."""
```

Checks:
1. `car_name`, `owner`, `service`, `cost`, `status` are not empty (after `.strip()`).
2. `cost` converts to `float` (use `try/except ValueError`) and is `>= 0` and `<= 100000`.
3. `service` is in `SERVICES`.
4. `status` is in `STATUSES`.

If any check fails → `return jsonify({"error": "Cost must be a number"}), 400`.

### Unknown record
If `get_one` returns `None` or `edit`/`delete` returns `False` → `return jsonify({"error": "Car not found"}), 404`.

### Database errors
Wrap DB calls in `try/except sqlite3.Error` → reply `{"error": "Database error"}` with status 500. Keep it to one simple pattern.

### Start
```python
if __name__ == "__main__":
    app.run(port=5050)
```

---

## 6. Client — `client.py`

### One request helper (the most important function to explain)

```python
SERVER = "http://127.0.0.1:5050"

def send_request(path, values=None):
    """GET if values is None, POST otherwise.
    Returns (data, None) on success or (None, error_message) on failure."""
```

Inside:
1. `url = SERVER + path`
2. If `values` → `body = urlencode(values).encode("utf-8")`, else `body = None`.
3. `with urlopen(url, data=body, timeout=5) as reply:` → `json.loads(reply.read().decode("utf-8"))`
4. Exceptions, **in this order**:
   - `except HTTPError as error:` → read Flask JSON with `json.loads(error.read().decode("utf-8"))`, return its `"error"` message.
   - `except URLError:` → `"Cannot connect to the server. Is Flask running?"`
   - `except socket.timeout:` → `"The server took too long to reply."`

Every button uses this helper, so error handling is in **one place**. If Flask is stopped, the user sees an error; when Flask restarts, they just click again (no window restart needed).

### Class `WorkshopApp` (holds the window)

Layout (top to bottom, use `grid` or `pack`, keep it plain):

```
┌───────────────────────────────────────────────┐
│ Car name: [__________]   Owner:  [__________] │
│ Service:  [Oil change ▼] Cost:   [__________] │
│ Status:   [Waiting    ▼]                      │
│                                               │
│ [Add] [Update] [Delete] [Clear] [Refresh]     │
│                                               │
│ ┌ ID │ Car │ Owner │ Service │ Cost │ Status ┐│
│ │ 1  │ ... │ ...   │ ...     │ ...  │ ...    ││
│ └─────────────────────────────────────────────┘│
│ Total cost: 550.00 SAR                        │
│ Status message: Car added                     │
└───────────────────────────────────────────────┘
```

- `ttk.Entry` for car name, owner, cost.
- `ttk.Combobox` (readonly) for service and status.
- `ttk.Treeview` for the table.
- A label at the bottom for messages; also use `messagebox` for errors.

### Methods

```python
def load_cars(self)        # GET /cars → fill table; if empty show "No cars yet"; then load_total()
def load_total(self)       # GET /total → update total label
def get_form_values(self)  # dict from the inputs
def add_car(self)          # POST /cars/add → message → load_cars()
def update_car(self)       # needs a selected row → POST /cars/<id>/edit
def delete_car(self)       # needs a selected row → messagebox.askyesno → POST /cars/<id>/delete
def on_select(self, event) # click row → fill inputs, remember selected id
def clear_form(self)
```

- No server address is typed by the user. `load_cars()` is called automatically when the window opens.
- If no row is selected for Update/Delete → show "Please select a car first".
- If the edited/deleted car no longer exists → Flask returns 404 → show "Car not found" and reload the table.

---

## 7. Report helper — `report.py`

Run in a terminal: `python report.py` (Flask must be running).

Steps:
1. `GET http://127.0.0.1:5050/cars` with `urlopen` (same error handling: `HTTPError`, `URLError`, `socket.timeout`). If it fails, print the error and stop.
2. Create **one** `Thread(target=write_report, args=(cars, "report.txt", result))` and call `start()`.
3. `write_report` opens the file with `with open(filename, "w", encoding="utf-8")`, writes the report, catches `OSError`, and stores `True/False` in `result` (a dict or list so the main thread can read it).
4. Main thread calls `join()`, then prints `"Report saved to report.txt"` or `"Could not save the report"`.

Example `report.txt`:
```
Car Workshop Report
===================
1. Camry 2020 | Ahmed | Oil change | 150.00 SAR | Done
2. Accord 2018 | Sara | Brakes | 400.00 SAR | Waiting

Number of cars: 2
Total cost: 550.00 SAR
```
If there are no cars, write `No cars saved.`

---

## 8. requirements.txt

```
flask
```

---

## 9. README.md (must contain)

1. **What the app does** (2–3 lines).
2. **Setup steps:**
   ```
   python -m venv venv
   source venv/bin/activate        # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. **Create tables:** automatic when `server.py` starts (`CarDB.create_table()`).
4. **Run:**
   ```
   python server.py      # terminal 1 (start first)
   python client.py      # terminal 2
   python report.py      # terminal 3, writes report.txt
   ```
5. **Course topic locations** table:

| Topic | Where |
|---|---|
| Python & collections | `database.py` `get_all()` (list of dicts), `client.py` `get_form_values()` (dict), `load_cars()` (loop) |
| Exceptions | `server.py` `check_car_form()` (ValueError), `client.py` `send_request()` (HTTPError/URLError/timeout), `report.py` `write_report()` (OSError) |
| Classes | `database.py` `CarDB`, `client.py` `WorkshopApp` |
| SQLite | `database.py` `CarDB` methods |
| Threads & files | `report.py` `main()` + `write_report()` |
| Tkinter | `client.py` `WorkshopApp` |
| Client & server | `client.py` `send_request()` → `server.py` `add_car()` (explain the Add request/reply) |
| Flask | `server.py` routes + `check_car_form()` |

6. **Test results** (checklist from section 10, marked pass/fail).
7. **Credits** (outside code, AI assistance used — follow the course policy).

---

## 10. Test checklist (do these before submitting)

- [ ] Fresh folder → follow README → app runs.
- [ ] Add, view, edit, delete work. Only the chosen record changes.
- [ ] Delete asks for confirmation.
- [ ] Stop and restart Flask + Tkinter → records still there.
- [ ] Empty name → error message. Cost `abc` → error. Cost `-5` → error.
- [ ] Empty database → table shows "No cars yet", total = 0.
- [ ] Unknown ID: open two windows, delete a car in one, edit it in the other → "Car not found" (404).
- [ ] Stop Flask, click Refresh → "Cannot connect to the server". Start Flask, click Refresh → works without restarting the window.
- [ ] `python report.py` → `report.txt` created with correct cars and total.

---

## 11. Implementation order (with git commits)

1. `git init`, add `.gitignore`, `requirements.txt` → commit "Project setup"
2. `database.py` (CarDB) → commit "Add CarDB class with SQLite"
3. `server.py` routes + validation → commit "Add Flask routes and input checks"
4. `client.py` window + `send_request` → commit "Add Tkinter window"
5. Delete confirmation, empty list, error messages → commit "Handle errors and empty list"
6. Total cost feature → commit "Add total cost feature"
7. `report.py` → commit "Add threaded report helper"
8. `README.md` + tests → commit "Add README and test results"

Push to a GitHub repo (if private, invite `majedoh`). Spread commits over **both weeks** (the commit history is marked).

### Submission (Blackboard)
- One ZIP named `Project_StudentID.zip` containing: all `.py` files, `README.md`, `requirements.txt`, slides (PDF or PowerPoint). `cars.db` with sample records is optional.
- Leave out `venv/`, `__pycache__/`, and any passwords.
- ZIP and GitHub must contain the **same final version**.
- Submission text: name, student ID, GitHub link.

---

## 12. Things to NOT do (keep it simple)

- No ORM (no SQLAlchemy), no `requests` library — use `sqlite3` and `urllib` only.
- No login, no extra tables, no dates, no search, no styling frameworks.
- No blueprints, no config files, no decorators beyond `@app.route`.
- No `async`, no extra threads in the GUI.
- Keep each file short and readable; add short comments explaining each step.

---

## 13. Presentation outline (10 min)

1. **1 min** — Idea: car workshop service log, who it helps.
2. **1 min** — Diagram: Tkinter → Flask → SQLite.
3. **6 min** — Demo: add, edit, delete (confirm), total cost, an invalid cost error, stop Flask → connection error.
4. **2 min** — Explain `send_request()`, the `/cars/add` route, the `CarDB` class, one SQL query with `?`, show GitHub commits.

Possible small changes the instructor may ask for: rename a label, change the max cost limit, add a service to `SERVICES`.

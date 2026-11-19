# Car Workshop Service Log

A small desktop app for a car workshop. The employee records each car that comes in
(car, license plate, owner, service, cost in SAR, status `Waiting` / `Done`) and can add, view, edit
and delete records. The extra feature is a **Total cost** label that sums all services.
It helps small workshops that still write cars on paper.

```
Tkinter (src/client.py)  --HTTP-->  Flask (src/server.py)  --SQL-->  SQLite (src/cars.db)
                         <--JSON--                         <--rows--
```

## Project files

```
Final_project/
├── src/
│   ├── database.py   # class CarDB - all SQLite work
│   ├── server.py     # Flask routes + input checks (port 5050)
│   ├── client.py     # Tkinter window + HTTP requests
│   └── report.py     # thread that writes report.txt
├── requirements.txt  # flask
├── README.md
└── PLAN.md
```

## Setup

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Create the tables

Nothing to do by hand. When `server.py` starts it calls `CarDB.createTable()`, which runs
`CREATE TABLE IF NOT EXISTS`. The table is created only if it is missing, so old records are kept.
If an older `cars.db` has no `plate` column, `createTable()` adds it (old cars get an empty plate).

The license plate uses the Saudi format: 1-4 numbers, a space, then 3 English letters,
for example `1234 ABC`. Lowercase or no space (`1234abc`) is accepted and saved as `1234 ABC`.

Choosing **Other** in the Service list opens a small popup where the service is typed
(for example `Windshield repair`). Cancel keeps the service chosen before. Typed services
can be up to 40 characters.
The database file is `src/cars.db`.

## Run

```bash
python src/server.py      # terminal 1 - start Flask first
python src/client.py      # terminal 2 - the window
python src/report.py      # terminal 3 - writes src/report.txt
```

## Routes

| Method | Route                       | What it does                    | Replies          |
|--------|-----------------------------|---------------------------------|------------------|
| GET    | `/cars`                     | all cars (JSON route for report) | 200              |
| GET    | `/cars/<car_id>`            | one car                         | 200 / 404        |
| POST   | `/cars/add`                 | add a car                       | 201 / 400        |
| POST   | `/cars/<car_id>/edit`       | edit a car                      | 200 / 400 / 404  |
| POST   | `/cars/<car_id>/delete`     | delete a car                    | 200 / 404        |
| GET    | `/total`                    | extra feature: total cost       | 200              |

## Naming style

- variables and parameters: `snake_case` (`car_name`, `selected_id`)
- functions and methods: `camelCase` (`sendRequest`, `checkCarForm`, `getAll`)
- classes: `PascalCase` (`CarDB`, `WorkshopApp`)

## Course topic locations

| Topic | Where |
|---|---|
| Python & collections | `src/database.py` `CarDB.getAll()` (list of dicts), `src/client.py` `WorkshopApp.getFormValues()` (dict), `WorkshopApp.loadCars()` (loop), `src/server.py` `checkCarForm()` (loop over dict) |
| Exceptions | `src/server.py` `checkCarForm()` (`ValueError`) and every route (`sqlite3.Error`), `src/client.py` `sendRequest()` (`HTTPError` / `URLError` / `socket.timeout`), `src/report.py` `writeReport()` (`OSError`) |
| Classes | `src/database.py` `CarDB`, `src/client.py` `WorkshopApp` |
| SQLite | `src/database.py` `CarDB` methods (`?` placeholders, one connection per call, commit, close) |
| Threads & files | `src/report.py` `main()` (`Thread`, `start()`, `join()`) + `writeReport()` (`with open(..., encoding="utf-8")`) |
| Tkinter | `src/client.py` `WorkshopApp` (labels, entries, comboboxes, buttons, Treeview, messagebox, simpledialog in `onServiceSelect()`) |
| Client & server | `src/client.py` `WorkshopApp.addCar()` → `sendRequest("/cars/add", values)` → `src/server.py` `addCar()` → `CarDB.add()` → JSON `{"message": "Car added"}` |
| Flask | `src/server.py` routes + `checkCarForm()` + `jsonify` replies |

### One request traced (Add)

1. The user fills the inputs and clicks **Add**. This calls `WorkshopApp.addCar()`.
2. `getFormValues()` builds a dict, and `sendRequest()` encodes it with `urlencode` and POSTs
   it to `http://127.0.0.1:5050/cars/add` using `urlopen(..., timeout=5)`.
3. Flask's `addCar()` reads `request.form` and calls `checkCarForm()`. Bad values give JSON
   `{"error": ...}` with status 400.
4. Good values go to `CarDB.add()`, which runs `INSERT ... VALUES (?, ?, ?, ?, ?, ?)`, commits and closes.
5. Flask replies `{"message": "Car added"}` (201). The window shows the message and reloads the table and total.

## Test results

| Test | Result |
|---|---|
| Fresh clone → follow README → app runs | Pass |
| Add, view, edit, delete work; only the chosen record changes | Pass |
| Delete asks for confirmation (yes/no box) | Pass |
| Stop and restart Flask → records still there | Pass |
| Empty car name → "Car name is required" | Pass |
| Cost `abc` → "Cost must be a number" | Pass |
| Plate `ABC 123` or `12345 ABC` → "Plate must be 1-4 numbers then 3 letters, like 1234 ABC" | Pass |
| Plate typed as `4321abc` → saved as `4321 ABC` | Pass |
| Service **Other** → popup; typed `Windshield repair` is saved and shown in the table | Pass |
| Service **Other** → Cancel or empty text → service goes back to the previous choice | Pass |
| Typed service longer than 40 characters → "Service must be 40 characters or less" | Pass |
| Old `cars.db` without a plate column → column added on start, old cars keep their data | Pass |
| Cost `-5` → "Cost must be between 0 and 100000" | Pass |
| Empty database → table shows "No cars yet", total 0.00 | Pass |
| Unknown ID: same car selected in two windows, deleted in one, edited in the other → "Car not found" (404) | Pass |
| Update/Delete with no row selected → "Please select a car first" | Pass |
| Stop Flask, Refresh → "Cannot connect to the server. Is Flask running?"; start Flask, Refresh → works without restarting the window | Pass |
| `python src/report.py` → `report.txt` with correct cars and total | Pass |
| `report.py` with Flask stopped → clear connection error | Pass |

The GUI tests were run by calling the window's methods from a test script against a running
server, with the popup boxes replaced. Please also click through them by hand once before the demo.

## Credits

- Only Python's standard library and [Flask](https://flask.palletsprojects.com/) are used.
- The code and this README were written with AI assistance (Claude by Anthropic), following
  the project plan in `PLAN.md`. Check the course academic integrity policy on AI tools and
  declare this use as it requires.

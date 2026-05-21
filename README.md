# DayAvg

DayAvg is a small Flask application for calculating the average daily holding cost of an item.

Users can open the page on a local network, enter:
- item name
- purchase price
- purchase date

The app then:
- calculates held days from the purchase date through today
- computes the average daily cost
- stores the record in a local SQLite database
- shows the full history on the home page

## Tech Stack

- Python 3.13.5
- Flask
- Jinja2
- SQLite

## Project Layout

- `src/app.py`: Flask entry point
- `src/dayavg/services/`: validation and calculation logic
- `src/dayavg/storage/`: SQLite setup and repository
- `templates/`: HTML templates
- `static/`: styles
- `tests/`: automated tests
- `outputs/dayavg.db`: local data file

## Run

```powershell
D:\Anaconda\python.exe src/app.py
```

Then open `http://<your-lan-ip>:5000` on another device in the same local network.

Detailed instructions live in `docs/usage.md`.

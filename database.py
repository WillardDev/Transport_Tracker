import sqlite3
from datetime import datetime

DB_NAME = "matatu_tracker.db"


def get_connection():
    return sqlite3.connect(DB_NAME)


def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS saccos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            code TEXT NOT NULL UNIQUE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS routes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            route_number TEXT NOT NULL,
            start_point TEXT NOT NULL,
            end_point TEXT NOT NULL,
            sacco_id INTEGER,
            fare_min INTEGER,
            fare_max INTEGER,
            route_type TEXT NOT NULL DEFAULT 'local',
            FOREIGN KEY (sacco_id) REFERENCES saccos(id)
        )
    """)
    try:
        cursor.execute("ALTER TABLE routes ADD COLUMN route_type TEXT NOT NULL DEFAULT 'local'")
    except sqlite3.OperationalError:
        pass

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fares (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            route_id INTEGER,
            amount INTEGER NOT NULL,
            date TEXT NOT NULL,
            weather_condition TEXT,
            FOREIGN KEY (route_id) REFERENCES routes(id)
        )
    """)

    conn.commit()
    conn.close()


def insert_sacco(name, code):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO saccos (name, code) VALUES (?, ?)", (name, code))
        conn.commit()
        sacco_id = cursor.lastrowid
        conn.close()
        return sacco_id, True
    except sqlite3.IntegrityError:
        cursor.execute("SELECT id FROM saccos WHERE code = ?", (code,))
        sacco_id = cursor.fetchone()[0]
        conn.close()
        return sacco_id, False

def insert_route(route_number, start, end, sacco_id, fare_min=None, fare_max=None, route_type='local'):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO routes (route_number, start_point, end_point, sacco_id, fare_min, fare_max, route_type) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (route_number, start, end, sacco_id, fare_min, fare_max, route_type)
    )
    conn.commit()
    route_db_id = cursor.lastrowid
    conn.close()
    return route_db_id

def insert_fare(route_db_id, amount, date=None, weather=None):
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO fares (route_id, amount, date, weather_condition) VALUES (?, ?, ?, ?)",
        (route_db_id, amount, date, weather)
    )
    conn.commit()
    fare_id = cursor.lastrowid
    conn.close()
    return fare_id


def get_all_saccos():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, code FROM saccos ORDER BY name")
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_all_routes(route_type=None):
    conn = get_connection()
    cursor = conn.cursor()
    if route_type:
        cursor.execute("""
            SELECT r.id, r.route_number, r.start_point, r.end_point, s.name, s.code,
                   r.fare_min, r.fare_max, r.route_type
            FROM routes r
            JOIN saccos s ON r.sacco_id = s.id
            WHERE r.route_type = ?
            ORDER BY r.route_number
        """, (route_type,))
    else:
        cursor.execute("""
            SELECT r.id, r.route_number, r.start_point, r.end_point, s.name, s.code,
                   r.fare_min, r.fare_max, r.route_type
            FROM routes r
            JOIN saccos s ON r.sacco_id = s.id
            ORDER BY r.route_number
        """)
    rows = cursor.fetchall()
    conn.close()
    return rows

def search_routes(search_term, route_type=None):
    conn = get_connection()
    cursor = conn.cursor()
    if route_type:
        cursor.execute("""
            SELECT r.id, r.route_number, r.start_point, r.end_point, s.name, s.code,
                   r.fare_min, r.fare_max, r.route_type
            FROM routes r
            JOIN saccos s ON r.sacco_id = s.id
            WHERE (r.start_point LIKE ?
               OR r.end_point LIKE ?
               OR r.route_number LIKE ?
               OR s.name LIKE ?)
              AND r.route_type = ?
            ORDER BY r.route_number
        """, (f"%{search_term}%", f"%{search_term}%", f"%{search_term}%", f"%{search_term}%", route_type))
    else:
        cursor.execute("""
            SELECT r.id, r.route_number, r.start_point, r.end_point, s.name, s.code,
                   r.fare_min, r.fare_max, r.route_type
            FROM routes r
            JOIN saccos s ON r.sacco_id = s.id
            WHERE r.start_point LIKE ?
               OR r.end_point LIKE ?
               OR r.route_number LIKE ?
               OR s.name LIKE ?
            ORDER BY r.route_number
        """, (f"%{search_term}%", f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_route_fares(route_db_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, amount, date, weather_condition
        FROM fares
        WHERE route_id = ?
        ORDER BY date DESC
    """, (route_db_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_latest_fare(route_db_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT amount, date, weather_condition
        FROM fares
        WHERE route_id = ?
        ORDER BY date DESC LIMIT 1
    """, (route_db_id,))
    row = cursor.fetchone()
    conn.close()
    return row

def route_exists(route_number, start, end, sacco_id, route_type='local'):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id FROM routes
        WHERE route_number = ? AND start_point = ? AND end_point = ? AND sacco_id = ? AND route_type = ?
    """, (route_number, start, end, sacco_id, route_type))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def export_routes_to_csv(filename="matatu_routes_export.csv"):
    import csv

    routes = get_all_routes()
    if not routes:
        return False

    with open(filename, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Route Number", "From", "To", "SACCO", "Fare Min (KSh)", "Fare Max (KSh)", "Type", "Latest Fare (KSh)", "Date"])

        for route in routes:
            db_id, route_number, start, end, sacco_name, sacco_code, fmin, fmax, route_type = route
            fmin_s = str(fmin) if fmin else "N/A"
            fmax_s = str(fmax) if fmax else "N/A"
            latest = get_latest_fare(db_id)
            fare_amount = str(latest[0]) if latest else "N/A"
            fare_date = latest[1] if latest else "N/A"
            writer.writerow([route_number, start, end, f"{sacco_name} ({sacco_code})", fmin_s, fmax_s, route_type, fare_amount, fare_date])

    return True

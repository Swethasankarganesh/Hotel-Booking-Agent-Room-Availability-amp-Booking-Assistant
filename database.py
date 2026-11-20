
import sqlite3
from pathlib import Path

# -----------------------------------
# DATABASE CONFIGURATION
# -----------------------------------

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "hotel.db"


# -----------------------------------
# DATABASE CONNECTION
# -----------------------------------

def get_connection():
    DATA_DIR.mkdir(exist_ok=True)

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    return connection


# -----------------------------------
# CREATE DATABASE TABLES
# -----------------------------------

def create_tables():

    with get_connection() as conn:

        # Rooms table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS rooms (

                room_no INTEGER PRIMARY KEY,

                room_type TEXT NOT NULL,

                bed_type TEXT NOT NULL
                    CHECK (bed_type IN ('Single', 'Double')),

                breakfast_included INTEGER NOT NULL
                    CHECK (breakfast_included IN (0, 1)),

                price_per_night REAL NOT NULL,

                floor INTEGER NOT NULL,

                capacity INTEGER NOT NULL DEFAULT 2,

                status TEXT NOT NULL DEFAULT 'Available'
                    CHECK (status IN ('Available', 'Booked'))

            )
        """)

        # Bookings table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS bookings (

                booking_id INTEGER PRIMARY KEY AUTOINCREMENT,

                room_no INTEGER NOT NULL,

                guest_name TEXT NOT NULL,

                guest_email TEXT NOT NULL,

                check_in TEXT NOT NULL,

                check_out TEXT NOT NULL,

                guests INTEGER NOT NULL,

                total_price REAL NOT NULL,

                booking_status TEXT NOT NULL DEFAULT 'Confirmed',

                created_at TEXT DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (room_no)
                    REFERENCES rooms(room_no)
            )
        """)

        # Improve date-based booking lookups
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_booking_dates
            ON bookings(room_no, check_in, check_out)
        """)

    print("Database tables created successfully!")


# -----------------------------------
# INSERT SAMPLE ROOM DATA
# -----------------------------------

def seed_rooms():

    rooms = [

        # Standard rooms
        (101, "Standard", "Single", 0, 2200, 1, 1, "Available"),
        (102, "Standard", "Single", 1, 2600, 1, 1, "Booked"),
        (103, "Standard", "Double", 0, 3000, 1, 2, "Available"),
        (104, "Standard", "Double", 1, 3400, 1, 2, "Available"),
        (105, "Standard", "Single", 0, 2200, 1, 1, "Available"),
        (106, "Standard", "Double", 1, 3400, 1, 2, "Available"),
        (107, "Standard", "Single", 1, 2600, 1, 1, "Available"),
        (108, "Standard", "Double", 0, 3000, 1, 2, "Booked"),
        (109, "Standard", "Double", 1, 3400, 1, 2, "Available"),
        (110, "Standard", "Single", 0, 2200, 1, 1, "Available"),

        # Deluxe rooms
        (201, "Deluxe", "Double", 1, 4500, 2, 2, "Available"),
        (202, "Deluxe", "Double", 0, 4100, 2, 2, "Booked"),
        (203, "Deluxe", "Single", 1, 3800, 2, 1, "Available"),
        (204, "Deluxe", "Double", 0, 4100, 2, 2, "Available"),
        (205, "Deluxe", "Double", 1, 4500, 2, 2, "Available"),
        (206, "Deluxe", "Single", 0, 3500, 2, 1, "Available"),
        (207, "Deluxe", "Double", 1, 4500, 2, 2, "Booked"),
        (208, "Deluxe", "Single", 1, 3800, 2, 1, "Available"),
        (209, "Deluxe", "Double", 0, 4100, 2, 2, "Available"),
        (210, "Deluxe", "Double", 1, 4500, 2, 2, "Available"),

        # Suite rooms
        (301, "Suite", "Double", 1, 6500, 3, 2, "Available"),
        (302, "Suite", "Double", 0, 6000, 3, 2, "Available"),
        (303, "Suite", "Double", 1, 7000, 3, 3, "Available"),
        (304, "Suite", "Double", 1, 6500, 3, 2, "Booked"),
        (305, "Suite", "Double", 0, 6000, 3, 2, "Available"),
        (306, "Suite", "Double", 1, 7500, 3, 3, "Available"),
        (307, "Suite", "Double", 0, 6000, 3, 2, "Available"),
        (308, "Suite", "Double", 1, 6500, 3, 2, "Available"),
        (309, "Suite", "Double", 1, 7000, 3, 3, "Available"),
        (310, "Suite", "Double", 0, 6000, 3, 2, "Available")
    ]

    with get_connection() as conn:

        existing = conn.execute(
            "SELECT COUNT(*) FROM rooms"
        ).fetchone()[0]

        if existing == 0:

            conn.executemany("""
                INSERT INTO rooms (
                    room_no,
                    room_type,
                    bed_type,
                    breakfast_included,
                    price_per_night,
                    floor,
                    capacity,
                    status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, rooms)

            print("30 sample rooms inserted successfully!")

        else:
            print("Room data already exists. Skipping insertion.")


# -----------------------------------
# VIEW ALL ROOMS
# -----------------------------------

def get_all_rooms():

    with get_connection() as conn:

        rows = conn.execute("""
            SELECT * FROM rooms
            ORDER BY room_no
        """).fetchall()

        return [dict(row) for row in rows]


# -----------------------------------
# DATABASE INITIALIZATION
# -----------------------------------

def initialize_database():

    create_tables()
    seed_rooms()

    print("Hotel database initialized successfully!")


if __name__ == "__main__":
    initialize_database()

    print("\nHotel Room Inventory:\n")

    for room in get_all_rooms():
        print(room)

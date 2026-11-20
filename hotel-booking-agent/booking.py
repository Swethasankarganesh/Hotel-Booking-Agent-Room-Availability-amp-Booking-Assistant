
import re
from datetime import date, datetime

from database import get_connection


def create_booking(
    room_no: int,
    guest_name: str,
    guest_email: str,
    check_in: str,
    check_out: str,
    guests: int
):
    """Create and save a hotel reservation."""

    # 1. Validate guest name
    if not isinstance(guest_name, str) or not guest_name.strip():
        return {
            "success": False,
            "message": "Guest name is required."
        }

    # 2. Validate email
    if not isinstance(guest_email, str) or not re.match(
        r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
        guest_email.strip()
    ):
        return {
            "success": False,
            "message": "Please enter a valid email address."
        }

    # 3. Validate room number and guest count
    if isinstance(room_no, bool) or not isinstance(room_no, int):
        return {"success": False, "message": "Invalid room number."}

    if isinstance(guests, bool) or not isinstance(guests, int) or guests < 1:
        return {"success": False, "message": "Invalid guest count."}

    # 4. Validate dates
    try:
        start_date = datetime.strptime(check_in, "%Y-%m-%d").date()
        end_date = datetime.strptime(check_out, "%Y-%m-%d").date()

    except (ValueError, TypeError):
        return {
            "success": False,
            "message": "Dates must use YYYY-MM-DD format."
        }

    if start_date < date.today():
        return {
            "success": False,
            "message": "Check-in date cannot be in the past."
        }

    if end_date <= start_date:
        return {
            "success": False,
            "message": "Check-out must be after check-in."
        }

    conn = get_connection()

    try:
        # Lock the database while checking and creating booking
        conn.execute("BEGIN IMMEDIATE")

        # 5. Find selected room
        room = conn.execute(
            """
            SELECT *
            FROM rooms
            WHERE room_no = ?
            """,
            (room_no,)
        ).fetchone()

        if room is None:
            conn.rollback()
            return {
                "success": False,
                "message": "Room not found."
            }

        if room["status"] != "Available":
            conn.rollback()
            return {
                "success": False,
                "message": "Room is not available."
            }

        if guests > room["capacity"]:
            conn.rollback()
            return {
                "success": False,
                "message": "Room capacity is insufficient."
            }

        # 6. Check overlapping reservations
        conflict = conn.execute(
            """
            SELECT booking_id
            FROM bookings
            WHERE room_no = ?
              AND booking_status != 'Cancelled'
              AND check_in < ?
              AND check_out > ?
            LIMIT 1
            """,
            (room_no, check_out, check_in)
        ).fetchone()

        if conflict:
            conn.rollback()
            return {
                "success": False,
                "message": "Room is already booked for these dates."
            }

        # 7. Calculate price
        nights = (end_date - start_date).days

        price_per_night = room["price_per_night"]
        total_price = price_per_night * nights

        # 8. Insert booking into database
        cursor = conn.execute(
            """
            INSERT INTO bookings (
                room_no,
                guest_name,
                guest_email,
                check_in,
                check_out,
                guests,
                total_price,
                booking_status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, 'Confirmed')
            """,
            (
                room_no,
                guest_name.strip(),
                guest_email.strip(),
                check_in,
                check_out,
                guests,
                total_price
            )
        )

        booking_id = cursor.lastrowid

        conn.commit()

        # 9. Return booking information
        return {
            "success": True,
            "booking_id": booking_id,
            "room_no": room_no,
            "room_type": room["room_type"],
            "bed_type": room["bed_type"],
            "breakfast": bool(room["breakfast_included"]),
            "guest_name": guest_name.strip(),
            "guest_email": guest_email.strip(),
            "check_in": check_in,
            "check_out": check_out,
            "nights": nights,
            "price_per_night": price_per_night,
            "total_price": total_price,
            "guests": guests,
            "message": "Booking confirmed successfully!"
        }

    except Exception as error:
        conn.rollback()

        return {
            "success": False,
            "message": f"Booking failed: {error}"
        }

    finally:
        conn.close()

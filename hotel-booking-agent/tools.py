
from datetime import date, datetime
from database import get_connection


# ==========================================
# 1. VALIDATE GUEST BOOKING REQUEST
# ==========================================

def validate_booking_request(
    check_in,
    check_out,
    bed_type,
    breakfast,
    guests
):
    """
    Validates the guest's booking requirements.
    """

    try:
        check_in_date = datetime.strptime(
            check_in, "%Y-%m-%d"
        ).date()

        check_out_date = datetime.strptime(
            check_out, "%Y-%m-%d"
        ).date()

    except (ValueError, TypeError):
        return False, "Invalid date format. Use YYYY-MM-DD."

    if check_in_date < date.today():
        return False, "Check-in date cannot be in the past."

    if check_out_date <= check_in_date:
        return False, "Check-out must be after check-in."

    if not isinstance(bed_type, str):
        return False, "Bed type must be Single or Double."

    bed_type = bed_type.strip().capitalize()

    if bed_type not in ["Single", "Double"]:
        return False, "Bed type must be Single or Double."

    if not isinstance(breakfast, bool):
        return False, "Breakfast must be True or False."

    if isinstance(guests, bool) or not isinstance(guests, int):
        return False, "Number of guests must be a whole number."

    if guests < 1:
        return False, "At least one guest is required."

    return True, "Booking request is valid."


# ==========================================
# 2. FIND AVAILABLE ROOMS
# ==========================================

def find_matching_rooms(
    check_in,
    check_out,
    bed_type,
    breakfast,
    guests
):
    """
    Searches SQLite for rooms that match
    the guest's requirements.

    Excludes:
    - Rooms marked as Booked
    - Rooms with overlapping reservations
    - Rooms with insufficient capacity
    """

    query = """
        SELECT
            r.room_no,
            r.room_type,
            r.bed_type,
            r.breakfast_included,
            r.price_per_night,
            r.floor,
            r.capacity,
            r.status

        FROM rooms r

        WHERE r.bed_type = ?
        AND r.breakfast_included = ?
        AND r.status = 'Available'
        AND r.capacity >= ?

        AND NOT EXISTS (

            SELECT 1

            FROM bookings b

            WHERE b.room_no = r.room_no

            AND b.booking_status != 'Cancelled'

            AND b.check_in < ?
            AND b.check_out > ?
        )

        ORDER BY r.price_per_night ASC
    """

    with get_connection() as conn:

        rows = conn.execute(
            query,
            (
                bed_type,
                int(breakfast),
                guests,
                check_out,
                check_in
            )
        ).fetchall()

        return [dict(row) for row in rows]


# ==========================================
# 3. FIND CLOSEST ALTERNATIVES
# ==========================================

def find_alternatives(
    check_in,
    check_out,
    bed_type,
    breakfast,
    guests,
    limit=2
):
    """
    Suggests the closest available alternatives.

    Priority:
    1. Same bed, different breakfast preference.
    2. Different bed, same breakfast preference.
    3. Different bed and breakfast preference.

    Only returns the closest available rooms.
    """

    query = """
        SELECT
            r.room_no,
            r.room_type,
            r.bed_type,
            r.breakfast_included,
            r.price_per_night,
            r.floor,
            r.capacity,
            r.status

        FROM rooms r

        WHERE r.status = 'Available'
        AND r.capacity >= ?

        AND NOT EXISTS (

            SELECT 1

            FROM bookings b

            WHERE b.room_no = r.room_no

            AND b.booking_status != 'Cancelled'

            AND b.check_in < ?
            AND b.check_out > ?
        )
    """

    with get_connection() as conn:

        rows = conn.execute(
            query,
            (guests, check_out, check_in)
        ).fetchall()

        rooms = [dict(row) for row in rows]

    # Exclude exact matches because this function
    # is only for alternatives.
    alternatives = []

    for room in rooms:

        bed_mismatch = (
            room["bed_type"] != bed_type
        )

        breakfast_mismatch = (
            bool(room["breakfast_included"]) != breakfast
        )

        if not bed_mismatch and not breakfast_mismatch:
            continue

        # Bed preference is given higher priority.
        score = (
            2 * int(bed_mismatch)
            + int(breakfast_mismatch)
        )

        room["alternative_score"] = score

        room["difference"] = []

        if bed_mismatch:
            room["difference"].append(
                f"Different bed type: {room['bed_type']}"
            )

        if breakfast_mismatch:
            room["difference"].append(
                "Breakfast included"
                if room["breakfast_included"]
                else "Breakfast not included"
            )

        alternatives.append(room)

    # Closest match first, then lower price.
    alternatives.sort(
        key=lambda room: (
            room["alternative_score"],
            room["price_per_night"],
            room["room_no"]
        )
    )

    return alternatives[:limit]


# ==========================================
# 4. MAIN AVAILABILITY TOOL
# ==========================================

def check_room_availability(
    check_in: str,
    check_out: str,
    bed_type: str,
    breakfast: bool,
    guests: int
):
    # Keep your existing availability-checking logic here.
    pass
    """
    Main availability tool.

    Returns:
    - Exact room matches
    - Alternative rooms
    - No availability
    - Validation errors
    """

    # Step 1: Validate request.

    valid, message = validate_booking_request(
        check_in,
        check_out,
        bed_type,
        breakfast,
        guests
    )

    if not valid:

        return {
            "status": "invalid_request",
            "message": message,
            "exact_matches": [],
            "alternatives": []
        }

    bed_type = bed_type.strip().capitalize()

    # Step 2: Search exact matches.

    exact_matches = find_matching_rooms(
        check_in,
        check_out,
        bed_type,
        breakfast,
        guests
    )

    # Step 3: Exact match found.

    if exact_matches:

        return {
            "status": "exact_match",
            "message": "Matching rooms are available.",
            "exact_matches": exact_matches,
            "alternatives": []
        }

    # Step 4: Search alternatives.

    alternatives = find_alternatives(
        check_in,
        check_out,
        bed_type,
        breakfast,
        guests
    )

    if alternatives:

        return {
            "status": "alternatives_found",
            "message": "No exact match. Here are the closest alternatives.",
            "exact_matches": [],
            "alternatives": alternatives
        }

    # Step 5: No availability.

    return {
        "status": "unavailable",
        "message": "Sorry, no suitable rooms are available for these dates.",
        "exact_matches": [],
        "alternatives": []
    }


# ==========================================
# 5. RUN A SAMPLE TEST
# ==========================================

if __name__ == "__main__":

    result = check_room_availability(
        check_in="2026-12-10",
        check_out="2026-12-12",
        bed_type="Double",
        breakfast=True,
        guests=2
    )

    print("\nROOM AVAILABILITY RESULT")
    print("=" * 40)

    print("Status:", result["status"])
    print("Message:", result["message"])

    if result["exact_matches"]:

        print("\nEXACT MATCHES")

        for room in result["exact_matches"]:
            print(room)

    if result["alternatives"]:

        print("\nALTERNATIVE ROOMS")

        for room in result["alternatives"]:
            print(room)

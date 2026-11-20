
from tools import check_room_availability


def run_test(title, **request):

    print("\n" + "=" * 50)
    print(title)
    print("=" * 50)

    result = check_room_availability(**request)

    print("Status:", result["status"])
    print("Message:", result["message"])

    for room in result["exact_matches"]:
        print(
            f"Room {room['room_no']} | "
            f"{room['room_type']} | "
            f"{room['bed_type']} | "
            f"₹{room['price_per_night']}/night"
        )

    for room in result["alternatives"]:
        print(
            f"Alternative Room {room['room_no']} | "
            f"{room['bed_type']} | "
            f"₹{room['price_per_night']}/night | "
            f"{', '.join(room['difference'])}"
        )


# TEST A: Exact match

run_test(
    "TEST A - EXACT MATCH",
    check_in="2026-12-10",
    check_out="2026-12-12",
    bed_type="Double",
    breakfast=True,
    guests=2
)


# TEST B: Alternative suggestions

run_test(
    "TEST B - ALTERNATIVES",
    check_in="2026-12-10",
    check_out="2026-12-12",
    bed_type="Single",
    breakfast=True,
    guests=2
)


# TEST C: Invalid past date

run_test(
    "TEST C - INVALID DATE",
    check_in="2026-11-18",
    check_out="2026-11-20",
    bed_type="Double",
    breakfast=True,
    guests=2
)


# TEST D: No suitable rooms

run_test(
    "TEST D - NO AVAILABILITY",
    check_in="2026-12-10",
    check_out="2026-12-12",
    bed_type="Double",
    breakfast=True,
    guests=99
)

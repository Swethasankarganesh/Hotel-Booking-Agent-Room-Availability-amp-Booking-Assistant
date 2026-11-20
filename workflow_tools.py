
from booking import create_booking
from email_service import send_booking_confirmation


def finalize_room_booking(
    room_no: int,
    guest_name: str,
    guest_email: str,
    check_in: str,
    check_out: str,
    guests: int
):
    """
    Finalize a reservation and generate its confirmation email.
    Only call this after the guest explicitly confirms.
    """

    # Step 1: Create the booking
    booking = create_booking(
        room_no=room_no,
        guest_name=guest_name,
        guest_email=guest_email,
        check_in=check_in,
        check_out=check_out,
        guests=guests
    )

    # Step 2: Stop if booking failed
    if not booking["success"]:
        return booking

    # Step 3: Generate confirmation email
    email_result = send_booking_confirmation(booking)

    # Step 4: Return complete result
    booking["email_status"] = email_result["message"]

    return booking

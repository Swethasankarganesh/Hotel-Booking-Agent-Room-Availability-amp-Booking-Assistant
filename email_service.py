
import os
from datetime import datetime


def send_booking_confirmation(booking):
    """
    Generate a mock booking confirmation email
    and save it to a local log file.
    """

    if not booking or not booking.get("success"):
        return {
            "success": False,
            "message": "Cannot send confirmation for an unsuccessful booking."
        }

    email_content = f"""
========================================
       HOTEL BOOKING CONFIRMATION
========================================

Dear {booking['guest_name']},

Your hotel booking has been confirmed!

Booking ID: {booking['booking_id']}
Room Number: {booking['room_no']}
Room Type: {booking['room_type']}
Bed Type: {booking['bed_type']}

Check-in: {booking['check_in']}
Check-out: {booking['check_out']}
Number of Nights: {booking['nights']}
Number of Guests: {booking['guests']}

Price per Night: Rs. {booking['price_per_night']}
Total Amount: Rs. {booking['total_price']}

Breakfast Included: {booking['breakfast']}

Guest Email: {booking['guest_email']}

Thank you for choosing our hotel!

We look forward to welcoming you.

========================================
"""

    os.makedirs("email_logs", exist_ok=True)

    filename = (
        f"email_logs/booking_{booking['booking_id']}.txt"
    )

    with open(filename, "w", encoding="utf-8") as file:
        file.write(email_content)

    print(email_content)

    return {
        "success": True,
        "message": f"Mock confirmation email saved to {filename}"
    }

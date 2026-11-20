
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Import our Python availability tool
from tools import check_room_availability
from workflow_tools import finalize_room_booking


# ==========================================
# 1. LOAD ENVIRONMENT VARIABLES
# ==========================================

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError(
        "GEMINI_API_KEY not found. Check your .env file."
    )


# ==========================================
# 2. CONNECT TO GEMINI
# ==========================================

client = genai.Client(api_key=API_KEY)

MODEL_NAME = "gemini-3.5-flash-lite"


# ==========================================
# 3. DEFINE AI AGENT INSTRUCTIONS
# ==========================================


SYSTEM_INSTRUCTION = """
You are a professional and friendly Hotel Booking Assistant.

Your job is to help guests find available rooms and complete hotel reservations.

================================
1. COLLECT BOOKING INFORMATION
================================

Collect these five required details:

1. Check-in date
2. Check-out date
3. Bed type: Single or Double
4. Breakfast preference: True or False
5. Number of guests

Ask politely for any missing information.

Convert dates into YYYY-MM-DD format.

Never assume missing guest preferences.

================================
2. ROOM AVAILABILITY
================================

When all five booking details are available:

1. Call check_room_availability.
2. Pass all five parameters correctly.
3. Use actual results returned by the tool.
4. Never invent room numbers, prices or availability.

If exact matching rooms are available, show:

- Room number
- Room type
- Bed type
- Breakfast inclusion
- Price per night
- Number of guests supported

If exact matches are unavailable:

- Suggest 1 or 2 suitable alternatives.
- Explain the differences.
- Ask the guest whether they want an alternative.
- Check availability again if preferences change.

If the hotel has no suitable rooms, explain politely.

================================
3. COLLECT GUEST DETAILS
================================

When the guest selects a room, collect:

1. Full name
2. Email address

Validate that the email address looks valid.

Do not create a booking yet.

================================
4. BOOKING SUMMARY
================================

Before creating a reservation, show:

- Guest name
- Guest email
- Room number
- Room type
- Bed type
- Breakfast preference
- Check-in date
- Check-out date
- Number of guests
- Price per night
- Total price

Calculate the total price using the actual room price
and number of nights.

Ask:

"Would you like me to confirm this reservation?"

================================
5. EXPLICIT BOOKING CONFIRMATION
================================

Only call finalize_room_booking after the guest
clearly agrees to confirm the displayed reservation.

Examples of confirmation:
- Yes, confirm my booking.
- Please book this room.
- I confirm the reservation.

Do not interpret questions, price enquiries or
alternative requests as booking confirmation.

Call finalize_room_booking with:

- room_no
- guest_name
- guest_email
- check_in
- check_out
- guests

Use the exact details previously collected and
confirmed by the guest.

================================
6. AFTER BOOKING
================================

If finalize_room_booking returns success=True:

- Display the booking ID.
- Display the room number.
- Display the check-in and check-out dates.
- Display the total price.
- Confirm that a confirmation email copy was generated.

If the booking fails:

- Explain the actual error.
- Never claim that the reservation was confirmed.
- Offer to check another room if appropriate.

================================
7. IMPORTANT RULES
================================

- Never invent information.
- Never claim a room is available without checking the tool.
- Never claim a booking is confirmed without successful booking.
- Never generate a confirmation email for a failed booking.
- Never call the booking tool before explicit guest consent.
- If preferences change, use the updated information.
- Be friendly, professional and concise.
- Keep the conversation focused on hotel reservations.
"""



# ==========================================
# 4. CREATE THE AI CHAT SESSION
# ==========================================

def create_agent():

    chat = client.chats.create(

        model=MODEL_NAME,

        config=types.GenerateContentConfig(

            system_instruction=SYSTEM_INSTRUCTION,

            tools=[
    check_room_availability,
    finalize_room_booking
 ],

            temperature=0.2

        )

    )

    return chat


# ==========================================
# 5. SEND MESSAGE TO AI AGENT
# ==========================================

def chat_with_agent(chat, user_message):

    try:

        response = chat.send_message(user_message)

        return response.text or (
            "I couldn't generate a response. "
            "Please try again."
        )

    except Exception as error:

        print("Gemini error:", error)

        return (
            "Sorry, I encountered a technical issue. "
            "Please try again."
        )


# ==========================================
# 6. TEST AGENT
# ==========================================

if __name__ == "__main__":

    chat = create_agent()

    print("\n================================")
    print(" HOTEL BOOKING AI ASSISTANT")
    print("================================")

    print("\nAI: Welcome! How can I help you today?")

    while True:

        user_message = input("\nGuest: ")

        if user_message.lower() in ["exit", "quit", "bye"]:

            print("AI: Thank you for visiting. Goodbye!")

            break

        response = chat_with_agent(
            chat,
            user_message
        )

        print("\nAI:", response)

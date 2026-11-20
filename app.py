
import re
import uuid
from datetime import date, timedelta

import streamlit as st
from agent import create_agent, chat_with_agent

# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Stayora AI | Hotel Concierge",
    page_icon="🏨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------

defaults = {
    "messages": [],
    "chat": None,
    "theme": "Light",
    "sidebar_collapsed": False,
    "agent_error": None,
    "availability_checked": False,
    "conversations": {},
    "current_id": uuid.uuid4().hex,
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


def initialize_agent():
    try:
        st.session_state.chat = create_agent()
        st.session_state.agent_error = None
    except Exception as error:
        st.session_state.agent_error = str(error)
        st.session_state.chat = None


if st.session_state.chat is None and st.session_state.agent_error is None:
    initialize_agent()


# --------------------------------------------------
# CHAT HISTORY HELPERS
# --------------------------------------------------

def conversation_title(messages):
    for message in messages:
        if message["role"] == "user":
            text = " ".join(message["content"].split())
            return text if len(text) <= 30 else text[:30].rstrip() + "…"
    return "New conversation"


def save_current():
    """Store the live conversation in the history list."""
    if st.session_state.messages:
        st.session_state.conversations[st.session_state.current_id] = {
            "title": conversation_title(st.session_state.messages),
            "messages": st.session_state.messages,
            "chat": st.session_state.chat,
            "availability_checked": st.session_state.availability_checked,
        }


def start_new_conversation():
    save_current()
    st.session_state.current_id = uuid.uuid4().hex
    st.session_state.messages = []
    st.session_state.availability_checked = False
    st.session_state.agent_error = None
    st.session_state.chat = None
    initialize_agent()


def open_conversation(conversation_id):
    save_current()
    record = st.session_state.conversations[conversation_id]
    st.session_state.current_id = conversation_id
    st.session_state.messages = record["messages"]
    st.session_state.availability_checked = record["availability_checked"]
    st.session_state.agent_error = None
    st.session_state.chat = record["chat"]
    if st.session_state.chat is None:
        initialize_agent()


# --------------------------------------------------
# BOOKING QUESTIONS INSIDE THE AI REPLY
# When the assistant asks for the booking details, an input box appears
# directly below each question, and a "Check availability" button appears at
# the end of the same reply. Nothing is shown separately from the reply.
# --------------------------------------------------

QUESTION_KEYS = [
    ("check_in", ("check-in", "check in", "arrival")),
    ("check_out", ("check-out", "check out", "departure")),
    ("bed", ("bed type", "single or double")),
    ("breakfast", ("breakfast",)),
    ("guests", ("number of guests", "how many guests", "guests")),
]

LIST_LINE = re.compile(r"^\s*(?:\d+[.)]|[-*•])\s+")


def detected_questions(text):
    low = text.lower()
    return [
        key for key, words in QUESTION_KEYS
        if any(word in low for word in words)
    ]


def asks_for_booking_details(text):
    return len(detected_questions(text)) >= 3


def question_of_line(line):
    low = line.lower()
    for key, words in QUESTION_KEYS:
        if any(word in low for word in words):
            return key
    return None


def render_field(key, label):
    """One input box for one question. Returns the chosen value."""

    box, _ = st.columns([2, 3])

    with box:

        if key == "check_in":
            return st.date_input(
                label,
                value=date.today(),
                min_value=date.today(),
                format="YYYY-MM-DD",
                key="form_check_in",
                label_visibility="collapsed"
            )

        if key == "check_out":
            first_day = st.session_state.get("form_check_in", date.today())
            min_out = first_day + timedelta(days=1)

            if (
                "form_check_out" not in st.session_state
                or st.session_state.form_check_out < min_out
            ):
                st.session_state.form_check_out = min_out

            return st.date_input(
                label,
                min_value=min_out,
                format="YYYY-MM-DD",
                key="form_check_out",
                label_visibility="collapsed"
            )

        if key == "bed":
            return st.selectbox(
                label,
                ["Single", "Double"],
                key="form_bed_type",
                label_visibility="collapsed"
            )

        if key == "breakfast":
            return st.selectbox(
                label,
                ["Yes", "No"],
                key="form_breakfast",
                label_visibility="collapsed"
            )

        return st.number_input(
            label,
            min_value=1,
            max_value=10,
            value=2,
            step=1,
            key="form_guests",
            label_visibility="collapsed"
        )


FIELD_LABELS = {
    "check_in": "Check-in date (YYYY-MM-DD)",
    "check_out": "Check-out date (YYYY-MM-DD)",
    "bed": "Bed type",
    "breakfast": "Breakfast preference",
    "guests": "Number of guests",
}


def build_booking_message(values):
    parts = ["I want to book a room."]

    if "check_in" in values:
        parts.append(f"Check-in date: {values['check_in']:%Y-%m-%d}.")

    if "check_out" in values:
        parts.append(f"Check-out date: {values['check_out']:%Y-%m-%d}.")

    if "check_in" in values and "check_out" in values:
        nights = (values["check_out"] - values["check_in"]).days
        parts.append(f"Stay length: {nights} night{'s' if nights != 1 else ''}.")

    if "bed" in values:
        parts.append(f"Bed type: {values['bed']}.")

    if "guests" in values:
        parts.append(f"Number of guests: {values['guests']}.")

    if "breakfast" in values:
        parts.append(f"Breakfast: {values['breakfast']}.")

    parts.append("Please check availability and show me the options.")

    return " ".join(parts)


def render_reply_with_form(text):
    """Show the assistant reply with an input under each question."""

    values = {}

    for line in text.split("\n"):

        if not line.strip():
            continue

        # keep "1." from turning into a one-item list that restarts at 1
        st.markdown(re.sub(r"^(\s*)(\d+)\.\s", r"\1\2\\. ", line))

        if LIST_LINE.match(line):
            key = question_of_line(line)

            if key and key not in values:
                values[key] = render_field(key, FIELD_LABELS[key])

    # questions the assistant asked in plain sentences (not as list items)
    for key in detected_questions(text):
        if key not in values:
            st.markdown(f"**{FIELD_LABELS[key]}**")
            values[key] = render_field(key, FIELD_LABELS[key])

    if st.button(
        "🔎  Check availability",
        use_container_width=True,
        key="form_submit"
    ):
        st.session_state.availability_checked = True
        st.session_state.pending_prompt = build_booking_message(values)
        st.rerun()


def render_assistant_message(text, is_last):
    """Plain reply, or reply with the booking inputs inside it."""

    if (
        is_last
        and not st.session_state.availability_checked
        and st.session_state.chat is not None
        and asks_for_booking_details(text)
    ):
        render_reply_with_form(text)
    else:
        st.markdown(text)


# --------------------------------------------------
# THEME SETTINGS
# --------------------------------------------------

themes = {
    "Light": {
        "background": "#F7F8FA",
        "sidebar": "#FFFFFF",
        "surface": "#FFFFFF",
        "surface_alt": "#F1F3F5",
        "text": "#20242C",
        "muted": "#777F8C",
        "border": "#E7E9ED",
        "accent": "#477B70",
        "accent_hover": "#37675D",
        "input": "#FFFFFF",
        "shadow": "0 2px 12px rgba(20, 30, 40, 0.04)",
    },
    "Dark": {
        "background": "#171A1F",
        "sidebar": "#1D2229",
        "surface": "#222831",
        "surface_alt": "#2A313B",
        "text": "#F1F3F5",
        "muted": "#A2AAB5",
        "border": "#343D48",
        "accent": "#8BBDB0",
        "accent_hover": "#A4D0C4",
        "input": "#252C35",
        "shadow": "0 2px 14px rgba(0, 0, 0, 0.12)",
    },
}

theme = themes[st.session_state.theme]

# --------------------------------------------------
# CSS
# Plain CSS string avoids Python f-string brace errors.
# --------------------------------------------------

sidebar_width = 76 if st.session_state.sidebar_collapsed else 270

css = """
<style>

@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');

:root {
    --bg: BG;
    --sidebar: SIDEBAR;
    --surface: SURFACE;
    --surface-alt: SURFACE_ALT;
    --text: TEXT;
    --muted: MUTED;
    --border: BORDER;
    --accent: ACCENT;
    --accent-hover: ACCENT_HOVER;
    --input: INPUT;
    --shadow: SHADOW;
}

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

.stApp {
    background: var(--bg);
    color: var(--text);
}

/* Main workspace */

/* keep the last reply (and its button) clear of the chat input bar */
[data-testid="stMainBlockContainer"] {
    padding-bottom: 9rem !important;
}

section.main > div {
    padding-top: 1.6rem;
    padding-bottom: 7rem;
}

.block-container {
    max-width: 1050px;
    padding-left: 3rem;
    padding-right: 3rem;
}

/* Sidebar */

section[data-testid="stSidebar"] {
    background: var(--sidebar);
    border-right: 1px solid var(--border);
    width: SIDEBAR_WIDTHpx !important;
    min-width: SIDEBAR_WIDTHpx !important;
    max-width: SIDEBAR_WIDTHpx !important;
    transition: width 0.2s ease;
}

section[data-testid="stSidebar"] > div {
    width: SIDEBAR_WIDTHpx !important;
}

section[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
    gap: 0.75rem;
}

section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] label {
    color: var(--text);
}

/* Buttons */

.stButton > button {
    border-radius: 10px;
    border: 1px solid var(--border);
    background: var(--surface);
    color: var(--text);
    min-height: 42px;
    font-family: 'DM Sans', sans-serif;
    font-weight: 500;
    transition: all 0.2s ease;
}

.stButton > button:hover {
    border-color: var(--accent);
    color: var(--accent);
    background: var(--surface-alt);
}

/* Sidebar buttons */

section[data-testid="stSidebar"] .stButton > button {
    width: 100%;
    text-align: left;
    justify-content: flex-start;
}

/* Sidebar buttons (new conversation, chat history, delete): light surface,
   readable text. !important so Streamlit's own dark button style cannot win. */

[data-testid="stSidebarUserContent"] button,
[data-testid="stSidebarUserContent"] [data-testid^="stBaseButton"] {
    background: var(--surface) !important;
    background-color: var(--surface) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    box-shadow: none !important;
}

[data-testid="stSidebarUserContent"] button p,
[data-testid="stSidebarUserContent"] button span,
[data-testid="stSidebarUserContent"] button div {
    color: var(--text) !important;
    -webkit-text-fill-color: var(--text) !important;
    margin: 0;
    font-size: 13px;
    line-height: 1.4;
    text-align: left;
}

[data-testid="stSidebarUserContent"] button:hover,
[data-testid="stSidebarUserContent"] button:focus,
[data-testid="stSidebarUserContent"] button:active {
    background: var(--bg) !important;
    background-color: var(--bg) !important;
    border-color: var(--accent) !important;
}

[data-testid="stSidebarUserContent"] button:hover p,
[data-testid="stSidebarUserContent"] button:focus p,
[data-testid="stSidebarUserContent"] button:active p {
    color: var(--accent) !important;
    -webkit-text-fill-color: var(--accent) !important;
}

/* Brand */

.brand {
    display: flex;
    align-items: center;
    gap: 11px;
    padding: 8px 2px 20px 2px;
}

.brand-icon {
    width: 42px;
    height: 42px;
    min-width: 42px;
    border-radius: 12px;
    background: #477B70 !important;
    color: #FFFFFF !important;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 21px;
    border: 1px solid #477B70;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12);
}
.brand-name {
    font-family: 'Manrope', sans-serif;
    font-size: 20px;
    font-weight: 800;
    color: var(--text);
    letter-spacing: -0.8px;
}

.brand-caption {
    font-size: 10px;
    color: var(--muted);
    letter-spacing: 1.3px;
    margin-top: -2px;
}

/* Sidebar labels */

.sidebar-section {
    color: var(--muted);
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
    padding: 15px 3px 5px 3px;
}

.sidebar-note {
    color: var(--muted);
    font-size: 12px;
    line-height: 1.6;
    padding: 10px 3px;
}

/* Hero */

.hero {
    text-align: center;
    padding: 75px 10px 32px 10px;
}

.hero-eyebrow {
    color: var(--accent);
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-bottom: 18px;
}

.hero-title {
    font-family: 'Manrope', sans-serif;
    font-size: clamp(34px, 5vw, 48px);
    line-height: 1.18;
    letter-spacing: -2px;
    font-weight: 800;
    color: var(--text);
    margin: 0;
}

.hero-subtitle {
    color: var(--muted);
    font-size: 15px;
    line-height: 1.8;
    max-width: 550px;
    margin: 15px auto 0 auto;
}

/* Feature cards */

.feature-card {
    height: 150px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 15px;
    padding: 19px;
    box-shadow: var(--shadow);
    transition: transform 0.2s ease, border-color 0.2s ease;
}

.feature-card:hover {
    transform: translateY(-3px);
    border-color: var(--accent);
}

.feature-icon {
    font-size: 22px;
    margin-bottom: 13px;
}

.feature-title {
    color: var(--text);
    font-weight: 700;
    font-size: 14px;
    margin-bottom: 6px;
}

.feature-description {
    color: var(--muted);
    font-size: 12px;
    line-height: 1.5;
}

/* Chat messages */

[data-testid="stChatMessage"] {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 15px;
    padding: 16px 18px;
    margin-bottom: 15px;
}

/* TEXT COLOR FIX: message text (user + assistant) */

[data-testid="stChatMessage"] p,
[data-testid="stChatMessage"] li,
[data-testid="stChatMessage"] span,
[data-testid="stChatMessage"] strong,
[data-testid="stChatMessage"] em,
[data-testid="stChatMessage"] h1,
[data-testid="stChatMessage"] h2,
[data-testid="stChatMessage"] h3,
[data-testid="stChatMessage"] h4,
[data-testid="stChatMessage"] td,
[data-testid="stChatMessage"] th,
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] {
    color: var(--text) !important;
    -webkit-text-fill-color: var(--text) !important;
}

/* Chat input */

[data-testid="stBottom"] {
    background: var(--bg) !important;
}

[data-testid="stBottom"] > div {
    background: var(--bg) !important;
}

[data-testid="stChatInput"] {
    background: var(--input) !important;
    border: 1px solid var(--border) !important;
    border-radius: 16px !important;
    box-shadow: var(--shadow) !important;
}

[data-testid="stChatInput"] > div {
    background: var(--input) !important;
    border-radius: 16px !important;
}

[data-testid="stChatInput"] textarea {
    color: var(--text) !important;
    -webkit-text-fill-color: var(--text) !important;
    background: var(--input) !important;
    caret-color: var(--accent) !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 15px !important;
}

[data-testid="stChatInput"] textarea::placeholder {
    color: var(--muted) !important;
    opacity: 1 !important;
}

/* Booking form: calendar, dropdowns, guest counter */

[data-testid="stWidgetLabel"] p {
    color: var(--text) !important;
    font-size: 12px;
    font-weight: 600;
}

[data-testid="stDateInput"] [data-baseweb="input"],
[data-testid="stDateInput"] [data-baseweb="base-input"],
[data-testid="stNumberInput"] [data-baseweb="input"],
[data-testid="stNumberInput"] [data-baseweb="base-input"],
[data-testid="stSelectbox"] [data-baseweb="select"] > div {
    background: var(--input) !important;
    border-color: var(--border) !important;
    border-radius: 10px !important;
}

[data-testid="stDateInput"] input,
[data-testid="stNumberInput"] input,
[data-testid="stSelectbox"] [data-baseweb="select"] div,
[data-testid="stSelectbox"] [data-baseweb="select"] span {
    color: var(--text) !important;
    -webkit-text-fill-color: var(--text) !important;
}

[data-testid="stNumberInput"] button {
    background: var(--surface) !important;
    color: var(--text) !important;
    border-color: var(--border) !important;
}

[data-testid="stSelectbox"] svg,
[data-testid="stDateInput"] svg {
    fill: var(--muted) !important;
}

/* Dividers and captions */

hr {
    border-color: var(--border) !important;
}

[data-testid="stCaptionContainer"] {
    color: var(--muted);
}

/* Responsive */

@media (max-width: 768px) {
    .block-container {
        padding-left: 1rem;
        padding-right: 1rem;
    }

    .hero {
        padding-top: 35px;
    }

    .hero-title {
        font-size: 34px;
    }
}

</style>
"""

replacements = {
    "BG": theme["background"],
    "SIDEBAR": theme["sidebar"],
    "SURFACE": theme["surface"],
    "SURFACE_ALT": theme["surface_alt"],
    "TEXT": theme["text"],
    "MUTED": theme["muted"],
    "BORDER": theme["border"],
    "ACCENT": theme["accent"],
    "ACCENT_HOVER": theme["accent_hover"],
    "INPUT": theme["input"],
    "SHADOW": theme["shadow"],
    "SIDEBAR_WIDTH": str(sidebar_width),
}

for old, new in replacements.items():
    css = css.replace(old, new)

st.markdown(css, unsafe_allow_html=True)



# --------------------------------------------------
# SIDEBAR - FIXED EXPANDED
# --------------------------------------------------

with st.sidebar:

    st.markdown(
        """
        <div class="brand">
            <div class="brand-icon">🏨</div>
            <div>
                <div class="brand-name">Stayora</div>
                <div class="brand-caption">AI HOTEL CONCIERGE</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    if st.button("＋  New conversation", key="new_expanded"):
        start_new_conversation()
        st.rerun()

    # Filled at the end of the script so the current chat shows up immediately
    history_slot = st.container()

    st.markdown(
        '<div class="sidebar-section">Appearance</div>',
        unsafe_allow_html=True
    )

    selected_theme = st.radio(
        "Theme",
        ["Light", "Dark"],
        index=0 if st.session_state.theme == "Light" else 1,
        horizontal=True,
        label_visibility="collapsed",
        key="theme_radio"
    )

    if selected_theme != st.session_state.theme:
        st.session_state.theme = selected_theme
        st.rerun()

    st.markdown(
        '<div class="sidebar-section">Assistant status</div>',
        unsafe_allow_html=True
    )

    if st.session_state.chat is not None:
        st.success("AI assistant connected")
    else:
        st.warning("AI assistant unavailable")

    st.markdown("---")

    st.markdown(
        """
        <div class="sidebar-note">
            Your personal hotel booking assistant.<br>
            Find rooms, compare options and book your stay.
        </div>
        """,
        unsafe_allow_html=True
    )


# --------------------------------------------------
# MAIN WORKSPACE
# --------------------------------------------------

st.markdown(
    """
    <div style="display:flex;justify-content:space-between;align-items:center;">
        <div style="color:var(--muted);font-size:12px;font-weight:600;letter-spacing:1px;">
            YOUR PERSONAL AI CONCIERGE
        </div>
        <div style="font-size:12px;color:var(--muted);">
            ✦ Powered by AI
        </div>
    </div>
    """,
    unsafe_allow_html=True
)


# --------------------------------------------------
# ERROR HANDLING
# --------------------------------------------------

if st.session_state.agent_error:
    st.error(
        "Unable to initialize the AI assistant. "
        "Please check your Gemini configuration and try again."
    )


# --------------------------------------------------
# READ THE INPUT FIRST
# Doing this before the history is drawn lets the history know whether a new
# message is being sent, so the booking inputs are never drawn twice.
# --------------------------------------------------

pending_prompt = st.session_state.pop("pending_prompt", None)

user_input = st.chat_input(
    "Message Stayora AI...",
    key="chat_input"
)

prompt = pending_prompt or user_input


# --------------------------------------------------
# WELCOME SCREEN
# --------------------------------------------------

if not st.session_state.messages:

    st.markdown(
        """
        <div class="hero">
            <div class="hero-eyebrow">✦ YOUR STAY, SIMPLIFIED</div>
            <h1 class="hero-title">How can I help<br>you today?</h1>
            <div class="hero-subtitle">
                Discover your perfect stay. I'll help you find available
                rooms, compare options and complete your booking.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns(3, gap="medium")

    with col1:
        st.markdown(
            """
            <div class="feature-card">
                <div class="feature-icon">🛏️</div>
                <div class="feature-title">Find your room</div>
                <div class="feature-description">
                    Explore available rooms based on your preferences.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            """
            <div class="feature-card">
                <div class="feature-icon">✨</div>
                <div class="feature-title">Compare options</div>
                <div class="feature-description">
                    Discover room options, prices and included amenities.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col3:
        st.markdown(
            """
            <div class="feature-card">
                <div class="feature-icon">🔐</div>
                <div class="feature-title">Book securely</div>
                <div class="feature-description">
                    Review your booking details before confirming.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown(
        '<div style="height:32px;"></div>'
        '<div style="font-size:13px;font-weight:700;color:var(--text);margin-bottom:12px;">Try asking</div>',
        unsafe_allow_html=True
    )

    prompt_col1, prompt_col2 = st.columns(2, gap="small")

    with prompt_col1:
        if st.button(
            "🛏️  Find available rooms",
            use_container_width=True,
            key="prompt_rooms"
        ):
            st.session_state.pending_prompt = (
                "I want to check available rooms. Help me with the booking details."
            )
            st.rerun()

        if st.button(
            "☕  Show breakfast options",
            use_container_width=True,
            key="prompt_breakfast"
        ):
            st.session_state.pending_prompt = (
                "Show me the room options that include breakfast."
            )
            st.rerun()

    with prompt_col2:
        if st.button(
            "💰  Check room prices",
            use_container_width=True,
            key="prompt_prices"
        ):
            st.session_state.pending_prompt = (
                "Can you explain the available room prices?"
            )
            st.rerun()

        if st.button(
            "📅  Help me plan my stay",
            use_container_width=True,
            key="prompt_plan"
        ):
            st.session_state.pending_prompt = (
                "Help me plan a hotel stay and find a suitable room."
            )
            st.rerun()


# --------------------------------------------------
# CHAT HISTORY
# --------------------------------------------------

else:

    st.markdown(
        '<div style="height:25px;"></div>',
        unsafe_allow_html=True
    )

    last_index = len(st.session_state.messages) - 1

    for index, message in enumerate(st.session_state.messages):

        with st.chat_message(message["role"]):

            if message["role"] == "assistant":
                render_assistant_message(
                    message["content"],
                    is_last=(index == last_index and not prompt)
                )
            else:
                st.markdown(message["content"])


# --------------------------------------------------
# CHAT INPUT AND AGENT RESPONSE
# (the input itself is read earlier, before the chat history is drawn)
# --------------------------------------------------

if prompt:

    if st.session_state.chat is None:
        st.error("The AI assistant is not connected. Please check your configuration.")

    else:

        st.session_state.messages.append({
            "role": "user",
            "content": prompt
        })

        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):

            with st.spinner("Stayora is thinking..."):

                try:
                    response = chat_with_agent(
                        st.session_state.chat,
                        prompt
                    )

                    answer = (
                        response.text
                        if hasattr(response, "text")
                        else str(response)
                    )

                    render_assistant_message(answer, is_last=True)

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": answer
                    })

                except Exception as error:

                       st.error("Gemini Backend Error")

                       st.exception(error)

                       st.session_state.agent_error = str(error)


# --------------------------------------------------
# SIDEBAR CHAT HISTORY (rendered after the reply so it is always current)
# --------------------------------------------------

save_current()

with history_slot:

    st.markdown(
        '<div class="sidebar-section">Chat history</div>',
        unsafe_allow_html=True
    )

    conversations = st.session_state.conversations

    if not conversations:
        st.markdown(
            '<div class="sidebar-note">No saved conversations yet.</div>',
            unsafe_allow_html=True
        )

    for conversation_id in list(conversations.keys())[::-1][:20]:

        record = conversations[conversation_id]
        is_current = conversation_id == st.session_state.current_id

        open_col, delete_col = st.columns([5, 1], gap="small")

        with open_col:
            if st.button(
                ("●  " if is_current else "💬  ") + record["title"],
                key=f"hist_open_{conversation_id}",
                use_container_width=True,
                help=f"{len(record['messages'])} messages"
            ):
                if not is_current:
                    open_conversation(conversation_id)
                    st.rerun()

        with delete_col:
            if st.button(
                "🗑",
                key=f"hist_del_{conversation_id}",
                help="Delete this conversation"
            ):
                if is_current:
                    st.session_state.messages = []
                    del conversations[conversation_id]
                    start_new_conversation()
                else:
                    del conversations[conversation_id]
                st.rerun()


# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.markdown(
    """
    <div style="
        text-align:center;
        color:var(--muted);
        font-size:11px;
        padding:25px 0 5px 0;
    ">
        Stayora AI · Your personal hotel concierge
    </div>
    """,
    unsafe_allow_html=True
)

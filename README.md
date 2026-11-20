
# AI Hotel Booking Assistant

An AI-powered conversational hotel booking application built using Python, Streamlit, Google Gemini API and SQLite.

## Features

- Conversational hotel booking assistant
- Check-in and check-out date validation
- Single and double bed preferences
- Breakfast preference selection
- Real-time room availability checks against SQLite
- Alternative room suggestions
- Guest information collection
- Booking summary and explicit confirmation
- Automatic booking price calculation
- SQLite reservation storage
- Mock booking confirmation email generation
- Error handling and booking validation

## Technology Stack

- Python
- Streamlit
- Google Gemini API
- SQLite
- Google Gen AI Python SDK

## Project Structure

```text
hotel-booking-agent/
├── app.py
├── agent.py
├── database.py
├── tools.py
├── booking.py
├── workflow_tools.py
├── email_service.py
├── requirements.txt
├── README.md
└── .gitignore
```

## Installation

Clone the repository:

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd hotel-booking-agent
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate on Windows Git Bash:

```bash
source .venv/Scripts/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## API Configuration

Create a `.env` file in the project root:

```text
GEMINI_API_KEY=your_gemini_api_key
```

Never upload your API key to GitHub.

## Run the Application

```bash
python -m streamlit run app.py
```

Open:

http://localhost:8501

## Database

The project uses SQLite to store room and reservation records.

The database should be initialized using the project's database initialization function.

## Email Confirmation

The current implementation generates a mock confirmation email and saves it locally in the email_logs folder. It does not send an actual email.

## Security

- API keys are stored in environment variables.
- Local database files and generated email logs are excluded from Git.
- Do not commit real guest information.

## Future Improvements

- Actual email delivery
- Persistent cloud database
- Cloud deployment
- Improved room recommendation interface

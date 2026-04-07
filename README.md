# Internal Legal Request System

This project provides a simple internal legal request intake form built with Streamlit. Requests are stored locally in a CSV file and any uploaded files are saved to a local folder. An email notification can be sent to the legal team via SMTP.

## Features
- Department dropdown
- Free-text request field (1,000 characters max)
- Multiple file uploads
- Name + email fields
- CSV storage for requests
- Email notification via SMTP
- Confirmation message on submission

## Setup

1. Create a virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Configure SMTP (optional):

```bash
export SMTP_HOST="smtp.example.com"
export SMTP_PORT="587"
export SMTP_USER="smtp-user"
export SMTP_PASSWORD="smtp-password"
export SMTP_USE_TLS="true"
export LEGAL_EMAIL="legal@company.com"
export FROM_EMAIL="no-reply@company.com"
```

3. Run the app:

```bash
streamlit run app.py
```

## Data Storage
- Requests are saved to `data/requests.csv`.
- Uploaded files are stored in `uploads/<request_id>/`.

If SMTP is not configured, the request is still stored and the app will display a warning.

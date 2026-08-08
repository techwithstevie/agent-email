# Agent Email 📧

A lightweight Flask-based email automation assistant that uses Ollama-powered AI to generate, analyze, summarize, and send emails with smart templates and scheduling support.

## 🚀 What it does

- Generate professional email content from a recipient, context, and tone
- Send emails via SMTP with optional attachments
- Fetch unread emails and thread summaries via IMAP
- Analyze incoming messages for priority, action, and summary
- Summarize individual emails or entire threads
- Schedule outgoing email delivery for future send times

## 🧩 Key Components

- `app/__init__.py`: Flask app routes and API endpoints
- `app/agents/email_agent.py`: AI-powered email generation and analysis using Ollama
- `app/services/email_service.py`: SMTP/IMAP email operations and scheduled email handling
- `app/services/template_service.py`: email template loading and rendering
- `app/services/analytics_service.py`: tracking usage and email activity
- `app/utils/validation.py`: input validation logic
- `app/templates/index.html`: frontend interface
- `app/static/`: CSS and JavaScript assets

## ⚙️ Requirements

- Python 3.11+ (recommended)
- SMTP credentials for sending email
- IMAP credentials for reading email
- Ollama running locally or accessible via `OLLAMA_BASE_URL`

## 📦 Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 🔧 Configuration

Create a `.env` file in the project root with the following values:

```env
FLASK_APP=app
FLASK_DEBUG=1
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-smtp-user@example.com
SMTP_PASSWORD=your-smtp-password
IMAP_HOST=imap.gmail.com
IMAP_USER=your-imap-user@example.com
IMAP_PASSWORD=your-imap-password
OLLAMA_BASE_URL=http://localhost:11434
MODEL_NAME=llama3.2
```

> Note: Replace the placeholder values with your actual credentials. Keep secrets safe and never commit them to source control.

## ▶️ Run the app

```bash
export FLASK_APP=app
export FLASK_DEBUG=1
flask run
```

Then open `http://127.0.0.1:5000` in your browser.

## 🧪 API Endpoints

- `POST /api/generate-email`
  - Inputs: `recipient`, `context`, `tone`
  - Returns generated email body
- `POST /api/send-email`
  - Inputs: `to`, `subject`, `body`, `attachments`, `category`, `template_id`
- `GET /api/unread-emails`
  - Query: `limit`
- `GET /api/email-threads`
  - Query: `limit`
- `GET /api/thread-conversation/<thread_id>`
  - Query: `limit`
- `POST /api/analyze-email`
  - Inputs: `content`
- `POST /api/summarize-email`
  - Inputs: `content`, `max_length`
- `POST /api/summarize-thread`
  - Inputs: `thread_content`
- `POST /api/schedule-email`
  - Inputs: `to`, `subject`, `body`, `scheduled_time`, `attachments`

## 🧾 Email Templates

The project includes reusable JSON templates:

- `app/email_templates/follow_up.json`
- `app/email_templates/meeting_request.json`
- `app/email_templates/welcome.json`

These templates can be used for rapid email generation and to keep messaging consistent.

## ✅ Validation & Safety

The app validates critical fields before taking action:

- email address format
- subject length
- body content presence
- valid category values
- attachment path types
- request payload structure

## 💡 Tips

- Run Ollama locally and verify the model name in `.env`
- Use a dedicated email account for testing
- Keep `FLASK_DEBUG` disabled in production

## 📚 Notes

This project is designed as a development-ready email automation assistant. It is not a production-ready email client until credentials, security, and deployment settings are hardened.

## 📝 License

MIT License

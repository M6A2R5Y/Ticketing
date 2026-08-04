# FlowDesk — Django Ticketing System & Chatbot

FlowDesk is a mini Zendesk-style ticketing system built with Django. It features a modern, responsive user interface styled with vanilla CSS, roles for Customers and Support Agents, ticket state tracking, internal notes, activity log history, and an interactive support chatbot widget.

## Key Features

- **Customer Support Portal**: Customers can log in, submit tickets, view support logs, and post public comments.
- **Agent Console**: Agents (staff users) can view all tickets, filter by status or priority, update ticket metadata (assignee, status, priority), and leave staff-only internal notes.
- **Activity Log & History**: Every property modification (status, priority, assignment changes) is logged and displayed on a visual timeline.
- **FlowBot Assistant**: A chatbot widget powered by a lightweight parser, enabling users to:
  - Check ticket statuses directly (e.g. `status of ticket #5`).
  - Draft and submit tickets asynchronously using a short syntax (e.g. `ticket: Login Issue | Cannot access account`).
  - Request list of their tickets.
- **Production-Ready**: Configured for Render deployment out of the box with PostgreSQL integration, Gunicorn, and WhiteNoise static asset serving.

---

## Technology Stack

- **Backend**: Python 3.11+ / Django 5.x
- **Database**: SQLite (Local Dev) / PostgreSQL (Production, Render)
- **Frontend**: Django Templates & Vanilla CSS (Outfit Font, responsive layout, glassmorphic accents)
- **Asset Serving**: WhiteNoise
- **Deployment**: Render Blueprint (`render.yaml`)

---

## Local Setup Instructions

Follow these step-by-step instructions to get the application running locally:

### 1. Initialize Virtual Environment
Initialize a Python virtual environment and activate it:
```bash
# Create virtual environment
python -m venv .venv

# Activate on Windows Powershell:
.venv\Scripts\Activate.ps1
# Activate on Linux/macOS:
source .venv/bin/activate
```

### 2. Install Dependencies
Install the required packages:
```bash
pip install -r requirements.txt
```

### 3. Generate & Run Database Migrations
Run the schema migrations to initialize the SQLite database:
```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Create an Agent/Superuser Account
To access the Agent Console and the standard Django admin page, create a superuser/staff member:
```bash
python manage.py createsuperuser
```
Follow the prompts to enter a username, email, and password. This user will have `is_staff` privileges, enabling the Agent View dashboard and the ability to update tickets and add internal notes.

### 5. Start the Development Server
Run the local development server:
```bash
python manage.py runserver
```
Visit the application in your browser at `http://127.0.0.1:8000/`.

---

## Using the Chatbot (FlowBot)

Logged-in users will see a floating chat icon in the bottom-right corner of their dashboard. Click it to open the assistant panel.

### Commands:
1. **Submit Ticket**: Enter a message in the format `ticket: Title | Description`. FlowBot will create the ticket instantly and return the ID.
2. **Check Status**: Type `status #1` or `status of ticket #1` to get a live status report.
3. **List Tickets**: Type `list` or `my tickets` to view your 5 most recent tickets.
4. **Greet**: Type `hello` or `hi` to get started.

---

## Deploying to Render

This repository is pre-configured with a Render blueprint. To deploy:

1. Push your code to a GitHub repository.
2. Connect your GitHub account to Render.
3. In the Render Dashboard, click **New +** and select **Blueprint**.
4. Select this repository and click **Apply**.
5. Render will automatically spin up:
   - A PostgreSQL database (`ticketing_db`)
   - A Web Service (`ticketing-system`) running the production build using Gunicorn.
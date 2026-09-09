# Expense Tracking System

A personal expense tracker built with React, Flask, and SQLite. I created this project to practice building a full-stack application, connecting a frontend to a REST API, and working with a relational database.

The application lets users record expenses, organize them by category, filter transactions, and review spending summaries. It runs locally and does not require an account or an external service.

## Features

* Add, view, edit, and delete expenses
* Record an amount, date, category, description, and optional notes
* Filter expenses by category and date range
* View total spending, expense count, and average expense
* Review spending totals by category
* Validate expense data before saving
* Store transactions in SQLite
* Responsive interface for desktop and smaller screens

## Tech Stack

| Area     | Technology                   |
| -------- | ---------------------------- |
| Frontend | React, Vite, JavaScript, CSS |
| Backend  | Python, Flask                |
| Database | SQLite                       |
| API      | REST, JSON                   |
| Testing  | Python unittest              |

## How It Works

The React frontend sends HTTP requests to the Flask API. Flask handles the requests and uses a repository layer to read and write expense data in SQLite.

```text
React frontend
      |
      | HTTP / JSON
      v
Flask REST API
      |
      v
Repository and validation
      |
      v
SQLite database
```

The database stores expenses and categories in related tables. The backend uses parameterized SQL queries and validates incoming data before saving changes.

## Project Structure

```text
expense-tracking-system/
├── backend/
│   ├── app.py
│   ├── database.py
│   ├── repository.py
│   ├── seed.py
│   ├── requirements.txt
│   └── tests/
│       └── test_repository.py
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── package-lock.json
│   └── src/
│       ├── api.js
│       ├── main.js
│       └── styles.css
├── .gitignore
└── README.md
```

## Run Locally

You will need Python 3.11 or newer and Node.js with npm installed.

### 1. Start the backend

Open a terminal in the project folder:

```bash
cd backend
python -m venv .venv
```

On Windows PowerShell, install the dependencies without activating the virtual environment:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Start Flask:

```powershell
.\.venv\Scripts\python.exe -m flask --app app run --debug
```

The API should be available at `http://127.0.0.1:5000`.

For macOS or Linux, activate the environment with `source .venv/bin/activate`, install the requirements, and run the same Flask command.

### 2. Start the frontend

Open a second terminal and leave Flask running.

```bash
cd frontend
npm install
npm run dev
```

Open the local URL printed by Vite, normally `http://localhost:5173`.

On Windows PowerShell, if npm is blocked by the execution policy, use `npm.cmd install` and `npm.cmd run dev` instead.

### Optional sample data

From the backend folder, run:

```powershell
.\.venv\Scripts\python.exe seed.py
```

This adds sample expenses for testing the interface.

## API Endpoints

| Method | Endpoint            | Description               |
| ------ | ------------------- | ------------------------- |
| GET    | `/api/health`       | Check API status          |
| GET    | `/api/categories`   | List available categories |
| GET    | `/api/expenses`     | List and filter expenses  |
| POST   | `/api/expenses`     | Create an expense         |
| GET    | `/api/expenses/:id` | Get a single expense      |
| PUT    | `/api/expenses/:id` | Update an expense         |
| DELETE | `/api/expenses/:id` | Delete an expense         |
| GET    | `/api/summary`      | Get spending summaries    |

The expense list supports optional `category_id`, `start_date`, and `end_date` query parameters.

## Testing

The repository tests cover database initialization, CRUD operations, filtering, summaries, validation, and missing records.

From the backend folder, run:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

The application has also been run locally with the React frontend and Flask backend.

## What I Learned

This project helped me practice connecting a React interface to a Python backend, designing REST endpoints, working with SQLite relationships, and separating database logic from route handling. I also worked through local environment setup, dependency installation, and debugging the frontend-to-backend workflow.

## Limitations

This is a local portfolio project. It does not include user authentication, banking integrations, or cloud deployment. The current version is intended for learning and personal expense tracking rather than production financial use.

## Author

**Noah Mengesha**

[GitHub](https://github.com/Noah-Mengesha) | [LinkedIn](https://www.linkedin.com/in/noah-mengesha-63915b265/)

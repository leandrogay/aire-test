# Project Name

A full-stack app with a Next.js frontend and a FastAPI backend for data processing.

## Tech Stack

- **Frontend:** Next.js, JavaScript, React, Tailwind CSS
- **Backend:** Python, FastAPI, pandas, openpyxl

## Prerequisites

Install these before doing anything else:

- **Python 3.11+** — [python.org/downloads](https://www.python.org/downloads/)
- **Node.js 18+ and npm** — [nodejs.org](https://nodejs.org/)
- **Git**

Check your versions:

```bash
python --version
node --version
npm --version
git --version
```

> **Windows note:** if `pip` isn't recognized after installing Python, use `python -m pip` instead, or add your Python Scripts folder to PATH.

## First-Time Setup

Clone the repo, then set up each side separately.

### 1. Backend setup

```bash
cd backend
python -m venv venv
```

Activate the virtual environment:

```bash
# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

Install dependencies:

```bash
pip install fastapi uvicorn pandas openpyxl python-multipart
```

### 2. Frontend setup

```bash
cd frontend
npm install
```

### 3. Environment variables

Create `frontend/.env.local`:

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Running the Servers

You need two terminals open at the same time, one per server.

**Terminal 1 — Backend:**

```bash
cd backend
venv\Scripts\activate   # or: source venv/bin/activate
uvicorn app.main:app --reload
```

Runs at [http://localhost:8000](http://localhost:8000)

**Terminal 2 — Frontend:**

```bash
cd frontend
npm run dev
```

Runs at [http://localhost:3000](http://localhost:3000)

## Project Structure

```
my-project/
├── backend/
│   ├── venv/
│   ├── app/
│   │   └── main.py
│   └── requirements.txt
├── frontend/
│   ├── app/
│   ├── public/
│   └── package.json
├── .gitignore
└── README.md
```

## Notes

- CORS is enabled on the backend for `http://localhost:3000`. If you deploy the frontend elsewhere, add that URL to the `allow_origins` list in `backend/app/main.py`.
- Don't commit `venv/`, `node_modules/`, or any `.env` files — they're already covered in `.gitignore`.

# SupportLens

A minimal AI-powered customer support analytics tool. Users chat with an LLM-based support agent, and every interaction is classified, stored, and visualized on a dashboard.

![Stack](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)
![Stack](https://img.shields.io/badge/React-61DAFB?style=flat&logo=react&logoColor=black)
![Stack](https://img.shields.io/badge/SQLite-003B57?style=flat&logo=sqlite&logoColor=white)
![Stack](https://img.shields.io/badge/Groq-000?style=flat&logoColor=white)

## Features

- **Chat Interface** — Send messages to an AI support agent powered by Groq (Llama 3.1)
- **Auto-Classification** — Each interaction is classified into one of 5 categories via a second LLM call:
  - Billing, Refund, Account Access, Cancellation, General Inquiry
- **Trace Storage** — Every interaction is saved with timestamp, response time, and category
- **Analytics Dashboard** — View totals, category breakdown with percentages, and average response time
- **Category Filtering** — Filter traces by category
- **Expandable Rows** — Click any trace to see the full bot response

## Tech Stack

| Layer    | Technology                        |
|----------|-----------------------------------|
| Backend  | Python, FastAPI, SQLAlchemy, SQLite |
| Frontend | React (Vite), Axios, React Router |
| LLM      | Groq API (Llama 3.1 8B Instant)  |

## Setup Instructions

### Prerequisites

- Python 3.11+
- Node.js 18+
- A [Groq API key](https://console.groq.com/) (free tier)

### 1. Clone the repository

```bash
git clone https://github.com/Abeehimr/SupportLens.git
cd SupportLens
```

### 2. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**Seed the database** (optional — inserts 20 sample traces):

```bash
python seed.py
```

**Start the backend:**

```bash
GROQ_API_KEY=your_api_key_here uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`.

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

The app will be available at `http://localhost:5173`.

## API Endpoints

| Method | Endpoint     | Description                              |
|--------|-------------|------------------------------------------|
| GET    | `/health`   | Health check                             |
| POST   | `/chat`     | Send a message, get LLM response + classification |
| GET    | `/traces`   | List all traces (optional `?category=` filter) |
| GET    | `/analytics` | Get totals, percentages, avg response time |

### Example: POST /chat

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "I want a refund for my last payment"}'
```

```json
{
  "id": "uuid-here",
  "bot_response": "I can help process your refund...",
  "category": "Refund",
  "response_time_ms": 312
}
```

## Project Structure

```
SupportLens/
├── backend/
│   ├── main.py              # FastAPI app (all endpoints + models)
│   ├── requirements.txt     # Python dependencies
│   └── seed.py              # Seed script (20 sample traces)
├── frontend/
│   ├── src/
│   │   ├── main.jsx         # App entry + routing
│   │   ├── Chat.jsx         # Chat page component
│   │   ├── Dashboard.jsx    # Dashboard page component
│   │   └── index.css        # Global styles (dark theme)
│   ├── package.json
│   └── vite.config.js
├── .gitignore
└── README.md
```

## Data Model

**Trace:**

| Field            | Type     | Description                 |
|------------------|----------|-----------------------------|
| id               | UUID     | Unique identifier           |
| user_message     | string   | User's input message        |
| bot_response     | string   | LLM-generated response      |
| category         | string   | Auto-classified category    |
| timestamp        | datetime | When the trace was created  |
| response_time_ms | int      | LLM response latency in ms  |

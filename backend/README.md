# SupportSphere — RAG-Based Agentic AI Smart Service Desk

A full-stack AI-powered customer support portal with automated ticket classification, department-based routing, agent workload management, and a RAG chatbot backed by a private knowledge base.

---

## Features

### AI Layer
- **Automatic ticket classification** — LLaMA 3 (70B) assigns priority (low / medium / high) based on natural language understanding. Queue (IT / HR / Finance / Facilities) is assigned instantly via keyword rules with LLM fallback
- **Document summarisation** — uploaded attachments are summarised by LLaMA 3.1-8B so agents see key points without opening the file
- **RAG chatbot** — semantic search over a private knowledge base using SentenceTransformers embeddings + ChromaDB vector store + Groq LLM for grounded answer generation
- **Conversation memory** — chatbot retains the last 10 exchanges for context-aware multi-turn responses
- **Ticket suggestion** — when no KB match is found, the chatbot prompts the user to raise a support ticket instead of hallucinating

### Ticketing System
- Three user roles: **Customer**, **Agent**, **Admin**
- Department-based agent routing — IT tickets go to IT agents, HR tickets to HR agents, etc.
- Workload balancing — agents capped at 30 active tickets, overflow redistributed automatically
- Ticket ownership — agents can only view and respond to tickets assigned to them
- Full conversation thread per ticket with file attachment support

### Admin Panel
- Manage agents (create, edit, reset password, assign department)
- Manage customers (view, edit, toggle active)
- Knowledge base document management (upload, index, delete)
- FAQ management
- Analytics dashboard with ticket volume, priority distribution, queue breakdown, and per-agent performance

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI, SQLAlchemy (async), SQLite, Alembic, Pydantic v2 |
| Frontend | React 18, React Router v6, Axios, Recharts, Lucide React, Vite |
| Auth | JWT (python-jose), bcrypt |
| LLM Inference | Groq API — LLaMA 3 70B + LLaMA 3.1 8B Instant |
| Embeddings | SentenceTransformers (all-MiniLM-L6-v2) — runs locally |
| Vector Store | ChromaDB (local persistent) |
| Logging | structlog |

---

## Project Structure

```
support-portal-v2/          # Backend
├── app/
│   ├── api/v1/endpoints/   # auth, tickets, users, faqs, kb, admin
│   ├── core/               # config, security, deps, exceptions, logging
│   ├── db/                 # session, base
│   ├── models/             # user, ticket, kb
│   ├── schemas/            # pydantic schemas
│   ├── services/
│   │   ├── ai/             # classifier, summarizer, rag
│   │   └── ticket, user, kb, analytics
│   └── utils/              # files, pagination
├── alembic/                # database migrations
├── seed.py                 # demo data seeder
└── requirements.txt

frontend/                   # React frontend
├── src/
│   ├── api/                # axios config
│   ├── auth/               # AuthContext, ProtectedRoute
│   ├── components/         # Shell, KBChat
│   └── pages/
│       ├── admin/          # Dashboard, ManageAgents, ManageCustomers, ManageFAQs, ManageKnowledgeBase, Reports
│       ├── agent/          # AgentDashboard, AssignedTickets, TicketDetail, ChangePassword
│       ├── customer/       # Tickets, CreateTicket, TicketDetail, FAQ, KnowledgeBase
│       └── public/         # Home, PublicFAQ, PublicKB
└── package.json
```

---

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- Groq API key — free at [console.groq.com](https://console.groq.com)

### Backend Setup

```bash
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/supportsphere.git
cd supportsphere/support-portal-v2

# 2. Create and activate virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # Mac/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create .env file
cp .env.example .env
# Edit .env and add your GROQ_API_KEY

# 5. Run database migrations
alembic upgrade head

# 6. Seed demo data
python seed.py

# 7. Start the server
uvicorn app.main:app --reload
```

Backend runs at `http://127.0.0.1:8000`
API docs available at `http://127.0.0.1:8000/docs`

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:5173`

---

## Environment Variables

Create a `.env` file in the backend root:

```env
APP_ENV=development
DEBUG=false
DATABASE_URL=sqlite+aiosqlite:///./support.db
JWT_SECRET_KEY=your-secret-key-change-in-production
ADMIN_EMAIL=admin@support.com
ADMIN_PASSWORD=Admin@123
GROQ_API_KEY=your_groq_api_key_here
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
ALLOWED_UPLOAD_TYPES=application/pdf,text/plain
KB_SIMILARITY_THRESHOLD=0.8
```

---

## Demo Accounts

After running `python seed.py`:

| Role | Email | Password |
|---|---|---|
| Admin | admin@support.com | Admin@123 |
| Agent | sarah@support.com | agent123 |
| Agent | james@support.com | agent123 |
| Customer | alice@example.com | customer123 |
| Customer | bob@example.com | customer123 |

---

## AI Pipeline

### Ticket Classification
```
Subject + Description
        ↓
Queue: keyword rules (IT / HR / Finance / Facilities) — instant, no API call
        ↓
Priority: Groq llama3-70b, temperature=0 → {"priority": "high"}
        ↓
Fallback: keyword rules if API unavailable
```

### RAG Chatbot
```
User question
     ↓
SentenceTransformers → 384-dim vector
     ↓
ChromaDB similarity search → top 4 chunks
     ↓
Filter: distance < 0.8 threshold
     ↓
Found? → Groq llama-3.1-8b + conversation history → grounded answer
No match? → Suggest raising a support ticket
```

---

## Key Design Decisions

- **RAG over fine-tuning** — new documents indexed in seconds, no GPU or retraining required
- **Groq over OpenAI** — LPU hardware for speed, open-source LLaMA models, free tier
- **Local embeddings** — SentenceTransformers runs on CPU, zero API cost, no internet dependency after first download
- **ChromaDB over Pinecone** — local persistence, zero cost, sufficient for demo scale
- **Two LLM models** — 70B for accurate classification, 8B-instant for low-latency chatbot responses
- **Async FastAPI** — non-blocking I/O handles concurrent LLM API calls without blocking
- **Background task with own session** — KB indexing never blocks the HTTP response; uses independent DB session to avoid lifecycle conflicts

---

## License

MIT
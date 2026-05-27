# VoiceForge — Voice-Driven Accessibility Assistant

> **Hackathon Submission** | One Man, An Entire System
> Stack: **Omi** + **Qdrant** + **Lyzr**

[![Python](https://img.shields.io/badge/Python-3.11+-blue?style=flat-square)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green?style=flat-square)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.3-61DAFB?style=flat-square)](https://react.dev)
[![Qdrant](https://img.shields.io/badge/Qdrant-Vector_DB-red?style=flat-square)](https://qdrant.tech)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)

---

## What is VoiceForge?

VoiceForge is an autonomous, voice-first accessibility assistant that empowers people with disabilities to generate structured documents, fill forms, create summaries, and execute guided workflows — **entirely through voice commands**.

Traditional AI chatbots give you conversations. VoiceForge gives you **outputs you can actually use** — PDFs, filled forms, formatted reports — all driven by natural speech.

---

##  Architecture Overview

```
┌──────────────────────────────────────────────────────────┐
│                   USER (Voice Input)                     │
└──────────────────────┬───────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────┐
│                  OMI INTEGRATION                         │
│   • WebSocket voice stream / Omi webhook receiver        │
│   • Real-time transcript processing                      │
│   • Intent extraction from speech                        │
└──────────────────────┬───────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────┐
│              LYZR AGENT ORCHESTRATION                    │
│   • AccessibilityAgent  (main orchestrator)              │
│   • DocumentAgent       (form/doc generation)            │
│   • MemoryAgent         (user preference learning)       │
│   • WorkflowAgent       (multi-step guided tasks)        │
└─────────────┬────────────────────────┬───────────────────┘
              │                        │
              ▼                        ▼
┌─────────────────────┐   ┌────────────────────────────────┐
│  QDRANT VECTOR DB   │   │       OUTPUT GENERATION        │
│  • User prefs       │   │   • PDF Documents              │
│  • Templates        │   │   • Filled Forms               │
│  • Session memory   │   │   • Structured Reports         │
│  • Doc history      │   │   • Guided Workflows           │
└─────────────────────┘   │   • Audio Feedback (TTS)       │
                          └────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Voice Input | **Omi** | Voice capture, real-time transcript, webhook |
| Vector Memory | **Qdrant** | Semantic memory, templates, user preferences |
| AI Orchestration | **Lyzr** | Multi-agent reasoning, workflow execution |
| Backend | **FastAPI** (Python) | REST API, WebSocket, webhook handler |
| Frontend | **React + Vite** | Accessible web UI |
| TTS | **ElevenLabs / gTTS** | Voice feedback |
| Doc Generation | **ReportLab** | PDF output |

---

##  Quick Start

### Prerequisites

```
Python 3.11+
Node.js 18+
Docker (for Qdrant)
```

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/voiceforge-accessibility
cd voiceforge-accessibility
```

### 2. Start Qdrant (Vector Database)

```bash
docker run -p 6333:6333 -p 6334:6334 \
  -v $(pwd)/qdrant_storage:/qdrant/storage:z \
  qdrant/qdrant
```

### 3. Configure Environment

```bash
cp .env.example .env
# Open .env and add your API keys
```

Required keys:
```
OPENAI_API_KEY=sk-...
LYZR_API_KEY=...
QDRANT_HOST=localhost
QDRANT_PORT=6333
OMI_APP_ID=...
OMI_APP_SECRET=...
```

### 4. Backend Setup

```bash
cd backend
pip install -r requirements.txt
python scripts/init_qdrant.py      # Creates collections + seeds templates
uvicorn main:app --reload --port 8000
```

### 5. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** in your browser.

---

## Docker Compose (Full Stack)

```bash
cp .env.example .env
# Add your API keys to .env

docker-compose up --build
```

Services started:
- Qdrant → http://localhost:6333
- Backend API → http://localhost:8000
- Frontend → http://localhost:5173

---

##  Voice Commands

| Say This | What Happens |
|----------|-------------|
| *"Create a medical intake form for John Smith"* | Generates a filled PDF medical form |
| *"Fill out a job application"* | Starts guided step-by-step workflow |
| *"Summarize my recent documents"* | Retrieves + summarizes from Qdrant memory |
| *"Remember I prefer large text"* | Saves accessibility preference to Qdrant |
| *"Generate a meeting summary"* | Creates structured meeting notes PDF |
| *"Read back my last document"* | TTS audio playback of last generated doc |
| *"Find my medical form from yesterday"* | Semantic search across document history |

---

## ♿ Accessibility Features

| Feature | Details |
|---------|---------|
| **Screen Reader** | Full ARIA labels, roles, live regions — NVDA + VoiceOver tested |
| **Large Text** | 3 font size modes: medium/large / x-large (CSS variable system) |
| **High Contrast** | WCAG AAA contrast ratio in high contrast mode |
| **Keyboard Navigation** | Every element reachable and operable via Tab / Enter |
| **Voice-Only Mode** | Complete app usable with zero mouse or keyboard input |
| **Reduce Motion** | Respects `prefers-reduced-motion` + manual toggle |
| **Audio Feedback** | TTS for all responses (ElevenLabs primary, gTTS fallback) |
| **Skip Link** | "Skip to main content" for screen reader users |
| **Persistent Prefs** | Accessibility settings stored in Qdrant across sessions |

**WCAG 2.1 AA Compliant** — see `docs/ACCESSIBILITY_COMPLIANCE.md` for full audit.

---

## Project Structure

```
voiceforge-accessibility/
├── backend/
│   ├── main.py                      # FastAPI app + all routes
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── agents/
│   │   ├── accessibility_agent.py   # Main Lyzr orchestrator
│   │   └── workflow_agent.py        # Guided multi-step workflows
│   ├── services/
│   │   ├── qdrant_service.py        # Vector DB — 4 collections
│   │   ├── lyzr_service.py          # Lyzr + OpenAI agent pipeline
│   │   ├── omi_service.py           # Omi webhook + transcript parser
│   │   ├── document_service.py      # PDF generation (ReportLab)
│   │   └── tts_service.py           # ElevenLabs / gTTS
│   ├── models/
│   │   └── schemas.py               # Pydantic data models
│   └── scripts/
│       └── init_qdrant.py           # DB init + template seeding
├── frontend/
│   ├── src/
│   │   ├── App.jsx                  # Root component + layout
│   │   ├── components/
│   │   │   ├── VoiceInterface.jsx   # Mic button + Web Speech API
│   │   │   ├── DocumentViewer.jsx   # PDF preview + download
│   │   │   ├── WorkflowGuide.jsx    # Step progress indicator
│   │   │   ├── MemoryPanel.jsx      # Conversation history sidebar
│   │   │   └── AccessibilityBar.jsx # Font/contrast/motion controls
│   │   ├── hooks/
│   │   │   └── useWebSocket.js      # WS connection + REST fallback
│   │   └── utils/
│   │       └── api.js               # API client helpers
│   ├── index.html
│   ├── vite.config.js
│   ├── Dockerfile
│   └── package.json
├── docs/
│   └── ACCESSIBILITY_COMPLIANCE.md  # WCAG 2.1 audit
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

---

##  Qdrant Collections

| Collection | Purpose | Vector Model |
|-----------|---------|-------------|
| `user_preferences` | Accessibility settings per user | all-MiniLM-L6-v2 |
| `document_templates` | 5 pre-built form templates | all-MiniLM-L6-v2 |
| `session_memory` | Conversation history + context | all-MiniLM-L6-v2 |
| `generated_docs` | Past documents for retrieval | all-MiniLM-L6-v2 |

Vector size: **384 dimensions**, Cosine similarity.

---

## Omi Integration

VoiceForge connects to Omi in two ways:

**Mode 1 — Omi Device Webhook** (for Omi hardware users)
```
Omi Device → POST /api/omi/webhook → Agent Pipeline → Output
```
Setup: Create an app at https://omi.me/developers → set webhook URL to `https://your-domain/api/omi/webhook`

**Mode 2 — Browser WebSocket** (no Omi device needed)
```
Browser Mic → Web Speech API → WebSocket → Agent Pipeline → Output
```
Works in Chrome and Edge. No extra hardware required.

---

## API Endpoints

| Method | Endpoint | Description |
|--------|---------|-------------|
| `POST` | `/api/omi/webhook` | Omi device webhook receiver |
| `WS` | `/ws/voice/{session_id}` | Real-time voice WebSocket |
| `POST` | `/api/command` | REST voice command (testing) |
| `GET` | `/api/preferences/{user_id}` | Get user accessibility prefs |
| `POST` | `/api/preferences/{user_id}` | Save accessibility prefs |
| `GET` | `/api/documents/{user_id}` | List user's documents |
| `GET` | `/api/templates` | List available templates |
| `POST` | `/api/session` | Create new session |
| `GET` | `/api/session/{id}/history` | Get session history |
| `GET` | `/health` | Health check |

Full API docs available at **http://localhost:8000/docs** (Swagger UI).

---

##  Document Templates

Five built-in templates, all voice-fillable:

| Template | Fields | Use Case |
|---------|--------|---------|
| Medical Intake Form | 10 fields | Healthcare visits |
| Job Application | 10 fields | Employment |
| Incident Report | 7 fields | Accidents/workplace |
| Meeting Summary | 8 fields | Productivity |
| Accommodation Request | 8 fields | Disability accommodations |

---

##  Judging Criteria

| Criteria | Our Implementation |
|---------|-------------------|
| **Functionality (30–40%)** | Full voice → PDF pipeline, 7 intent types, guided workflows |
| **AI Output Quality (20%)** | Lyzr multi-agent + GPT-4o-mini reasoning, context-aware responses |
| **Qdrant Usage (15–20%)** | 4 collections, semantic search, RAG, preference learning |
| **Innovation (10–35%)** | Autonomous document generation from pure voice — no typing needed |
| **UX / Accessibility (10–20%)** | WCAG AA, screen reader, keyboard nav, voice-only mode |
| **Documentation (5–10%)** | Full README + compliance doc + Swagger UI + inline comments |

---

##  Deployment

### Railway (Recommended)

```bash
# Install Railway CLI
npm install -g @railway/cli
railway login
railway new
railway up
```

### Render

Set build command: `pip install -r requirements.txt`
Set start command: `uvicorn main: app --host 0.0.0.0 --port $PORT`

### Qdrant Cloud (Production DB)

1. Sign up at https://cloud.qdrant.io (free tier available)
2. Create a cluster → copy Host + API Key
3. Update `.env`: `QDRANT_HOST=your-cluster.qdrant.io` + `QDRANT_API_KEY=...`

---

##  Contributing

1. Fork the repo
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit: `git commit -m 'Add my feature'`
4. Push: `git push origin feature/my-feature`
5. Open a Pull Request

---

## License

MIT License — free to use, modify, and distribute.

---

##  Acknowledgments

Built with:
- [Omi](https://omi.me) — Voice capture and memory
- [Qdrant](https://qdrant.tech) — Vector database
- [Lyzr](https://lyzr.ai) — AI agent orchestration
- [FastAPI](https://fastapi.tiangolo.com) — Python web framework
- [React](https://react.dev) — Frontend UI

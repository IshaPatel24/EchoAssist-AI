# 🎙️ VoiceForge — Voice-Driven Accessibility Assistant

> **Hackathon Submission** | One Man, An Entire System  
> Stack: **Omi** + **Qdrant** + **Lyzr**

---

## 🌟 What is VoiceForge?

VoiceForge is an autonomous, voice-first accessibility assistant that empowers people with disabilities to generate structured documents, fill forms, create summaries, and execute guided workflows — entirely through voice commands.

Traditional AI chatbots give you *conversations*. VoiceForge gives you **outputs you can actually use** — PDFs, filled forms, formatted reports, and structured data — all driven by natural speech.

---

## 🧠 Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    USER (Voice Input)                    │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│                  OMI INTEGRATION                         │
│  • WebSocket voice stream / Omi webhook receiver         │
│  • Real-time transcript processing                       │
│  • Intent extraction from speech                         │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│               LYZR AGENT ORCHESTRATION                   │
│  • AccessibilityAgent (main orchestrator)                │
│  • DocumentAgent (form/doc generation)                   │
│  • MemoryAgent (user preference learning)                │
│  • WorkflowAgent (multi-step guided tasks)               │
└──────────┬──────────────────────────┬───────────────────┘
           │                          │
           ▼                          ▼
┌──────────────────┐      ┌──────────────────────────────┐
│  QDRANT VECTOR   │      │     OUTPUT GENERATION         │
│  DATABASE        │      │  • PDF Documents               │
│  • User prefs    │      │  • Filled Forms               │
│  • Templates     │      │  • Structured Reports         │
│  • Session mem   │      │  • Guided Workflows           │
│  • Doc history   │      │  • Audio Feedback (TTS)       │
└──────────────────┘      └──────────────────────────────┘
```

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Voice Input | **Omi** | Voice capture, real-time transcript, webhook |
| Vector Memory | **Qdrant** | Semantic memory, templates, user preferences |
| AI Orchestration | **Lyzr** | Multi-agent reasoning, workflow execution |
| Backend | **FastAPI** (Python) | REST API, WebSocket, webhook handler |
| Frontend | **React + Vite** | Accessible web UI |
| TTS | **gTTS / ElevenLabs** | Voice feedback |
| Doc Generation | **ReportLab + FPDF2** | PDF output |

---

## 🚀 Quick Start

### Prerequisites

```bash
Python 3.11+
Node.js 18+
Docker (for Qdrant)
```

### 1. Clone & Install

```bash
git clone https://github.com/yourusername/voiceforge-accessibility
cd voiceforge-accessibility

# Backend
cd backend
pip install -r requirements.txt

# Frontend
cd ../frontend
npm install
```

### 2. Start Qdrant

```bash
docker run -p 6333:6333 -p 6334:6334 \
  -v $(pwd)/qdrant_storage:/qdrant/storage:z \
  qdrant/qdrant
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env with your API keys
```

### 4. Initialize Vector Collections

```bash
cd backend
python scripts/init_qdrant.py
```

### 5. Run

```bash
# Backend (from /backend)
uvicorn main:app --reload --port 8000

# Frontend (from /frontend)
npm run dev
```

---

## 🎯 Key Features

### Voice Commands Supported

| Command Pattern | Action |
|----------------|--------|
| "Create a medical form for [name]" | Generates filled medical intake form |
| "Summarize my last meeting" | Retrieves + summarizes from memory |
| "Fill out a job application" | Guided multi-step workflow |
| "Remember I prefer large text" | Stores accessibility preference |
| "Generate a report about [topic]" | Structured document output |
| "Read back my document" | TTS playback of generated content |

### Accessibility Features

- Screen reader compatible (ARIA labels throughout)
- High contrast mode (WCAG AA compliant)
- Large text mode (user preference stored in Qdrant)
- Keyboard navigation (full app usable without mouse)
- Voice-only mode (no typing required)
- Reduced motion mode (respects prefers-reduced-motion)

---

## 📁 Project Structure

```
voiceforge-accessibility/
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   ├── agents/
│   │   ├── accessibility_agent.py
│   │   ├── document_agent.py
│   │   ├── memory_agent.py
│   │   └── workflow_agent.py
│   ├── services/
│   │   ├── omi_service.py
│   │   ├── qdrant_service.py
│   │   ├── lyzr_service.py
│   │   ├── tts_service.py
│   │   └── document_service.py
│   ├── models/
│   │   └── schemas.py
│   └── scripts/
│       └── init_qdrant.py
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── components/
│   │   └── hooks/
│   └── package.json
├── docs/
│   └── ACCESSIBILITY_COMPLIANCE.md
├── .env.example
└── README.md
```

---

## Qdrant Collections

| Collection | Purpose | Vector Size |
|-----------|---------|-------------|
| user_preferences | Accessibility settings per user | 384 |
| document_templates | Reusable form/doc templates | 384 |
| session_memory | Conversation context + history | 384 |
| generated_docs | Past documents for retrieval | 384 |

---

## License

MIT License

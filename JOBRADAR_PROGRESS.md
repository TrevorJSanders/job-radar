# JobRadar — Build Progress Tracker

> Paste this file into Claude at the start of each session so we can pick up where we left off.
> Update checkboxes and notes as you complete steps.

---

## Project Overview

AI-powered job application tracker with Gmail integration, Kanban board UI, and background email polling.

## Tech Stack

| Layer           | Technology                                       |
| --------------- | ------------------------------------------------ |
| AI              | Gemini API (Python SDK)                          |
| Backend         | Python 3.11+ / FastAPI / Uvicorn                 |
| Database        | SQLite (via Python `sqlite3`)                    |
| Scheduler       | APScheduler                                      |
| Gmail           | Gmail API / google-auth Python library           |
| Frontend        | React + TypeScript + Vite + Tailwind + shadcn/ui |
| Drag & Drop     | dnd-kit                                          |
| Charts          | Recharts                                         |
| Frontend Host   | Vercel (free)                                    |
| Backend Host    | Railway (free hobby tier)                        |
| Package Manager | pnpm (monorepo workspaces)                       |

---

## Phase 1 — Foundation

**Goal:** Monorepo scaffolded, FastAPI running, SQLite schema created, React frontend running, frontend talking to backend.

- [x] **Step 1** — Monorepo initialized (`pnpm-workspace.yaml`, root `package.json`, `/backend`, `/frontend` folders)
- [x] **Step 2** — FastAPI backend initialized (`main.py`, `requirements.txt`, `/health` endpoint confirmed working)
- [x] **Step 3** — SQLite schema designed and created (`database.py`, all tables created on startup)
- [x] **Step 4** — React frontend initialized (Vite + TypeScript + Tailwind + shadcn/ui confirmed running)
- [x] **Step 5** — Frontend fetches from backend (`/health` call confirmed from React)

**Phase 1 Notes:**

```
(paste any errors, decisions, or deviations here)
```

---

## Phase 2 — Gmail Integration

**Goal:** OAuth flow working, emails fetched and stored in SQLite, deduplicated by message ID.

- [ ] **Step 6** — Google Cloud project created, Gmail API enabled, OAuth credentials downloaded (`credentials.json`)
- [ ] **Step 7** — Gmail auth flow written in Python (browser consent on first run, token saved to `token.json`, auto-refresh working)
- [ ] **Step 8** — Email fetcher written (pulls last 7 days of unread emails, extracts sender/subject/body/timestamp/thread ID)
- [ ] **Step 9** — Raw emails stored in SQLite (deduplicated by Gmail message ID)
- [ ] **Step 10** — Live inbox test passed (real emails pulling and storing correctly)

**Phase 2 Notes:**

```
(paste any errors, decisions, or deviations here)
```

---

## Phase 3 — AI Classification Layer

**Goal:** Gemini classifying emails, structured JSON output, confidence threshold routing to review queue.

- [ ] **Step 11** — Gemini Python SDK installed, API key configured, first test call working
- [ ] **Step 12** — Classification prompt written and tested (returns `{type, company, role, confidence, action_needed, reasoning}`)
- [ ] **Step 13** — Extraction prompt written and tested (pulls clean fields from confirmed job emails)
- [ ] **Step 14** — Confidence threshold logic added (≥85% auto-log, <85% → review queue)
- [ ] **Step 15** — Classifier wired into email fetcher pipeline
- [ ] **Step 16** — Prompt iteration complete (classification feels accurate on real emails)

**Phase 3 Notes:**

```
(paste any errors, decisions, or deviations here)
```

---

## Phase 4 — Backend API

**Goal:** All endpoints built and tested that the frontend will consume.

- [ ] **Step 17** — Applications CRUD endpoints (GET all, GET one, POST manual entry, PATCH status/notes, DELETE)
- [ ] **Step 18** — Review queue endpoints (GET pending, POST confirm/correct)
- [ ] **Step 19** — Dashboard stats endpoint (counts by status, response rate, weekly trend data)
- [ ] **Step 20** — Manual poll trigger endpoint (POST `/poll` runs Gmail fetch + classify on demand)
- [ ] **Step 21** — Cover letter endpoint (POST with JD text, returns AI draft)

**Phase 4 Notes:**

```
(paste any errors, decisions, or deviations here)
```

---

## Phase 5 — Frontend

**Goal:** Full UI built — Kanban board, card detail, review queue, dashboard, manual entry, demo mode, cover letter modal.

- [ ] **Step 22** — Kanban board built (4 columns, cards per application, dnd-kit drag and drop wired)
- [ ] **Step 23** — Application card component (company, role, days since activity, status badge, next action chip)
- [ ] **Step 24** — Card detail drawer (full detail, email thread, notes editor, fit score)
- [ ] **Step 25** — Review queue UI (list of low-confidence emails, Accept/Edit/Reject actions)
- [ ] **Step 26** — Dashboard page (stat cards, Recharts weekly chart, applications list)
- [ ] **Step 27** — Manual entry form (add application not from email)
- [ ] **Step 28** — Demo mode toggle (seeds fake data, masks real data)
- [ ] **Step 29** — Cover letter modal (paste JD → get draft → copy to clipboard)

**Phase 5 Notes:**

```
(paste any errors, decisions, or deviations here)
```

---

## Phase 6 — Background Scheduler

**Goal:** APScheduler polling Gmail every 30 minutes automatically when backend is running.

- [ ] **Step 30** — APScheduler wired into FastAPI (starts on server start, polls every 30 min)
- [ ] **Step 31** — Last-polled timestamp surfaced in UI (small indicator + manual "poll now" button)

**Phase 6 Notes:**

```
(paste any errors, decisions, or deviations here)
```

---

## Phase 7 — Deployment

**Goal:** Backend live on Railway, frontend live on Vercel, OAuth working in production, README complete.

- [ ] **Step 32** — Backend deployed to Railway (env vars set, confirmed running)
- [ ] **Step 33** — Frontend deployed to Vercel (API base URL env var set, confirmed building)
- [ ] **Step 34** — Gmail OAuth production flow resolved (token handling for hosted environment)
- [ ] **Step 35** — End to end live test passed (polling, classification, frontend all working on live URLs)
- [ ] **Step 36** — README written (architecture diagram, features, setup instructions, demo mode note)

**Phase 7 Notes:**

```
(paste any errors, decisions, or deviations here)
```

---

## Current Session Notes

```
Session date:
Currently working on: Phase 1, Step 1
Blockers:
Decisions made this session:
```

---

## Key Decisions Log

| Decision             | Choice Made                           | Reason                                 |
| -------------------- | ------------------------------------- | -------------------------------------- |
| AI provider          | Gemini API                            | Free tier, already familiar            |
| Database             | SQLite                                | Zero config, good for learning         |
| Backend framework    | FastAPI                               | Industry standard Python API framework |
| Hosting              | Railway (backend) + Vercel (frontend) | Both free tier                         |
| Confidence threshold | 85%                                   | TBD — adjust after Phase 3 testing     |

---

## File Structure (target)

```
jobradar/
├── pnpm-workspace.yaml
├── package.json
├── .gitignore
├── README.md
├── JOBRADAR_PROGRESS.md
├── backend/
│   ├── main.py
│   ├── database.py
│   ├── requirements.txt
│   ├── routers/
│   │   ├── applications.py
│   │   ├── queue.py
│   │   ├── dashboard.py
│   │   └── ai.py
│   ├── services/
│   │   ├── gmail_service.py
│   │   ├── classifier.py
│   │   └── scheduler.py
│   └── credentials.json        ← never commit this
│   └── token.json              ← never commit this
└── frontend/
    ├── index.html
    ├── vite.config.ts
    ├── tailwind.config.ts
    ├── package.json
    └── src/
        ├── main.tsx
        ├── App.tsx
        ├── components/
        │   ├── KanbanBoard.tsx
        │   ├── ApplicationCard.tsx
        │   ├── CardDetailDrawer.tsx
        │   ├── ReviewQueue.tsx
        │   ├── Dashboard.tsx
        │   ├── ManualEntryForm.tsx
        │   └── CoverLetterModal.tsx
        └── lib/
            └── api.ts
```

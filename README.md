# Namma Seva Agent AI (நம்ம சேவை)

> **Tamil Nadu's Unified AI Agent for Government Services**  
> An intelligent, multilingual civic assistance platform designed to help citizens discover, prepare for, and track Tamil Nadu government services in simple Tamil, Tanglish, and English.

[![CI Test Suite](https://github.com/nanthishvaran17/namma-seva-agent/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/nanthishvaran17/namma-seva-agent/actions/workflows/ci.yml)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%20%7C%203.14-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.159-009688.svg)](https://fastapi.tiangolo.com/)
[![React 19](https://img.shields.io/badge/React-19.3-61DAFB.svg)](https://react.dev/)
[![DPDP Act 2023](https://img.shields.io/badge/Privacy-DPDP%20Compliant-success.svg)](./SECURITY.md)

---

## 🏛️ 1. Overview & Vision

Government portals often confront citizens with bureaucratic jargon, intricate prerequisites, and fragmented digital websites (e-Sevai, TNeGA, TNPDS, NSP). **Namma Seva Agent** acts as an empathetic personal government-service assistant:

A citizen can simply ask:
- *"Enakku community certificate venum."*
- *"எனக்கு வருமானச் சான்றிதழ் வேண்டும்."*
- *"First graduate certificate eppadi apply pandrathu?"*
- *"What are the prerequisites for Post-Matric Scholarship?"*

The agent understands their goal, verifies prerequisite certificates recursively using a **Deterministic Dependency Graph (DAG)**, generates step-by-step checklists, prepares document requirements, and tracks progress through a verified state machine.

### Non-Negotiable Civic Invariants:
1. **100% Verified Source Grounding:** Government facts, fees, and timelines are anchored in official Tamil Nadu Citizen Charters and gazettes. The LLM is **never** permitted to fabricate fees or deadlines.
2. **Zero OTP / Secret Disclosure Policy:** The agent strictly **never** asks for, accepts, or stores Aadhaar OTPs, portal passwords, or bank PINs. Submissions operate in **Guided Mode** with the citizen in control.
3. **Citizen Data Sovereignty (DPDP Act 2023):** One-click full data export (JSON) and permanent erasure on demand (`DELETE /api/v1/auth/me/data`).

---

## 🏗️ 2. System Architecture

```
                      +---------------------------------------+
                      |       Citizen Channels / Clients      |
                      |  - Web UI (React + Tailwind CSS)     |
                      |  - WhatsApp Business Cloud API        |
                      |  - Tamil / English Voice Interface    |
                      +-------------------+-------------------+
                                          |
                                    REST / JSON
                                          v
                      +---------------------------------------+
                      |         FastAPI Gateway (/api/v1)     |
                      |  - Auth & RBAC (Citizen & Admin)      |
                      |  - Rate Limiting & Input Validation   |
                      |  - Consent & Privacy Interceptor      |
                      +-------------------+-------------------+
                                          |
        +---------------------------------+---------------------------------+
        |                                 |                                 |
        v                                 v                                 v
+------------------+            +-------------------+             +-------------------+
|  Agent AI Engine |            | Dependency Graph  |             | Document Pipeline |
| - Intent Router  |            | & Planner         |             | - File Upload     |
| - Tool Dispatcher|            | - DAG Resolution  |             | - OCR Engine      |
| - LLM Adapter    |            | - Cycle Detection |             | - Field Extractor |
|   (Gemini/Mock)  |            | - Topological Sort|             | - Doc Matcher     |
+--------+---------+            +---------+---------+             +---------+---------+
                                          |
                                          v
                      +---------------------------------------+
                      |         Service Playbook Engine       |
                      |  - Schema-validated JSON playbooks    |
                      |  - Verified Official Sources          |
                      |  - Verification Status Lifecycle      |
                      +-------------------+-------------------+
```

---

## 📂 3. Repository Directory Layout

```
namma-seva-agent/
├── frontend/                     # React + Vite + TypeScript application
│   ├── src/
│   │   ├── components/           # UI primitives (Chat, Directory, Dashboard, Admin)
│   │   ├── services/api.ts       # Typed REST API client
│   │   ├── types.ts              # Domain interfaces
│   │   └── App.tsx               # Main application coordinator
│   └── package.json
├── backend/                      # FastAPI Python backend
│   ├── app/
│   │   ├── api/v1/               # Versioned REST API endpoints
│   │   ├── core/                 # Config, JWT, security utilities
│   │   ├── db/                   # Async SQLAlchemy database session
│   │   ├── models/               # Relational ORM models (User, Tasks, Docs, Audit)
│   │   ├── planning/             # Deterministic DAG dependency planner
│   │   ├── playbooks/            # Schema validator and catalog loader
│   │   ├── agent/                # LLM orchestration and providers (Mock/Gemini)
│   │   ├── tools/                # Validated tool registry
│   │   └── main.py               # Application entrypoint & static mounting
│   ├── tests/                    # 13 automated test suites + 50 benchmark cases
│   └── requirements.txt
├── knowledge/
│   ├── playbooks/                # 5 Candidate Tamil Nadu Government Playbooks
│   ├── schemas/                  # JSON Schema for service playbooks
│   └── evaluation/               # 50-Scenario Multilingual Benchmark Dataset
├── infrastructure/               # Dockerfiles for containerized deployment
├── docker-compose.yml
├── .env.example
├── ARCHITECTURE.md
├── SECURITY.md
├── PROJECT_STATUS.md
└── IMPLEMENTATION_PLAN.md
```

---

## 🚀 4. Quick Start & Local Execution

### Prerequisites
- Python 3.12+ (Python 3.14 compatible)
- Node.js v20+ and npm

### Step 1: Backend Setup
```bash
# Clone the repository
git clone https://github.com/nanthishvaran17/namma-seva-agent.git
cd namma-seva-agent

# Create Python virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt
```

### Step 2: Run Automated Tests
```bash
# Execute the full 13-test suite including the 50-case multilingual benchmark
pytest backend/tests/ -v
```

### Step 3: Start the Backend Service
```bash
# Start FastAPI on port 8000
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
API Documentation is available interactively at `http://127.0.0.1:8000/docs`.

### Step 4: Frontend Development
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` to interact with the application.

---

## 🧪 5. Automated Test Suite & Benchmark Evidence

The system includes 13 comprehensive automated test suites:
- **`test_playbooks_and_planning.py`**:
  - Schema validation for all 5 initial candidate playbooks
  - Recursive prerequisite dependency resolution (`post_matric_scholarship` $\to$ `community`, `income`, `nativity`)
  - First Graduate prerequisite resolution (`first_graduate` $\to$ `nativity`)
  - Personalized action plan generation filtering already completed certificates
  - Circular dependency detection (`DependencyCycleError`)
  - Bilingual search in Tamil and English
- **`test_agent_evaluation.py`**:
  - Evaluates 50 benchmark scenarios across Tamil, Tanglish, and English
  - Prompt injection defense verification
  - Human officer escalation handling
  - Official source citation grounding verification
- **`test_api_v1.py`**:
  - Health check & metadata verification
  - Full citizen lifecycle: Registration, Login, Token generation
  - User task creation and deterministic state machine transitions
  - DPDP Data Export and irreversible one-click erasure
  - WhatsApp Cloud API simulation

---

## 🔒 6. Security & Privacy

For full threat modeling and DPDP Act 2023 details, refer to [SECURITY.md](./SECURITY.md).

---

## 📜 7. License & Attribution

Developed for the citizens of Tamil Nadu under the MIT License. Grounded strictly in public government data published by Tamil Nadu e-Governance Agency (TNeGA), Revenue & Disaster Management Department, and Welfare Departments.

# Namma Seva Agent AI — Implementation Plan

This implementation plan details the architectural milestones, deliverables, test requirements, and acceptance criteria for building Namma Seva Agent.

---

## Roadmap & Milestones

### Milestone 1 — Foundation & Playbook Engine
- [x] Environment inspection and architectural baseline.
- [ ] Create repository directory tree (`backend/`, `frontend/`, `knowledge/`, `docs/`, `infrastructure/`).
- [ ] Backend setup:
  - Python virtual environment `.venv`.
  - `pyproject.toml` and dependencies (`fastapi`, `uvicorn`, `pydantic`, `pydantic-settings`, `sqlalchemy`, `aiosqlite`, `pytest`, `pytest-asyncio`, `httpx`, `pyyaml`).
  - Core configuration system (`backend/app/core/config.py`).
  - Database engine and declarative Base (`backend/app/db/session.py`).
  - Initial normalized models: User, Consent, ServicePlaybook, ServiceSource, ServiceDependency, UserTask, TaskEvent, UserDocument, Reminder, AuditLog.
- [ ] Playbook engine:
  - Playbook schema with Pydantic (`knowledge/schemas/playbook_schema.json` & Pydantic models).
  - 5 initial verified candidate services for Tamil Nadu:
    1. Community Certificate (Revenue Dept / e-Sevai)
    2. Income Certificate (Revenue Dept / e-Sevai)
    3. Nativity Certificate (Revenue Dept / e-Sevai)
    4. First Graduate Certificate (Higher Education Dept / e-District)
    5. Post-Matric Scholarship for SC/ST/SCC or BC/MBC Students (TN Welfare Depts)
  - Playbook loader & schema validator.
  - Deterministic Dependency Graph & Topological Planner (`backend/app/planning/dependency_graph.py`).
  - Cycle detection, missing prerequisites resolution, and personalized action plan generation.
- [ ] Unit & Integration Tests:
  - Test playbook validation against schema.
  - Test dependency resolver & topological ordering.
  - Test cycle detection.
  - Test database models & CRUD operations.

### Milestone 2 — AI Agent Engine & Tool Calling
- [ ] Provider-agnostic LLM Abstraction (`LLMProviderInterface`):
  - Mock provider (`MockLLMProvider`) with deterministic Tamil/Tanglish/English response logic.
  - Real provider adapter (Google Gemini / OpenAI compatible) configured via environment variables.
- [ ] Agent Brain & Tool Dispatcher:
  - Intent classification (`DISCOVER_SERVICE`, `CHECK_ELIGIBILITY`, `GET_DOCUMENTS`, `RESOLVE_DEPENDENCIES`, `PREPARE_TASK`, `STATUS_QUERY`, `CLARIFICATION`, `OUT_OF_SCOPE`).
  - Tool system with strict Pydantic schemas:
    - `search_services`
    - `get_service_details`
    - `get_verified_sources`
    - `check_eligibility`
    - `resolve_service_dependencies`
    - `create_action_plan`
    - `get_required_documents`
    - `list_missing_documents`
    - `create_task`
    - `update_task_progress`
    - `get_task_status`
    - `create_reminder`
    - `request_user_confirmation`
    - `escalate_to_human`
    - `export_user_data`
    - `delete_user_data`
- [ ] Grounded Prompting & Hallucination Prevention:
  - Source citations injection.
  - Grounding validation before responding.
  - Refusal to guess fees or unverified deadlines.
- [ ] Multilingual benchmark evaluation:
  - 50 evaluation scenarios across Tamil ("எனக்கு வருமானச் சான்றிதழ் வேண்டும்"), Tanglish ("Enakku first graduate certificate eppadi apply pandrathu"), and English.

### Milestone 3 — Product UI (React + Vite + Tailwind CSS)
- [ ] Modern, high-trust frontend application:
  - Design system with accessible typography, responsive mobile-first grid, subtle civic-grade UI (deep navy, emerald accents, saffron highlights, warm neutral backgrounds).
  - Language switcher (Tamil, Tanglish, English) with instant string localization.
- [ ] Views & Features:
  - Landing page (Hero, conversational query bar, category explorer, trust & privacy pillar, FAQ, emergency escalation).
  - AI Assistant Chat (streaming/structured card responses, source tags, document checklists, interactive action cards).
  - Service Catalog & Directory (filtering by department, category, target beneficiary, online status).
  - Service Detail View (prerequisites, official portals, verified fees/turnaround times).
  - Authenticated Citizen Dashboard (active application tasks, pending documents, scheduled reminders).
  - Task Progress & Action Plan Viewer.
  - Account, Privacy & DPDP Consent Controls (Export personal data, one-click deletion).

### Milestone 4 — Document Intelligence & Reminders
- [ ] Document processing pipeline:
  - Secure upload endpoint with MIME-type and size verification.
  - OCR abstraction (`OCRProviderInterface`) with Mock OCR and extensible cloud vision backend.
  - Document classifier and field extractor (e.g., extracting Name, Date of Issue, Certificate Number, Validity).
  - Document-to-Service requirement validator (identifying missing required documents).
  - Form data pre-filler and downloadable summary checklist.
- [ ] Reminder Engine:
  - Persistent reminder state machine.
  - Background task runner for reminder dispatching and follow-up alerts in Asia/Kolkata timezone.

### Milestone 5 — Admin & Knowledge Management
- [ ] Playbook editor & verification queue.
- [ ] Verification status lifecycle (`DRAFT`, `NEEDS_VERIFICATION`, `VERIFIED`, `RETIRED`).
- [ ] Audit logs viewer & anonymized analytics.
- [ ] Human escalation resolution view.

### Milestone 6 — External Integrations & Fallbacks
- [ ] WhatsApp Cloud API adapter with webhook validation & interactive simulator.
- [ ] Speech-to-Text and Text-to-Speech abstraction (Bhashini/Sarvam/Whisper/Mock).
- [ ] Production configuration (Dockerfiles, `docker-compose.yml`, environment configuration).

### Milestone 7 — Quality Assurance & Production Readiness
- [ ] Complete automated test suite execution (backend + frontend).
- [ ] Security threat model verification & DPDP compliance verification.
- [ ] Final implementation report and operational runbook.

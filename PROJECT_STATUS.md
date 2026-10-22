# Namma Seva Agent AI — Project Status

**Current Status:** Milestone 1 in progress (Foundation Setup & Architecture)  
**Date:** 2026-10-22  
**Region:** Tamil Nadu, India  
**Languages:** Tamil, Tanglish, English  

---

## 1. Environment & Workspace State

- **Workspace Root:** `e:\New folder`
- **Host OS:** Windows
- **Runtimes Detected:**
  - Python: 3.14.6
  - Node.js: v24.18.0
  - npm: 11.16.0
  - Git: 2.55.0.windows.3
  - Docker: Not detected on host (Container configs provided in `infrastructure/` and `docker-compose.yml`, native execution supported out of the box)
- **Database Engine:** SQLAlchemy supporting async SQLite (`sqlite+aiosqlite`) for zero-dependency local dev/tests, and PostgreSQL (`postgresql+asyncpg`) for production.
- **Virtual Environment:** Python `.venv` managed locally.

---

## 2. Milestone Progress Tracker

| Milestone | Scope | Status | Verification & Evidence |
|:---|:---|:---:|:---|
| **Milestone 1 — Foundation** | DB schema, models, playbook schema, YAML/JSON playbooks, deterministic dependency planner, service search | **IN PROGRESS** | Playbook validation suite, dependency graph tests, search tests |
| **Milestone 2 — AI Agent Engine** | LLM abstraction (Mock + Gemini/OpenAI), tool dispatcher, intent classifier, grounded prompt templates, evaluation harness | Pending | 50 benchmark evaluations across Tamil, Tanglish, English |
| **Milestone 3 — Product UI** | React + Vite + Tailwind CSS, responsive landing page, authenticated dashboard, AI conversation UI, task manager, service detail | Pending | Component rendering, flow tests, mobile viewport responsiveness |
| **Milestone 4 — Documents & Reminders** | Secure file upload, OCR adapter (Mock/Tesseract/Vision), document requirement matcher, reminder scheduler, prefilled PDF generator | Pending | OCR extraction tests, reminder scheduler tests |
| **Milestone 5 — Admin & Verification** | Playbook editor, source provenance inspector, verification status transitions (`DRAFT` $\to$ `NEEDS_VERIFICATION` $\to$ `VERIFIED`), audit logs | Pending | Admin authorization tests, status transition tests |
| **Milestone 6 — External Integrations** | WhatsApp Cloud API webhook adapter & simulator, Tamil/English Speech adapter, Object Storage adapter | Pending | Webhook signature verification tests, simulator tests |
| **Milestone 7 — Production Readiness** | End-to-end tests, security scan, PII redaction, threat model verification, CI pipeline, setup guide | Pending | Full pytest suite + frontend build pass |

---

## 3. Assumptions and External Dependencies

1. **Government Portal Automations:** Government of India and Tamil Nadu portals (e-Sevai, TNeGA, TNPDS, NSP) lack public open write APIs for direct autonomous submission without citizen intervention. Guided Mode (Level 1 & Level 2) is the primary deterministic paradigm.
2. **Citizen Credentials & OTPs:** The agent strictly **never** handles, stores, asks for, or relays OTPs, Aadhaar OTPs, passwords, or CAPTCHA answers.
3. **External AI & Cloud Services:** In development mode without active paid API keys, the system operates deterministically using clearly labeled mock adapters (`MockLLMProvider`, `MockOCRProvider`, `MockSpeechProvider`, `MockWhatsAppAdapter`).
4. **Data Privacy (DPDP Act 2023):** Citizen documents and PII are encrypted at rest, subject to explicit consent, purpose limitation, and one-click data deletion/export.

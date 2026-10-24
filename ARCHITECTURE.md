# Namma Seva Agent AI — System Architecture

## 1. System Overview

Namma Seva Agent is an extensible, AI-orchestrated civic assistance platform designed for the citizens of Tamil Nadu. It bridges the gap between complex governmental digital portals (such as e-Sevai, TNeGA, TNPDS, and the National Scholarship Portal) and citizens by providing a multilingual conversational guide in Tamil, Tanglish, and English.

```
                      +---------------------------------------+
                      |       Citizen Channels / Clients      |
                      |  - Web UI (React + Tailwind CSS)     |
                      |  - WhatsApp Business Cloud API        |
                      |  - Voice Adapter (Tamil/English STT)  |
                      +-------------------+-------------------+
                                          |
                                    REST / JSON
                                          v
                      +---------------------------------------+
                      |         FastAPI Gateway (/api/v1)     |
                      |  - Auth & RBAC (Citizen & Admin)      |
                      |  - Input Validation                   |
                      |  - [Planned: Token Bucket Rate Limit] |
                      |  - [Planned: Privacy Interceptor]     |
                      +-------------------+-------------------+
                                          |
        +---------------------------------+---------------------------------+
        |                                 |                                 |
        v                                 v                                 v
+------------------+            +-------------------+             +-------------------+
|  Agent AI Engine |            | Dependency Graph  |             | Document Pipeline |
| - Intent Router  |            | & Planner         |             | - File Upload     |
| - Tool Dispatcher|            | - DAG Resolution  |             | - [Demo Mock OCR] |
| - Provider Layer |            | - Cycle Detection |             | - Field Extractor |
|   (Mock Provider)|            | - Topological Sort|             | - Doc Matcher     |
+--------+---------+            +---------+---------+             +---------+---------+
         |                                |                                 |
         +--------------------------------+---------------------------------+
                                          |
                                          v
                      +---------------------------------------+
                      |         Service Playbook Engine       |
                      |  - Schema-validated YAML/JSON records |
                      |  - Verified Official Sources          |
                      |  - Verification Lifecycle Management  |
                      +-------------------+-------------------+
                                          |
                                          v
                      +---------------------------------------+
                      |           Persistence Layer           |
                      |  - SQLAlchemy 2.0 Async               |
                      |  - SQLite (Local Dev) / PostgreSQL    |
                      |  - [Planned: AES-256 Vault at rest]   |
                      +-------------------+-------------------+
```

---

## 2. Core Architectural Pillars

### A. Deterministic Playbook Engine
Government service rules (eligibility parameters, official documents, departmental authorities, fees, and links) are stored in validated JSON/YAML playbooks with strict schemas. The LLM is **never** permitted to hallucinate or fabricate eligibility requirements or fees. All answers must ground against verified playbook data and cite official sources.

### B. Dependency Graph & Topological Planning Engine
Complex civic tasks (such as applying for a Post-Matric Scholarship or First Graduate tuition fee concession) require prerequisite certificates (e.g., Community Certificate, Income Certificate, Nativity Certificate).
The planning engine constructs a Directed Acyclic Graph (DAG) of service dependencies and executes a deterministic topological sort to give the citizen a step-by-step sequential action plan.

### C. Human-in-the-Loop & Guided Submission
To maintain citizen safety and avoid violations of portal terms:
- The system uses **Guided Submission (Levels 1 & 2)**: generating checklists, pre-filling forms, explaining each official portal screen, and providing official links.
- The system **strictly forbids** asking for, storing, or handling citizen OTPs, passwords, or CAPTCHA answers.
- All consequential actions (data submission, document archiving, or data deletion) require explicit user consent.

### D. Multilingual First-Class Citizen Experience
The system is built from the ground up to understand:
- **Tamil** (தமிழ்): e.g., "எனக்கு முதல் தலைமுறை பட்டதாரி சான்றிதழ் பெற என்ன செய்ய வேண்டும்?"
- **Tanglish**: e.g., "Enakku income certificate apply panna enna docs venum?"
- **English**: e.g., "How do I apply for a community certificate online?"

---

## 3. Database Schema Design (Normalized Relational Model)

1. `users`: Citizen & Administrator accounts with hashed credentials and role assignments (`CITIZEN`, `REVIEWER`, `ADMIN`).
2. `user_consents`: Timestamped citizen consent records under the Digital Personal Data Protection (DPDP) Act 2023.
3. `service_playbooks`: Service identifier, bilingual titles, descriptions, department, category, verification status (`DRAFT`, `NEEDS_VERIFICATION`, `VERIFIED`, `RETIRED`), version, fee, processing time.
4. `service_sources`: Verified official URLs, government publishers, retrieval dates, and verification notes.
5. `service_dependencies`: Graph edges defining prerequisite service requirements.
6. `service_required_documents`: Required and optional documents for each service with validity criteria.
7. `user_tasks`: Active citizen application workflows with state machine transitions:
   - `DRAFT` $\to$ `NEEDS_INFORMATION` $\to$ `COLLECTING_DOCUMENTS` $\to$ `READY_FOR_USER_REVIEW` $\to$ `READY_TO_SUBMIT` $\to$ `SUBMITTED` $\to$ `TRACKING` $\to$ `COMPLETED` (or `BLOCKED`, `REJECTED`, `CANCELLED`).
8. `task_events`: Full immutable audit trail of state transitions.
9. `user_documents`: Uploaded document metadata, MIME type, storage path, OCR status, and extracted fields.
10. `reminders`: Citizen reminders scheduled in `Asia/Kolkata` timezone with recurrence and trigger status.
11. `audit_logs`: Security and access logs for all sensitive queries and data modifications.

# Namma Seva Agent AI — Security Architecture & Threat Model

## 1. Security Philosophy

In a civic assistance platform handling citizen documentation and government workflows, security, data integrity, and privacy are non-negotiable foundations.

### Absolute Invariants:
1. **Zero Secret / OTP Disclosure:** The system **never** prompts for, accepts, records, or forwards Aadhaar OTPs, portal passwords, bank pins, or CAPTCHA answers.
2. **Deterministic Authorization:** An LLM cannot override or bypass object-level access controls. User A cannot access User B's documents, tasks, or conversations under any circumstance.
3. **No Autonomous Submission (Zero L4 Claims):** The system generates copyable pre-fill sheets and step-by-step checklists. It does not perform autonomous submission to government portals and generates no fake government seals or certificates.
4. **Prompt Injection Isolation:** Document text extracted via OCR is categorized as strictly **untrusted data**. Extracted text is never fed into raw system instructions as executable directives.
5. **Full Citizen Data Sovereignty:** Citizens can view, export in JSON, or completely delete all personal records, tasks, and uploaded files on demand.

---

## 2. Threat Modeling Matrix: Implemented vs Planned

| Threat Category | Potential Attack Vector | Status | Defensive Control & Implementation Details |
|:---|:---|:---|:---|
| **Brute Force / Scraping** | Automated credential guessing or LLM quota exhaustion | **IMPLEMENTED (Wave 1)** | Safe IP resolution via `get_client_ip()` (never trusts `X-Forwarded-For` unless from `TRUSTED_PROXIES`; walks proxy chains right-to-left). In-memory token bucket rate limiting on `/auth/login`, `/auth/register`, `/chat`, `/documents/upload`, `/whatsapp/webhook`. |
| **Webhook Spoofing & Replay** | Forged Meta payloads or replayed WhatsApp messages | **IMPLEMENTED (Wave 1)** | Constant-time HMAC-SHA256 signature verification (`X-Hub-Signature-256`). Persistent database deduplication (`webhook_processed_messages` table). Decoupled async background processing. Retry-safe state transitions (`received` → `processing` → `processed`/`failed`). |
| **Document Exposure at Rest** | Physical disk theft or unauthorized host file inspection | **IMPLEMENTED (Wave 1)** | AES-256-GCM encryption with per-file 12-byte random nonce and 16-byte authentication tag. Bound Authenticated Additional Data (`AAD = f"{user_id}:{document_id}"`). Key versioning header (`b"NSEV1"`, `b"NSEV2"`) supporting zero-downtime rotation. Dedicated `DOC_ENCRYPTION_KEY`. |
| **Database Field-Level Exposure** | SQL dump exposes citizen phone number, name, or OCR data | **IMPLEMENTED (Wave 1)** | Field-level AES-256-GCM encryption for `User.full_name`, `User.phone_number`, and `UserDocumentModel.extracted_fields`. HMAC-SHA256 blind index (`phone_blind_index`) for deterministic lookups without storing plaintext phone numbers. Dedicated `FIELD_ENCRYPTION_KEY`. |
| **PII / Data Retention Abuse** | Citizen requests deletion under DPDP Act 2023 | **IMPLEMENTED (Wave 1)** | `DELETE /api/v1/auth/me/data` atomically purges citizen records across 8 tables and physically deletes files under `storage/uploads/{user_id}/`. Retains non-PII deletion receipt and preserves admin accountability logs. |
| **Malicious File Upload** | Executable/polyglot files disguised as images/PDFs | **IMPLEMENTED (Wave 1)** | Strict binary magic-byte inspection (PDF, PNG, JPEG, WebP), strict extension and declared MIME cross-matching, path traversal sanitization, and storage under isolated UUID filenames. |
| **Unauthorized Playbook Tampering** | Citizen modifies eligibility, fees, or official URLs | **IMPLEMENTED (Wave 1)** | Admin RBAC (`require_admin_user`). Database is the sole source of truth; disk writes are excluded from production request paths. Divergence detection and operator-only export. Invariant enforcement (`last_verified` is strictly null for unverified playbooks). Audit log trail. |
| **Unauthorized Access (IDOR)** | Attacker guesses `task_id` or `document_id` of another citizen | **IMPLEMENTED (Wave 0)** | Object-level authorization checks verify `record.user_id == current_user.id` on all authenticated operations. |
| **Prompt Injection via OCR** | Malicious text in uploaded document instructs LLM to bypass rules | **PLANNED (Wave 2)** | Document text will be parsed into structured JSON schemas before presentation to agent; prompt sandwiching and instruction/data separation guardrails. |
| **Distributed Rate Limiting** | Multi-worker uvicorn cluster bypasses local memory limits | **PLANNED (Wave 2)** | Redis-backed distributed token bucket with atomic Lua scripts. |

---

## 3. Client IP Resolution & Rate Limiting Architecture

### Safe Client IP Resolution (`get_client_ip`):
- **IP Spoofing Defense:** When `settings.TRUSTED_PROXIES` is empty (default), `X-Forwarded-For` and `X-Real-IP` headers are **never trusted**. The direct socket peer (`request.client.host`) is used unconditionally.
- **Trusted Reverse Proxy Chaining:** If `settings.TRUSTED_PROXIES` is configured (e.g., `["127.0.0.1", "10.0.0.0/8"]`), the proxy chain is evaluated right-to-left:
  1. If `request.client.host` is not in `TRUSTED_PROXIES`, forwarded headers are discarded.
  2. If `request.client.host` is in `TRUSTED_PROXIES`, `X-Forwarded-For` is parsed backwards to locate the first untrusted upstream IP, which represents the authentic client.

### Documented In-Memory Rate Limiting Limitations:
- **Process-Local State:** Token buckets are maintained in Python process heap memory.
- **Volatility on Restart:** Rate limiting counters reset when the server or worker restarts.
- **Multi-Worker / Clustered Scale:** When running multiple uvicorn workers or multi-container horizontal replicas, each worker maintains an independent token bucket. The effective rate limit is multiplied by the number of active processes.

### Production Roadmap & Redis Follow-Up:
In production multi-node clusters, in-memory rate limiting must be upgraded to:
1. A distributed Redis token bucket using atomic Lua `EVAL` scripts, OR
2. Edge rate limiting enforced at the reverse proxy or API gateway (NGINX `limit_req`, Cloudflare Rate Limiting, or AWS WAF).

---

## 4. Cryptographic Architecture: Key Separation, File & Field Encryption

### Target Database Environments:
- **Production Target:** **PostgreSQL 15+ with asyncpg** (`postgresql+asyncpg://...`), fully compatible with Alembic async migrations.
- **Development & Automated CI Target:** **SQLite 3.37+ with aiosqlite** (`sqlite+aiosqlite://...`), with enforced `PRAGMA foreign_keys=ON`.

### Strict Five-Way Key Separation (Fail-Closed Startup):
In production (`ENVIRONMENT=production` or `staging`), startup aborts immediately if any key is missing, insecure, or shared across purposes:
1. `SECRET_KEY`: Used exclusively for JWT access token cryptographic signing (HS256).
2. `DOC_ENCRYPTION_KEY`: Used exclusively for AES-256-GCM encryption of physical files at rest.
3. `FIELD_ENCRYPTION_KEY`: Used exclusively for field-level encryption (FLE) of citizen PII (name, phone, OCR fields).
4. `BLIND_INDEX_KEY`: Used exclusively for deterministic HMAC-SHA256 phone blind indexing.
5. `DELETION_PEPPER`: Dedicated high-entropy secret used exclusively for peppered HMAC-SHA256 deletion receipts.

```
+-------------------------------------------------------------------------------------------------------+
| Five-Way Key Separation Invariant:                                                                    |
| SECRET_KEY != DOC_ENCRYPTION_KEY != FIELD_ENCRYPTION_KEY != BLIND_INDEX_KEY != DELETION_PEPPER       |
| All keys must be strictly distinct and >= 32 characters (256-bit entropy) in production.              |
+-------------------------------------------------------------------------------------------------------+
```

### File-Level Encryption at Rest (AES-256-GCM + AAD Binding):
- **Binary Format:** `[4-byte 'NSEV' + 1-byte version] + [12-byte random nonce] + [ciphertext + 16-byte auth tag]`
- **Authenticated Additional Data (AAD) Binding:** Every file is encrypted with `AAD = f"{user_id}:{document_id}".encode("utf-8")`.
  - If an attacker attempts to copy or swap an encrypted file on disk to another citizen's account, AES-GCM tag verification fails (`InvalidTag`), completely preventing document ownership forgery.
- **Key Versioning & Zero-Downtime Rotation:**
  - Files are tagged with version headers (`b"NSEV1"`, `b"NSEV2"`).
  - The runtime maintains a versioned keyring (`_DOC_KEY_RING`). When decrypting, the engine extracts the version byte, selects the appropriate key, and verifies the authentication tag without requiring instantaneous batch re-encryption.
  - New writes dynamically adopt the primary key version indicated by `CURRENT_DOC_KEY_VERSION`.

### Field-Level Encryption (FLE) & Blind Index:
- **Sensitive Citizen Fields:** `User.full_name`, `User.phone_number`, and `UserDocumentModel.extracted_fields` are transparently encrypted before database storage via SQLAlchemy `TypeDecorator` (`EncryptedString` and `EncryptedJSON`).
- **Encrypted Field Format:** `FLE:<version>:<urlsafe_base64(nonce + ciphertext + tag)>`
- **HMAC-SHA256 Blind Index (`phone_blind_index`):**
  - Storing encrypted phone numbers prevents SQL equality searches (`SELECT * FROM users WHERE phone_number = ?`).
  - To preserve fast, deterministic citizen lookups (e.g. from WhatsApp incoming messages) without exposing plaintext phone numbers, the system computes a one-way HMAC-SHA256 blind index over canonicalized phone numbers (`91XXXXXXXXXX`) using dedicated `BLIND_INDEX_KEY`.
  - Database queries search exclusively on `phone_blind_index = ?`.
- **Blind Index Reindexing on Key Rotation:**
  - When rotating `BLIND_INDEX_KEY`, an operator runs the reindex CLI command:
    ```bash
    python -m backend.app.cli reindex-blind-index --key-version 2
    ```
  - This decodes user phone numbers in-memory via FLE and updates `phone_blind_index` to the new HMAC digest version without downtime.

---

## 5. Citizen Data Deletion & Audit Hygiene (Pending Legal Review)

> [!IMPORTANT]
> **Legal Notice:** All references to data erasure, retention horizons, and compliance under India's Digital Personal Data Protection (DPDP) Act 2023 are subject to formal legal review with designated cyber-law / faculty counsel. Code implementations provide technical mechanisms (cryptographic deletion, receipt generation, PII scrub), but do not constitute legal advice.

### `/api/v1/auth/me/data` Deletion Workflow:
When a citizen exercises their Right to Erasure:

1. **Peppered Deletion Receipt Generation (Zero PII):**
   - A `DeletionReceiptModel` record is generated containing:
     - `id`: Unique receipt UUID
     - `user_id_hash`: HMAC-SHA256 digest of citizen ID keyed with dedicated `DELETION_PEPPER` (cannot be brute-force guessed even if user IDs are sequential)
     - `deletion_timestamp`: UTC timestamp of purge execution
     - `request_channel`: Channel initiating deletion (`WEB`, `WHATSAPP`, etc.)
     - `consent_withdrawal_recorded`: Boolean flag confirming explicit consent revocation
     - `consent_withdrawal_evidence`: `{"legal_status": "PENDING_LEGAL_REVIEW", "action": "CITIZEN_CONSENT_REVOCATION_AND_DATA_PURGE"}`
     - `receipt_signature`: Cryptographic HMAC-SHA256 receipt signature keyed with `DELETION_PEPPER`
2. **Live Database Purge:** The system atomically purges all personal records linked to `user_id` across:
   - `users` (account credentials and profile)
   - `user_tasks` and `task_events` (application state)
   - `user_documents` (metadata and extracted OCR fields)
   - `reminders` (scheduled notifications)
   - `conversations` and `messages` (chat history)
   - `user_consents` (granted consents)
   - Citizen activity audit logs (`USER_LOGIN`, `DOCUMENT_UPLOAD`, etc.)
3. **Audit Hygiene on Preserved Administrative Accountability Logs:**
   - Administrative audit log entries (actions matching `PLAYBOOK_VERIFICATION_STATUS_CHANGE`, `ADMIN_USER_ROLE_CHANGE`, `ADMIN_OVERRIDE`) are preserved for state accountability.
   - However, **all citizen PII (name, phone, email, extracted fields) is recursively sanitized** from the `details` payload, replacing citizen identifiers with `"[REDACTED_PURGED_CITIZEN_PII]"`.
   - A post-purge database scan verifies zero instances of the citizen's PII remain across all preserved audit tables.
4. **Physical Disk Erasure:** All files stored in `storage/uploads/{user_id}/` and the directory itself are permanently deleted via secure recursive unlinking.

### Exact Legal-Review Questions for Faculty / Legal Counsel:
1. **Statutory Retention vs. Right to Erasure:** Under DPDP Act 2023 Section 12, what is the required statutory retention window for the non-PII deletion receipt and consent withdrawal evidence to defend against post-deletion regulatory audits?
2. **Consent Revocation Evidence Standard:** What specific metadata fields are required to constitute legally verifiable proof of consent withdrawal without retaining citizen PII?
3. **Receipt Contents & Anonymization:** Is an HMAC-SHA256 user hash using a secret pepper legally sufficient anonymization under DPDP Act 2023, or does the receipt itself need additional anonymization?
4. **Disaster Recovery Rolling Snapshots:** Clarify legal disclosure guidelines regarding cold backup retention windows (14-30 days) before full snapshot rotation and obligations around tombstone replay.

### Honest Retention & Trace Policies:
- **Application Logs:** Citizen phone numbers are masked (`+91 ******3456`). Message bodies, raw OCR payloads, and FLE fields are **never logged**. Tested and verified by automated test suites.
- **LLM Traces:** In development and benchmark evaluations, responses are generated locally using the deterministic mock provider. No citizen personal data or application documents are sent to external third-party model APIs without explicit user consent.
- **Cold Backups:** Offline database snapshots retain historical data for 14 to 30 days. On disaster recovery restoration, an automated post-restore tombstone replay script re-applies historical deletion receipts to ensure erased records are not resurrected.

---

## 6. Playbook Integrity & Verification Workflow

- **Source of Truth:** The **Database (`service_playbooks` table) is the sole ground truth**.
- **Disk Isolation on Request Paths:** HTTP API endpoints (`PATCH /admin/playbooks/{id}/status`) update the database and in-memory loader, but **never write to disk JSON files** in production.
- **Explicit Operator Export:** Disk JSON files can only be synchronized via explicit operator commands (`python -m backend.app.cli export-playbooks`) or migration scripts.
- **Divergence Detection:** The server logs a `WARNING` on startup if discrepancies are detected between disk definitions and database records.
- **Status Progression:** `DRAFT` → `NEEDS_VERIFICATION` → `VERIFIED` → `RETIRED`.
- **RBAC:** Only authenticated users with `role="ADMIN"` can modify playbook verification status.
- **Verification Invariant:** A playbook with `verification_status="NEEDS_VERIFICATION"` must carry `last_verified = null` and `verified_by = "PENDING_OFFICIAL_VERIFICATION"`. Only playbooks verified against official government orders carry a non-null verification timestamp.

---

## 7. Incident Response & Security Contact

For security inquiries or vulnerability reports, contact: `security@nammaseva.tn.gov.in` (Development Team: Namma Seva Project Lead).

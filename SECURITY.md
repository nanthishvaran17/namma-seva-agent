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
| **Webhook Spoofing & Replay** | Forged Meta payloads or replayed WhatsApp messages | **IMPLEMENTED (Wave 1)** | Constant-time HMAC-SHA256 signature verification (`X-Hub-Signature-256`). Persistent database deduplication (`webhook_processed_messages` table). Decoupled async background processing. |
| **Document Exposure at Rest** | Physical disk theft or unauthorized host file inspection | **IMPLEMENTED (Wave 1)** | AES-256-GCM encryption with per-file 12-byte random nonce and 16-byte authentication tag. Dedicated `DOC_ENCRYPTION_KEY` separate from `SECRET_KEY`. Fail-closed production startup. |
| **PII / Data Retention Abuse** | Citizen requests deletion under DPDP Act 2023 | **IMPLEMENTED (Wave 1)** | `DELETE /api/v1/auth/me/data` atomically purges all database rows across 9 tables and physically deletes all files on disk under `storage/uploads/{user_id}/`. |
| **Malicious File Upload** | Executable/polyglot files disguised as images/PDFs | **IMPLEMENTED (Wave 1)** | Strict binary magic-byte inspection (PDF, PNG, JPEG, WebP), strict extension and declared MIME cross-matching, path traversal sanitization, and storage under isolated UUID filenames. |
| **Unauthorized Playbook Tampering** | Citizen modifies eligibility, fees, or official URLs | **IMPLEMENTED (Wave 1)** | Admin RBAC (`require_admin_user`), status synchronization across in-memory catalog, SQLite/PostgreSQL DB, and disk JSON. Invariant enforcement (`last_verified` is strictly null for unverified playbooks). Audit log trail (`who`, `when`, `old_status`, `new_status`). |
| **Unauthorized Access (IDOR)** | Attacker guesses `task_id` or `document_id` of another citizen | **IMPLEMENTED (Wave 0)** | Object-level authorization checks verify `record.user_id == current_user.id` on all authenticated operations. |
| **Prompt Injection via OCR** | Malicious text in uploaded document instructs LLM to bypass rules | **PLANNED (Wave 2)** | Document text will be parsed into structured JSON schemas before presentation to agent; prompt sandwiching and instruction/data separation guardrails. |
| **Database Field-Level Encryption** | SQL dump exposes citizen phone number or name | **PLANNED (Wave 2)** | Field-level envelope encryption for sensitive columns (`phone_number`, `full_name`) in the database. |
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

## 4. Document Encryption at Rest (AES-256-GCM)

### Key Separation & Fail-Closed Startup:
- Citizen documents are encrypted before writing to disk using **AES-256-GCM**.
- The encryption key is loaded from the `DOC_ENCRYPTION_KEY` environment variable. It is strictly separate from `SECRET_KEY` (which signs JWTs).
- In production (`ENVIRONMENT=production` or `staging`), startup aborts immediately if `DOC_ENCRYPTION_KEY` is missing, default, or under 32 characters.

### Key Rotation Runbook:
1. To rotate `DOC_ENCRYPTION_KEY`, run a dual-key re-encryption migration script:
   - Provide `OLD_DOC_ENCRYPTION_KEY` and `NEW_DOC_ENCRYPTION_KEY`.
   - The script decrypts each file under `storage/uploads/` using the old key, verifies the GCM authentication tag, re-encrypts with a fresh 12-byte random IV using the new key, and writes the ciphertext atomically.
2. Update `DOC_ENCRYPTION_KEY` in production environment / secret manager and restart instances.

### Key-Loss Consequence:
> [!CAUTION]
> **Irreversible Data Loss:** AES-256-GCM provides authenticated ciphertext with no backdoor. If `DOC_ENCRYPTION_KEY` is lost, deleted, or overwritten without a backup, **all stored citizen documents are permanently unrecoverable**. Regular encrypted key backups in a hardware security module (HSM) or cloud KMS (Google Cloud KMS / AWS KMS) are mandatory.

---

## 5. Data Deletion (DPDP Act 2023) & Backup Retention Policy

### `/api/v1/auth/me/data` Deletion Scope:
When a citizen invokes `DELETE /api/v1/auth/me/data`:
1. **Live Database Purge:** The system atomically purges all records linked to `user_id` across:
   - `users`
   - `user_tasks`
   - `task_events`
   - `user_documents`
   - `reminders`
   - `conversations`
   - `messages`
   - `user_consents`
   - `audit_logs`
2. **Physical Disk Erasure:** All files stored in the citizen's directory (`storage/uploads/{user_id}/`) and the directory itself are permanently deleted from disk.
3. **Session Invalidation:** The citizen's token is immediately rendered invalid as the underlying user record no longer exists.

### Honest Backup Retention Disclosure:
While live database rows and physical storage files are purged immediately upon request:
- **Cold Backups / Snapshots:** Offline database snapshots, WAL archives, and disaster-recovery object storage backups retain historical cold copies until their natural rolling retention window expires (typically 14 to 30 days depending on infrastructure configuration).
- **Disaster Recovery Safeguard:** Cold backups are not surgically altered. In the event of a disaster recovery database restoration, an automated post-restore tombstone replay script re-applies all historical deletion logs to ensure deleted citizen records are not inadvertently resurrected.

---

## 6. Playbook Integrity & Verification Workflow

- **Status Progression:** `DRAFT` → `NEEDS_VERIFICATION` → `VERIFIED` → `RETIRED`.
- **RBAC:** Only authenticated users with `role="ADMIN"` or `role="REVIEWER"` can modify playbook status.
- **Verification Invariant:** A playbook with `verification_status="NEEDS_VERIFICATION"` must carry `last_verified = null` and `verified_by = "PENDING_OFFICIAL_VERIFICATION"`. Only playbooks verified against official government orders carry a non-null verification timestamp.
- **Three-Tier Persistence:** Status changes update:
  1. In-memory catalog (`playbook_loader.catalog`)
  2. Database model (`service_playbooks`)
  3. JSON file on disk (`knowledge/playbooks/{service_id}.json`)
- **Immutable Audit Trail:** All status updates record an audit log entry detailing who made the change, when, previous status, new status, and review notes.

---

## 7. Incident Response & Security Contact

For security inquiries or vulnerability reports, contact: `security@nammaseva.tn.gov.in` (Development Team: Namma Seva Project Lead).

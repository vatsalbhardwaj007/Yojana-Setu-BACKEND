# YojanaSetu - Backend & Rules Progress Status

**Role:** Member 2 — Backend & Rules  
**Repository:** `Yojana-Setu-BACKEND`  
**Current Milestone:** Phase 3 Complete (Backend API Layer)  
**Last Updated:** September 4, 2026  

---

## 1. Executive Summary

Member 2 is responsible for the **FastAPI backend, Supabase/PostgreSQL database, User/Profile APIs, Scheme APIs, deterministic Eligibility Engine, Reason Codes, and Recommendation/Ranking logic**.

At this checkpoint, **Phase 3 (Backend API Layer)** is complete:
- Exposed full suite of stable REST APIs required by M1 (Frontend), M3 (AI/Search), and M4 (WhatsApp/Data).
- **Citizen Profile Management (`POST /profile`, `GET /profile`, `PUT /profile`)**:
  - Secure profile storage and recursive sanitization (strips Aadhaar numbers, passwords, OTPs, bank credentials).
  - Deep-merging partial updates without silently discarding existing citizen fields.
- **Schemes Catalog & Details (`GET /schemes`, `GET /schemes/{scheme_id}`)**:
  - Deterministic filtering across `scheme_type`/`category`, `status`, `ministry`, `search` text, `target_group`, and `state`.
  - Pagination with `{ "items": [...], "total": N }` contract alongside legacy list compatibility.
  - Dual lookup support by canonical snake_case `scheme_code`, database UUID, or common aliases (e.g. `pm_jay`, `pmay_u`).
- **Eligibility Engine Integration (`POST /eligibility/check`)**:
  - Verified and strictly preserved pure deterministic Phase 2 engine.
  - Zero AI interference; operates directly on M4 rule data.
- **Documents & Tutorial APIs (`GET /schemes/{scheme_id}/documents`, `GET /schemes/{scheme_id}/tutorial`)**:
  - Direct database truth from `scheme_documents` and `tutorial_steps` (ordered `step_number ASC`).
- **Deterministic Recommendations (`POST /schemes/recommend`)**:
  - Pure metadata/criteria-based relevance scoring without LLMs or vector embeddings (M3 owns AI).
  - Prominent non-legal disclaimer explicitly stating that recommendations do not constitute legal eligibility.
- **Automated Test Suite**: **65 automated tests** passing with 100% success in <0.9s.

---

## 2. Completed Work (Phases 0, 1, 2 & 3)

| Component | Status | Description / Deliverable |
| :--- | :---: | :--- |
| **Repository Setup** | ✅ Done | Initialized `Yojana-Setu-BACKEND` on branch `feature/backend` |
| **Directory Skeleton** | ✅ Done | Modular layout (`api`, `core`, `db`, `models`, `schemas`, `services`, `rules`, `tests`, `data`, `scripts`, `supabase`) |
| **App Initialization** | ✅ Done | `app/main.py` with FastAPI lifespan, CORS middleware, `/health`, `/schemes`, `/profile`, and `/eligibility/check` |
| **Configuration Layer** | ✅ Done | `app/core/config.py` with Pydantic v2 `BaseSettings` |
| **M4 Data Layer Integration** | ✅ Done | 15 canonical scheme JSONs, schemas, canonical enums, validation scripts, Supabase migrations |
| **Data Contracts & Schemas** | ✅ Done | Schemas for schemes, eligibility, profiles (`app/schemas/profile.py`), catalog & recommendation (`app/schemas/catalog.py`) |
| **Database Models & Tables** | ✅ Done | 6 scheme tables + `user_profiles` table in `app/db/session.py` |
| **Repository Layer** | ✅ Done | `SchemeRepository` with paged filtering + alias resolution, `ProfileRepository` with deep-merge |
| **Service Layer** | ✅ Done | `SchemeService`, `EligibilityService`, `ProfileService`, `RecommendationService` |
| **Eligibility Engine** | ✅ Done | Pure deterministic engine with 10 operators, exclusion handling, missing fields tracking, and reason codes |
| **Profile REST APIs** | ✅ Done | `POST /profile`, `GET /profile`, `PUT /profile` with recursive sanitization |
| **Catalog & Detail REST APIs** | ✅ Done | `GET /schemes`, `GET /schemes/{id}`, `GET /schemes/{id}/documents`, `GET /schemes/{id}/tutorial` |
| **Recommendation REST API** | ✅ Done | `POST /schemes/recommend` with deterministic multi-factor profile scoring + compliance disclaimer |
| **Automated Test Suite** | ✅ Done | 65 pytest tests passing across all unit, engine, repository, and Phase 3 API integration scenarios |

---

## 3. What Has NOT Been Implemented (By Design)

Per blueprint specifications and Phase 3 boundaries, the following are intentionally deferred:
- ❌ No AI / vector embeddings / semantic search / LLM ranking (Member 3 responsibility)
- ❌ No WhatsApp integration / Webhooks (Member 4 responsibility)
- ❌ No frontend UI / React components (Member 1 responsibility)
- ❌ No government API integrations / automated form submission (Out of scope)
- ❌ No collection of Aadhaar numbers, OTPs, passwords, or bank credentials (Strict security constraint)

---

## 4. Current Blueprint Alignment & Team Roadmap

| Phase | Focus | Owner | Current Status for Member 2 |
| :--- | :--- | :---: | :--- |
| **Phase 0** | Foundation & Scaffolding | M2 | ✅ Completed |
| **Phase 1** | Scheme data + Backend integration | **M4 + M2** | ✅ Completed (15 schemes, 6 tables, repository & APIs ready) |
| **Phase 2** | Deterministic Eligibility Engine + Reason Codes | **M2** | ✅ Completed (Generic engine, all 10 operators, `/eligibility/check`) |
| **Phase 3** | Backend API Layer | **M2** | ✅ Completed (Profile, Schemes, Docs, Tutorial, Recommend, Eligibility) |
| **Phase 4** | Frontend Foundation & AI Search Integration | M1 + M3 | — (M1/M3 consume M2's completed backend APIs) |
| **Phase 5** | Document Readiness & Tutorials | M1 + M4 | — (APIs exposed and verified) |
| **Phase 6** | Voice + WhatsApp | M3 + M4 | — (APIs exposed and verified) |
| **Phase 7** | Integration + Testing + Polish | All | ⚪ Future |

---

## 5. Cross-Team Synchronization & Dependencies

1. **Member 1 (Frontend / UI / UX):**
   - 🟢 **Ready to Consume:**
     - `GET /schemes`: paginated scheme catalog with query filters (`category`, `search`, `state`, etc.).
     - `GET /schemes/{scheme_id}`: comprehensive scheme detail by code, UUID, or alias.
     - `POST /profile`, `GET /profile`, `PUT /profile`: citizen profile store and partial updates.
     - `POST /schemes/recommend`: personalized recommendation list with match reasons and relevance scores.
     - `POST /eligibility/check`: deterministic eligibility decision, reason codes, and missing field prompts.
     - `GET /schemes/{scheme_id}/documents`: checklist of mandatory and optional required documents.
     - `GET /schemes/{scheme_id}/tutorial`: step-by-step application guidance ordered by `step_number`.
2. **Member 3 (AI / Search):**
   - 🟢 **Ready to Consume:** Deterministic eligibility verification (`POST /eligibility/check`) and metadata recommendations (`POST /schemes/recommend`) can be invoked directly by AI tools.
3. **Member 4 (Data / WhatsApp):**
   - 🟢 **Ready to Consume:** WhatsApp bot can maintain user profile state via `/profile` and check eligibility via `/eligibility/check`.

---

## 6. Team Sync & Agent Comparison Prompt

*Copy and paste the block below into your team chat or AI agent to get an instant cross-team status sync:*

```text
Here is the current status for Member 2 (Backend & Rules) of the YojanaSetu project:

- Role: Member 2 (Backend & Rules: FastAPI, Supabase/PostgreSQL, Eligibility Engine, REST APIs)
- Repository: Yojana-Setu-BACKEND
- Branch: feature/backend
- Current Milestone: Phase 3 Complete (Backend API Layer) — 100% Passed (65/65 tests)
- Completed Deliverables:
  1. Full backend architecture and modular layout (api, core, db, models, schemas, services, rules, tests, data, scripts, supabase).
  2. M4 Canonical Data Layer integrated: 15 verified schemes, JSON schemas, canonical enums, validation scripts, Supabase migrations.
  3. Relational database session (app/db/session.py) supporting 6 scheme tables and user_profiles table.
  4. Repositories: SchemeRepository (advanced filtering + alias resolution) and ProfileRepository (deep-merge updates).
  5. Services: SchemeService, EligibilityService, ProfileService (recursive sanitization), RecommendationService (deterministic profile matching).
  6. APIs exposed at both root level and /api/v1:
     - Profile: POST /profile, GET /profile, PUT /profile
     - Schemes: GET /schemes (paged with total), GET /schemes/{scheme_id} (code/UUID/alias)
     - Documents: GET /schemes/{scheme_id}/documents
     - Tutorial: GET /schemes/{scheme_id}/tutorial
     - Recommendations: POST /schemes/recommend
     - Eligibility: POST /eligibility/check (10 operators, exclusions, reason codes)
     - Health: GET /health
  7. Deterministic Recommendation Engine: metadata-based scoring across occupation, income, caste, state, and landholding attributes + legal disclaimer.
  8. Full test suite with 65 passing tests (test_phase3_api, test_eligibility_engine, test_eligibility_api, test_rules_evaluator, test_schemes, test_health).
- Security & Compliance:
  - Recursive stripping of Aadhaar numbers, passwords, OTPs, and bank credentials.
  - Zero hardcoding of scheme logic; database rules remain the single source of truth.
  - No LLM/AI used for eligibility decisions.
- Cross-Team Readiness:
  - M1 (Frontend): Can consume all catalog, profile, recommendation, and eligibility endpoints.
  - M3 (AI / Search): Can invoke deterministic backend APIs.
  - M4 (Data / WhatsApp): Can verify citizen eligibility and retrieve scheme tutorials over chat.
```

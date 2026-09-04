# YojanaSetu - Backend & Rules Progress Status

**Role:** Member 2 — Backend & Rules  
**Repository:** `Yojana-Setu-BACKEND`  
**Current Milestone:** Phase 1 Complete (Data & Backend Integration) / Ready for Phase 2  
**Last Updated:** September 4, 2026  

---

## 1. Executive Summary

Member 2 is responsible for the **FastAPI backend, Supabase/PostgreSQL database, User/Profile APIs, Scheme APIs, deterministic Eligibility Engine, Reason Codes, and Recommendation/Ranking logic**.

At this checkpoint, **Phase 1 (Data & Backend Integration)** is complete:
- M4's canonical scheme data layer (15 verified schemes, JSON schemas, canonical values, SQL migrations) has been fully integrated into the backend.
- The 6 canonical tables (`schemes`, `scheme_rules`, `scheme_documents`, `tutorial_steps`, `scheme_verification`, `scheme_profile_fields`) are represented cleanly in Pydantic schemas, database entity models, and the repository layer.
- Backend data access layer can retrieve complete scheme details, rules (separated into eligibility vs exclusion), documents, tutorial steps, verification history, and profile fields.
- 18 automated tests are in place and passing (100% test pass rate).
- Ready for Phase 2 (Deterministic Eligibility Engine & Reason Codes).

---

## 2. Completed Work (Phase 0 & Phase 1)

| Component | Status | Description / Deliverable |
| :--- | :---: | :--- |
| **Repository Setup** | ✅ Done | Initialized `Yojana-Setu-BACKEND` on branch `feature/backend` |
| **Directory Skeleton** | ✅ Done | Modular layout (`api`, `core`, `db`, `models`, `schemas`, `services`, `rules`, `tests`, `data`, `scripts`, `supabase`) |
| **App Initialization** | ✅ Done | `app/main.py` with FastAPI, lifespan DB initialization, CORS middleware, and `/health` route |
| **Configuration Layer** | ✅ Done | `app/core/config.py` with Pydantic v2 `BaseSettings` reading environment variables and project paths |
| **M4 Data Layer Integration** | ✅ Done | 15 canonical scheme JSONs, schemas, canonical enums, validation scripts, Supabase migrations |
| **Data Contracts & Schemas** | ✅ Done | `app/schemas/scheme.py` matching M4 6-table canonical structure |
| **Entity Models** | ✅ Done | `app/models/scheme.py` mapping relational tables |
| **Relational DB & Session** | ✅ Done | `app/db/session.py` with self-contained relational engine + Supabase connector |
| **Repository Layer** | ✅ Done | `app/repositories/scheme_repository.py` for queries across all 6 tables |
| **Service Layer** | ✅ Done | `app/services/scheme_service.py` with `SchemeNotFoundError` and query methods |
| **Scheme REST APIs** | ✅ Done | `app/api/v1/schemes.py` endpoints for listing, details, rules, docs, tutorials, profile fields |
| **Testing Suite** | ✅ Done | 18 pytest tests passing across all 10 Phase 1 requirements + health check |

---

## 3. What Has NOT Been Implemented (By Design)

Per blueprint and Phase 1 specifications, the following are intentionally deferred to subsequent phases:
- ❌ No eligibility evaluation engine yet (Phase 2 priority)
- ❌ No profile management / user profile CRUD endpoints (Phase 2)
- ❌ No recommendation ranking logic (Phase 2)
- ❌ No AI / vector embeddings / semantic search (Member 3 responsibility)
- ❌ No WhatsApp integration (Member 4 responsibility)

---

## 4. Current Blueprint Alignment & Team Roadmap

| Phase | Focus | Owner | Current Status for Member 2 |
| :--- | :--- | :---: | :--- |
| **Phase 0** | Foundation & Scaffolding | M2 | ✅ Completed |
| **Phase 1** | Scheme data + Backend integration | **M4 + M2** | ✅ Completed (15 schemes, 6 tables, repository & APIs ready) |
| **Phase 2** | Deterministic Eligibility Engine + Reason Codes | **M2** | 🟡 **Next Immediate Priority** |
| **Phase 3** | Frontend foundation + Core flow | M1 | — (M1 consuming M2's APIs) |
| **Phase 4** | Reverse search + Grounded explainer | M3 | — (M3 integrating embeddings with scheme records) |
| **Phase 5** | Document readiness + Tutorials | M1 + M4 | — (APIs exposed in Phase 1) |
| **Phase 6** | Voice + WhatsApp | M3 + M4 | — |
| **Phase 7** | Integration + Testing + Polish | All | ⚪ Future |

---

## 5. Upcoming Work for Member 2 (Phase 2 Focus)

1. **Deterministic Eligibility Engine (`app/rules/`):**
   - Implement evaluator supporting canonical operators: `=`, `!=`, `>=`, `<=`, `>`, `<`, `in`, `not_in`, `exists`, `between`.
   - Logic: AND-only eligibility rules + disqualifying exclusion rules (disqualification overrides eligibility).
   - Categorization: `ELIGIBLE`, `POTENTIALLY_ELIGIBLE` (missing required fields / incomplete profile), `NOT_ELIGIBLE`.
   - Explainability: Human-readable pass/fail reason codes mapped to evaluated rules and citizen profile attributes.
2. **Citizen Profile Contracts & Services (`app/schemas/profile.py`, `app/services/profile_service.py`):**
   - Profile fields aligned with canonical scheme requirements (`age`, `annual_income`, `state`, `gender`, `category`, `occupation`, etc.).
   - Profile validation and persistence.
3. **Eligibility Check & Recommendation APIs (`app/api/v1/eligibility.py`):**
   - `POST /api/v1/eligibility/check`: Evaluate single scheme or full catalog against citizen profile.
   - `POST /api/v1/schemes/recommend`: Return ranked eligible schemes with match scoring and reason codes.
4. **User / Profile Management APIs (`app/api/v1/profile.py`):**
   - `POST /api/v1/profile`, `GET /api/v1/profile`, `PUT /api/v1/profile`.

---

## 6. Cross-Team Synchronization & Dependencies

1. **Member 4 (Data / WhatsApp):**
   - ✅ **Received & Integrated:** 15 verified canonical scheme JSONs, schemas, SQL migrations, and seed scripts.
   - 🟢 **Next Sync:** Ensure any new schemes or rule updates continue to pass `scripts/validate_data.py`.
2. **Member 1 (Frontend / UI / UX):**
   - 🟢 **Ready to Consume:** Scheme catalog and details can now be fetched directly from:
     - `GET /api/v1/schemes`
     - `GET /api/v1/schemes/{scheme_code}`
     - `GET /api/v1/schemes/{scheme_code}/rules`
     - `GET /api/v1/schemes/{scheme_code}/documents`
     - `GET /api/v1/schemes/{scheme_code}/tutorials`
     - `GET /api/v1/schemes/{scheme_code}/profile-fields`
   - 🟡 **Next Sync:** Finalize citizen onboarding form fields matching `scheme_profile_fields`.
3. **Member 3 (AI / Search):**
   - 🟢 **Ready to Consume:** M4 canonical scheme records and metadata are available for embedding generation and semantic search indexing.
   - 🟡 **Next Sync:** Clarify reverse-search integration contract (direct backend proxy or AI microservice hook).

---

## 7. Team Sync & Agent Comparison Prompt

*Copy and paste the block below into your team chat or AI agent to get an instant cross-team status sync:*

```text
Here is the current status for Member 2 (Backend & Rules) of the YojanaSetu project:

- Role: Member 2 (Backend & Rules: FastAPI, Supabase/PostgreSQL, Eligibility Engine)
- Repository: Yojana-Setu-BACKEND
- Branch: feature/backend
- Current Milestone: Phase 1 Complete (Data & Backend Integration) — 100% Passed (18/18 tests)
- Completed Deliverables:
  1. Full backend architecture and modular layout (api, core, db, models, schemas, services, rules, tests, data, scripts, supabase).
  2. M4 Canonical Data Layer integrated: 15 verified schemes, JSON schemas, canonical enums, validation scripts, Supabase migrations.
  3. Pydantic contracts (app/schemas/scheme.py) and entity models (app/models/scheme.py) for all 6 tables (schemes, scheme_rules, scheme_documents, tutorial_steps, scheme_verification, scheme_profile_fields).
  4. Relational database session (app/db/session.py) with deterministic UUIDv5 generation and Supabase client connector.
  5. Repository (app/repositories/scheme_repository.py) and service layer (app/services/scheme_service.py) supporting complete scheme retrieval, eligibility vs exclusion rule separation, documents, tutorials, verification, and profile fields.
  6. Operational REST APIs under /api/v1/schemes with full filtering and 404 error handling.
  7. Automated test suite (app/tests/test_schemes.py & test_health.py) with 18 passing tests.
- What is NOT Implemented (By Design):
  Eligibility engine calculations and profile scoring (deferred to Phase 2 to keep phases clean).
- Immediate Next Focus (Phase 2):
  1. Generic deterministic eligibility engine supporting canonical operators (=, !=, >=, <=, >, <, in, not_in, exists, between).
  2. Explainable reason code generator and pass/fail summary cards.
  3. Citizen profile schemas and eligibility evaluation endpoints (POST /api/v1/eligibility/check).
- Current Cross-Team Readiness:
  - M1 (Frontend): APIs ready to consume scheme lists, details, documents, tutorials, and profile field requirements.
  - M3 (AI / Search): Canonical scheme JSONs ready for embedding generation.
  - M4 (Data): Data layer successfully integrated and verified via validate_data.py.
```

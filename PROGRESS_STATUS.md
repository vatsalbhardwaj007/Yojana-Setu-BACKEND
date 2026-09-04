# YojanaSetu - Backend & Rules Progress Status

**Role:** Member 2 — Backend & Rules  
**Repository:** `Yojana-Setu-BACKEND`  
**Current Milestone:** Phase 0 Complete / Ready for Phase 1 & 2  
**Last Updated:** September 1, 2026  

---

## 1. Executive Summary

Member 2 is responsible for the **FastAPI backend, Supabase/PostgreSQL database, User/Profile APIs, Scheme APIs, deterministic Eligibility Engine, Reason Codes, and Recommendation/Ranking logic**.

At this checkpoint, the entire **backend project skeleton and architectural foundation** have been established, strictly avoiding mock assumptions or premature business logic until cross-team contracts (Phase 1) are aligned with Member 4 (Data) and Member 1 (Frontend).

---

## 2. Completed Work (Phase 0 — Foundation & Scaffolding)

| Component | Status | Description / Deliverable |
| :--- | :---: | :--- |
| **Repository Setup** | ✅ Done | Cloned and initialized `Yojana-Setu-BACKEND` |
| **Directory Skeleton** | ✅ Done | Created clean, modular layout (`api`, `core`, `db`, `models`, `schemas`, `services`, `rules`, `tests`, `data`) |
| **App Initialization** | ✅ Done | `app/main.py` configured with FastAPI, CORS middleware, and `/health` route |
| **Configuration Layer** | ✅ Done | `app/core/config.py` with Pydantic v2 `BaseSettings` reading environment variables |
| **Environment Template** | ✅ Done | `.env.example` created with Supabase, PostgreSQL, and host config placeholders |
| **Dependencies** | ✅ Done | `requirements.txt` configured with FastAPI, Uvicorn, Supabase, SQLAlchemy, Pydantic, Pytest |
| **Git Hygiene** | ✅ Done | `.gitignore` updated with Python, virtualenvs, IDE, and cache exclusions |
| **Testing Setup** | ✅ Done | `app/tests/test_health.py` created and verified passing with `pytest` |
| **Documentation** | ✅ Done | `README.md` and `data/README.md` added with architecture guide and data folder guidelines |

---

## 3. What Has NOT Been Implemented (By Design)

Per team guidelines and blueprint requirements, the following are intentionally deferred:
- ❌ No hardcoded API endpoints or routes (waiting on API contracts)
- ❌ No database schemas or table migrations (waiting on Scheme schema alignment)
- ❌ No mock eligibility logic (must be data-driven as per blueprint, not hardcoded if-else)
- ❌ No dummy scheme data in code (all scheme data will live in `data/` or Supabase)

---

## 4. Current Blueprint Alignment & Team Roadmap

According to the **YojanaSetu Execution Plan (Page 15 of Blueprint)**:

| Phase | Focus | Owner | Current Status for Member 2 |
| :---: | :--- | :---: | :--- |
| **Phase 1** | Scheme schema + 8–15 curated records | **M4 + M2** | 🟡 **Next Immediate Priority:** Agree on canonical Scheme JSON & rule representation |
| **Phase 2** | Eligibility engine + Scheme APIs | **M2** | ⚪ Queued: Build deterministic rule engine & Postman tests |
| **Phase 3** | Frontend foundation + Core flow | M1 | — (M1 consuming M2's APIs) |
| **Phase 4** | Reverse search + Grounded explainer | M3 | — (M3 integrating embeddings with scheme records) |
| **Phase 5** | Document readiness + Tutorials | M1 + M4 | ⚪ Queued: Expose `/schemes/{id}/documents` & `/tutorial` |
| **Phase 6** | Voice + WhatsApp | M3 + M4 | ⚪ Queued: Ensure backend webhook route `/webhook/whatsapp` is ready |
| **Phase 7** | Integration + Testing + Polish | All | ⚪ Future |

---

## 5. Upcoming Work for Member 2 (Phase 1 & 2 Tasks)

1. **Database Models & Supabase Initialization (`app/models/`, `app/db/`):**
   - Tables: `users`, `user_profiles`, `schemes`, `eligibility_rules`, `documents`, `tutorial_steps`, `saved_schemes`
2. **Pydantic Schemas (`app/schemas/`):**
   - Profile payload (state, age, income, category, occupation, education)
   - Scheme response & detail schemas
   - Eligibility check request & explainable response format
3. **Deterministic Eligibility Engine (`app/rules/`):**
   - Rule evaluator supporting operators: `IN`, `BETWEEN`, `<=`, `>=`, `==`
   - Classification: `Eligible`, `Potentially Eligible` (missing required fields), `Not Eligible`
   - Explainability generator: Reason codes and pass/fail cards
4. **Recommendation / Ranking Service (`app/services/`):**
   - Sorting schemes by relevance match to profile
5. **API Endpoints (`app/api/`):**
   - `POST /profile`, `GET /profile`, `PUT /profile`
   - `GET /schemes`, `GET /schemes/{id}`
   - `POST /eligibility/check`, `POST /schemes/recommend`
   - `GET /schemes/{id}/documents`, `GET /schemes/{id}/tutorial`

---

## 6. Blockers / Dependencies Needed from Teammates

To start Phase 1 & 2 implementation smoothly, Member 2 requires:

1. **From Member 4 (Data / WhatsApp):**
   - The agreed **Scheme JSON schema** and sample records (8–15 curated schemes).
   - The list of eligibility rule fields & operator formats (e.g., `annual_income <= 250000`, `state IN [...]`).
2. **From Member 1 (Frontend):**
   - Confirmation on profile field naming convention (camelCase vs snake_case) for the onboarding form.
3. **From Member 3 (AI / Search):**
   - Agreement on whether Reverse Search will be a direct backend route (`POST /schemes/search`) or an AI microservice call.

---

## 7. ChatGPT Team Comparison Prompt

*Copy and paste the block below into ChatGPT alongside your teammates' status updates to get an instant cross-team sync:*

```text
Here is the current status for Member 2 (Backend & Rules) of the YojanaSetu project:

- Role: Member 2 (Backend & Rules: FastAPI, Supabase/PostgreSQL, Eligibility Engine)
- Repository: Yojana-Setu-BACKEND
- Status: Phase 0 Completed, Ready for Phase 1 & Phase 2.
- Completed:
  1. Full backend architecture and directory structure (api, core, db, models, schemas, services, rules, tests, data).
  2. FastAPI app setup with CORS middleware and operational /health endpoint.
  3. Environment management (.env.example, Pydantic BaseSettings in app/core/config.py).
  4. Core dependencies installed and verified (requirements.txt, pytest passing).
  5. Clean Git setup (.gitignore updated for Python/venv).
  6. Documented project responsibilities and data folder guidelines.
- Intentionally deferred:
  No hardcoded API endpoints, no assumed DB tables, and no hardcoded rule if-statements (keeping it modular for Phase 1 team contracts).
- Next Deliverables:
  1. Finalize Scheme JSON & Rule schema with Member 4 (Data).
  2. Implement Supabase/PostgreSQL models and migrations.
  3. Build deterministic rule engine (Eligible/Potentially Eligible/Not Eligible + reason codes).
  4. Implement Profile and Scheme APIs.
- Needed from Team:
  - Member 4: 8-15 curated scheme records and rule data format.
  - Member 1: Profile builder field requirements.
  - Member 3: Reverse search endpoint expectations.

Please compare this with the progress of my teammates:
[PASTE YOUR TEAMMATES' UPDATES HERE]

Provide:
1. Overall project synchronization score (Are we aligned?).
2. Any blocking bottlenecks or mismatched assumptions between backend, frontend, AI, and data.
3. Immediate next step recommendations for each member.
```

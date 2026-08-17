# Brown Bag — Current Status

*Last updated: August 12, 2026*
*Location: `C:\Users\Octopus\Documents\marlo\docs\STATUS.md`*

> **Doc rule:** REPLACED each session, never appended. One "Last updated" date only.

---

## Where Things Stand

**Design is settled.** Product, architecture, and data model are all documented and agreed. The writer agent has been validated against realistic material.

**Build has started.** `database/models.py` is written but not yet tested or deployed.

**Nothing else is built.** No writer, no editor UI, no scan flow, no sending.

---

## 🔴 IMMEDIATE — Next Steps

### 1. Test the models
```powershell
cd C:\Users\Octopus\Documents\marlo\backend
Remove-Item -Recurse -Force __pycache__ -ErrorAction SilentlyContinue
python -c "from database.models import Base; print(f'{len(Base.metadata.tables)} tables')"
```
Should print **17 tables**.

### 2. ⚠️ Fix broken imports before pushing
`main.py` registers `businesses.router`, `agent.approval_router`, and `agent.router` — all import models that **no longer exist** in the new `models.py` (`Business`, `AgentAction`, `PlatformIntegration`).

The fault-tolerant `include()` helper will log them as SKIPPED rather than crash, but they should be removed properly rather than left failing.

**Do not push until this is resolved.**

### 3. Then P0 items 3–10
See `TASKS.md`.

---

## ✅ Done

- Product definition, architecture, data model — all documented
- Writer agent validated (`WRITER_TEST.md`) — bar is reachable, failure is upstream in the interviewer
- Instagram/Stripe code archived to `backend/archive/`
- `main.py` and `scheduler.py` cleaned of archived imports (Aug 11)
- Docs consolidated to 8 files
- `database/models.py` written — 17 tables

---

## 🆕 Not Built

Everything in P0 items 3–10 and all of P1–P3. Specifically:
- Writer agent, style guard
- Editor login, review queue
- Personalizer, renderer, dispatcher
- Unsubscribe
- Invitation codes, vendor signup, interviewer agent
- Scan flow, subscriber creation
- All scheduler jobs (framework running, zero jobs registered — correct for now)

---

## 🗄️ Archived (`backend/archive/`, not imported)

`content_pipeline.py`, `strategy_agent.py`, `executor.py`, `google_ads_agent.py`, `analytics_agent.py`, `meta.py`, `oauth.py`, `google_ads.py`, `billing/`

**Do not build on these.**

---

## 🚧 Blocking Decisions

| Question | Blocks |
|---|---|
| **Brown Bag sending domain** — can't be marlo021.ai | Any outbound email |
| One React app with role routing, or separate vendor / editor apps? | Editor UI |
| Physical QR format | Vendor rollout |

---

## Reference

| Item | Value |
|---|---|
| Publication name | **Brown Bag** (provisional, stored in `markets.publication_name`) |
| Backend system name | Marlo (repo, API — never user-facing) |
| API base | `https://api.marlo021.ai` |
| Local repo | `C:\Users\Octopus\Documents\marlo\` |
| Logs | `railway logs --tail` |
| Health check | `GET /health` → `0.2.0` |

---

## Key Design Decisions (quick recall)

- **Two agents:** interviewer gathers 素材, writer writes the story
- **Everything publishable is a block** — one table, one approval lifecycle
- **The bank is a query**, not a table: approved + not expired + no open corrections
- **Seen is permanent** per reader; **fatigue** is a decaying penalty per vendor
- **Vendors see drafts before editors** and can flag corrections
- **Issue ships every week** — never shrink, never skip, get more material
- **Nothing ships without editor approval**
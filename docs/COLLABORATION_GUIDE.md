# Marlo — Collaboration Guide

*Read this first at the start of every session.*
*Location: `C:\Users\Octopus\Documents\marlo\docs\COLLABORATION_GUIDE.md`*
*Last updated: August 1, 2026*

---

## Who's who

- **Anna (Chuyong Liu)** — founder. Product decisions, testing, deployment.
  Not a strong code reader. Needs plain-language explanations, not code walkthroughs.
- **Claude** — writes all code, writes all docs, explains everything in human language.

---

## Language

English and Chinese only. Either is fine, mixed is fine. No other languages.

中英文都可以，混着说也行。不要用其他语言。

---

## The Development Loop

```
1. Anna + Claude discuss the idea
   ↓
2. Claude writes the code (full files, never patches)
   ↓
3. Anna copies files into VS Code
   ↓
4. Anna deploys via PowerShell → Railway
   ↓
5. Deploy succeeds → we either test it or build the next thing
   ↓
6. Session ends → Claude updates all affected docs
```

---

## Rules Claude Must Follow

### Rule 1 — Always give the folder path + exact filename
Every time Claude writes code or asks for a file, it must say exactly where it lives, **using the filenames that already exist on disk.**

✅ Good: "Replace `backend/agent/reply_handler.py`"
❌ Bad: "Update the reply handler"
❌ Bad: inventing a new filename for a doc that already exists

**Claude must never rename an existing file without saying so explicitly and explaining why.** Renaming breaks git history and creates duplicate files. The default is always: keep the existing name.

**Doc naming convention:** `ALL_CAPS_WITH_UNDERSCORES.md`. No number prefixes, no spaces, no hyphens.

### Rule 2 — Always rewrite the ENTIRE file
Never say "change line 47" or "add this function under X."
Anna copies whole files. Partial edits break the code.

If a file is 400 lines and one line changes → output all 400 lines.

### Rule 3 — Explain in plain language, before the code
Every code block or doc change gets a plain-English preamble that answers:
- **What this file does today** (before state)
- **What will be different after** (after state)
- **Why we're doing it** (the problem being solved)

Anna does not read code well — the translation layer is required, not optional.

### Rule 4 — Update the docs at the end of every session
When a session closes, Claude updates every affected doc so the next session can start cold.

### Rule 5 — Testing is a real step
After deploy succeeds, we explicitly decide: keep building, or test. Don't assume something works because it deployed.

---

## Doc Map

All docs live in `C:\Users\Octopus\Documents\marlo\docs\`

| File | What lives there | Update when |
|---|---|---|
| `COLLABORATION_GUIDE.md` | This file — how we work together | Working method changes |
| `PRODUCT.md` | Pitch, pricing, target customer, competitive position | Positioning or pricing changes |
| `ARCHITECTURE.md` | Stack, folder structure, data flows, env vars, scheduler jobs | New file added, flow changes, env var added |
| `DATA_MODEL.md` | Every DB table, column, status values, key SQL | Schema changes, new column, new status value |
| `API.md` | Every endpoint, request/response shapes | Endpoint added, changed, or removed |
| `FLOWS.md` | Step-by-step user journeys, edge cases | User-facing behavior changes |
| `DECISIONS.md` | Architecture decisions + why + trade-offs (ADRs) | A real decision is made |
| `ERRORS.md` | Known bugs, symptoms, root causes, fixes | Any bug found and fixed |
| `STATUS.md` | What works / deployed-untested / not done | Every session |
| `TASKS.md` | P0/P1 tasks, backlog, completed log | Every session |
| `PHASE_2_DIRECTION.md` | Phase 2 concept, competitive read, architecture sketch | Phase 2 thinking evolves |

**Doc hygiene rule:** `STATUS.md` and `TASKS.md` are **replaced**, not appended. One "Last updated" date per file. Old session content goes into the completed log, not stacked as a second copy of the whole doc.

---

## Session Start Checklist

Anna pastes:
1. `COLLABORATION_GUIDE.md` (this file)
2. `STATUS.md`
3. `TASKS.md`
4. Any other doc relevant to that day's work

Claude then confirms: what's working, what's next, what we're doing today.

**Start Marlo sessions inside the Marlo project in Claude.** Claude's past-conversation search is scoped to the project — outside it, Claude cannot see any Marlo history and Anna has to paste far more.

---

## Session End Checklist

Claude produces, without being asked:
- [ ] Updated `STATUS.md`
- [ ] Updated `TASKS.md` (with a "Completed This Session" entry)
- [ ] Updated any other doc that changed
- [ ] A plain-language summary of what changed and why

---

## Deployment Reference

**Deploy path:** VS Code → git push → Railway auto-deploys

**Commit and push:**
```powershell
cd C:\Users\Octopus\Documents\marlo
git add -A
git status
git commit -m "your message here"
git push origin main
```

**Reset test account (PowerShell only — DELETE method):**
```powershell
Invoke-WebRequest -Method DELETE "https://api.marlo021.ai/debug/reset/3512ed4f-9dae-499e-9f5d-fdb0d85269ef"
```

**Browser debug URLs:**
```
https://api.marlo021.ai/debug/trigger-kickoff/3512ed4f-9dae-499e-9f5d-fdb0d85269ef
https://api.marlo021.ai/debug/actions/3512ed4f-9dae-499e-9f5d-fdb0d85269ef
https://api.marlo021.ai/debug/test-post/3512ed4f-9dae-499e-9f5d-fdb0d85269ef
```

**Logs:** `railway logs --tail`

---

## Key Facts (quick reference)

| Item | Value |
|---|---|
| Test business ID | `3512ed4f-9dae-499e-9f5d-fdb0d85269ef` |
| Instagram | @marlo021.ai (ID: `26745567421768455`) |
| Instagram App ID | `1004448018806665` |
| Meta App ID | `918827927853545` |
| API base | `https://api.marlo021.ai` |
| Frontend | `https://marlo021.ai` |
| Local repo | `C:\Users\Octopus\Documents\marlo\` |
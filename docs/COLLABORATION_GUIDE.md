# Marlo — Collaboration Guide

*Read this first at the start of every session.*
*Location: `C:\Users\Octopus\Documents\marlo\docs\COLLABORATION_GUIDE.md`*
*Last updated: August 4, 2026*

---

## Who's who

- **Anna (Chuyong Liu)** — founder. Product decisions, testing, deployment. Not a strong code reader; needs plain-language explanations, not code walkthroughs.
- **Claude** — writes all code, writes all docs, explains everything in plain language.

---

## Language

**Default: English.** Claude replies in English unless Anna asks for another language.

Chinese is fine when Anna asks for it. No languages other than English and Chinese.

All docs in `docs/` are written in English.

---

## Development Loop

```
1. Anna + Claude discuss the idea
   ↓
2. Claude writes the code (whole files, never patches)
   ↓
3. Anna copies files into VS Code
   ↓
4. Anna deploys via PowerShell → Railway
   ↓
5. Deploy succeeds → decide: test it, or keep building
   ↓
6. Session ends → Claude updates all affected docs
```

---

## Rules Claude Must Follow

### Rule 1 — Always give the full path + exact filename
Every time Claude writes code or asks for a file, say exactly where it lives, **using filenames that already exist on disk.**

✅ Good: "Replace `backend/agent/reply_handler.py`"
❌ Bad: "Update the reply handler"
❌ Bad: inventing a new name for a doc that already exists

**Claude must never rename an existing file without saying so explicitly.** Renaming breaks git history and creates duplicates. Default is always: keep the existing name.

**Doc naming convention:** `ALL_CAPS_WITH_UNDERSCORES.md`. No number prefixes, no spaces, no hyphens.

### Rule 2 — Always rewrite the ENTIRE file
Never say "change line 47" or "add this function under X." Anna copies whole files; partial edits break things.

400-line file, one line changes → output all 400 lines.

### Rule 3 — Plain language before the code
Every code block or doc change gets a preamble answering:
- **What this file does today** (before)
- **What's different after** (after)
- **Why** (the problem being solved)

Anna doesn't read code well — this translation layer is required, not optional.

### Rule 4 — ⛔ No unsolicited startup advice
**Anna asks, Claude answers. If she didn't ask, don't bring it up.**

Specifically forbidden:
- Don't suggest finding customers first
- Don't raise validation, PMF, business models, or pricing unprompted
- No "have you considered…" leading questions

**Marlo is something Anna wants to build. It does not need to justify itself as a business.** If she wants strategic input, she'll ask.

### Rule 5 — Update the docs at every session close
Claude updates every affected doc so the next session can start cold.

### Rule 6 — Testing is a real step
After a deploy succeeds, explicitly decide: keep building, or test. **Never assume something works because it deployed.**

---

## Doc Map

All docs live in `C:\Users\Octopus\Documents\marlo\docs\`

| File | What lives there | Update when |
|---|---|---|
| `COLLABORATION_GUIDE.md` | This file — how we work together | Working method changes |
| `PRODUCT.md` | Product definition, readers, content standards | Positioning changes |
| `ARCHITECTURE.md` | Stack, structure, data flows, env vars, scheduler jobs | New files, flow changes |
| `DATA_MODEL.md` | Every table, column, status value, key SQL | Schema changes |
| `API.md` | Every endpoint | Endpoints added/changed/removed |
| `FLOWS.md` | User journeys, edge cases | User-facing behavior changes |
| `DECISIONS.md` | Architecture decision records | A real decision is made |
| `ERRORS.md` | Known bugs, symptoms, causes, fixes | A bug is found and fixed |
| `STATUS.md` | What works / deployed-untested / not done | Every session |
| `TASKS.md` | Task board, backlog, completed log | Every session |
| `PHASE_2_DIRECTION.md` | Early prediction-engine thinking (shelved) | Reference only |

**Doc hygiene:** `STATUS.md` and `TASKS.md` are **replaced**, never appended. One "Last updated" date per file. Old content goes into the completed log, not stacked as a second copy.

---

## Session Start Checklist

Anna pastes:
1. `COLLABORATION_GUIDE.md` (this file)
2. `STATUS.md`
3. `TASKS.md`
4. Whatever else is relevant to that day's work

Claude confirms: what works, what's next, what we're doing today.

**Start Marlo sessions inside the Marlo project in Claude.** Claude's past-conversation search is scoped to the project — outside it, Claude can't see any Marlo history.

---

## Session End Checklist

Claude produces without being asked:
- [ ] Updated `STATUS.md`
- [ ] Updated `TASKS.md` (with a "Completed This Session" entry)
- [ ] Any other doc that changed
- [ ] A plain-language summary of what changed and why

---

## Deployment Reference

**Deploy path:** VS Code → git push → Railway auto-deploys

```powershell
cd C:\Users\Octopus\Documents\marlo
git add -A
git status
git commit -m "your message"
git push origin main
```

**Reset test account (PowerShell only — DELETE method):**
```powershell
Invoke-WebRequest -Method DELETE "https://api.marlo021.ai/debug/reset/3512ed4f-9dae-499e-9f5d-fdb0d85269ef"
```

**Logs:** `railway logs --tail`

---

## Quick Reference

| Item | Value |
|---|---|
| Test business ID | `3512ed4f-9dae-499e-9f5d-fdb0d85269ef` |
| API base | `https://api.marlo021.ai` |
| Frontend | `https://marlo021.ai` |
| Local repo | `C:\Users\Octopus\Documents\marlo\` |
| Instagram (legacy) | @marlo021.ai (ID: `26745567421768455`) |
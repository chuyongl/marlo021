"""
Skills: small, focused instruction files that the interview and writing
pipelines load one at a time.

Each skill is a folder under content/skills/ with a SKILL.md (frontmatter plus
instructions) and, optionally, other .md files (examples) that load with it.
That is the same shape as Anthropic's Agent Skills: a short name and
description that are always known, and the full body loaded only when the
skill is used.

The orchestrator (content/interviewer.py, content/writer.py) decides WHICH
skill to load, in code, so behaviour stays predictable on a phone-speed chat.
An editor can change a skill's text in the editor app; that change is stored
in the database (SkillOverride) and takes effect within seconds, without a
deploy. "Reset" returns to the file shipped with the code.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path

SKILLS_DIR = Path(__file__).parent / "skills"
OVERRIDE_TTL_SECONDS = 30

STAGES = ("scout", "interview", "director", "write", "eval")


@dataclass(frozen=True)
class Skill:
    name: str
    description: str
    stage: str
    default_body: str
    body: str                      # the body in effect (override if any)
    extras: dict = field(default_factory=dict)   # other .md files in the folder, by name
    edited: bool = False
    edited_by: str | None = None
    edited_at: str | None = None

    def text(self, with_extras: bool = True) -> str:
        """The instruction text to hand to the model."""
        parts = [self.body.strip()]
        if with_extras:
            parts += [v.strip() for _, v in sorted(self.extras.items()) if v.strip()]
        return "\n\n".join(parts)


_defaults: dict[str, dict] = {}
_overrides: dict[str, tuple[str, str | None, str | None]] = {}   # name -> (body, by, at)
_refreshed_at: float = 0.0


def _parse(text: str) -> tuple[dict, str]:
    text = text.lstrip("﻿")
    if not text.startswith("---"):
        return {}, text.strip()
    _, _, rest = text.partition("---")
    head, sep, body = rest.partition("\n---")
    meta = {}
    for line in head.strip().splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            meta[k.strip()] = v.strip()
    return meta, body.strip() if sep else text.strip()


def load_defaults(force: bool = False) -> dict[str, dict]:
    """Read every skill folder once. Skills ship with the code, so this is cached."""
    global _defaults
    if _defaults and not force:
        return _defaults
    found: dict[str, dict] = {}
    for folder in sorted(p for p in SKILLS_DIR.iterdir() if p.is_dir()):
        main = folder / "SKILL.md"
        if not main.exists():
            continue
        meta, body = _parse(main.read_text(encoding="utf-8"))
        name = meta.get("name") or folder.name
        extras = {p.name: p.read_text(encoding="utf-8") for p in sorted(folder.glob("*.md")) if p.name != "SKILL.md"}
        found[name] = {
            "name": name, "description": meta.get("description", ""), "stage": meta.get("stage", "interview"),
            "body": body, "extras": extras,
        }
    _defaults = found
    return _defaults


def names(stage: str | None = None) -> list[str]:
    d = load_defaults()
    return [n for n, s in d.items() if stage is None or s["stage"] == stage]


def get(name: str) -> Skill:
    d = load_defaults()
    if name not in d:
        raise KeyError(f"Unknown skill: {name}")
    s = d[name]
    ov = _overrides.get(name)
    return Skill(
        name=name, description=s["description"], stage=s["stage"], default_body=s["body"],
        body=ov[0] if ov else s["body"], extras=s["extras"],
        edited=bool(ov), edited_by=ov[1] if ov else None, edited_at=ov[2] if ov else None,
    )


def text(*skill_names: str) -> str:
    """Compose several skills into one system prompt (the persona plus the chosen skill)."""
    return "\n\n---\n\n".join(get(n).text() for n in skill_names)


def all_skills() -> list[Skill]:
    return [get(n) for n in load_defaults()]


# ── Editor overrides (database) ──────────────────────────────────────────────

async def refresh(db, force: bool = False) -> None:
    """Pull editor changes from the database into memory (at most every 30 seconds)."""
    global _refreshed_at, _overrides
    now = time.monotonic()
    if not force and now - _refreshed_at < OVERRIDE_TTL_SECONDS:
        return
    _refreshed_at = now
    try:
        from sqlalchemy import select

        from database.models import SkillOverride

        rows = (await db.execute(select(SkillOverride))).scalars().all()
        _overrides = {
            r.name: (r.body, r.updated_by, r.updated_at.isoformat() if r.updated_at else None)
            for r in rows if r.name in load_defaults()
        }
    except Exception:  # noqa: BLE001 - table may not exist yet; defaults still work
        pass


def set_override(name: str, body: str, by: str | None, at: str | None) -> None:
    _overrides[name] = (body, by, at)


def clear_override(name: str) -> None:
    _overrides.pop(name, None)

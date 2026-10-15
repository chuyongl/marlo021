"""
Startup schema upkeep.

create_all() adds missing TABLES but never changes existing ones. These
idempotent statements bring existing tables up to the current models. Each
runs on its own so one failure can't block the rest.
"""

import logging

from sqlalchemy import inspect, text

logger = logging.getLogger(__name__)

STATEMENTS = [
    # vendors
    "ALTER TABLE vendors ADD COLUMN IF NOT EXISTS venue_id UUID REFERENCES venues(id)",
    "ALTER TABLE vendors ADD COLUMN IF NOT EXISTS instagram VARCHAR",
    "ALTER TABLE vendors ADD COLUMN IF NOT EXISTS website VARCHAR",
    "ALTER TABLE vendors ADD COLUMN IF NOT EXISTS is_sample BOOLEAN NOT NULL DEFAULT false",
    # blocks
    "ALTER TABLE blocks ADD COLUMN IF NOT EXISTS slug VARCHAR",
    "ALTER TABLE blocks ADD COLUMN IF NOT EXISTS is_public BOOLEAN NOT NULL DEFAULT true",
    "ALTER TABLE blocks ADD COLUMN IF NOT EXISTS guard_notes JSONB",
    "ALTER TABLE blocks ADD COLUMN IF NOT EXISTS is_sample BOOLEAN NOT NULL DEFAULT false",
    "CREATE UNIQUE INDEX IF NOT EXISTS ix_blocks_slug ON blocks (slug)",
    # subscribers — no longer owned by a market (Aug 27 decision)
    "ALTER TABLE subscribers ADD COLUMN IF NOT EXISTS home_market_id UUID REFERENCES markets(id)",
    "ALTER TABLE subscribers ADD COLUMN IF NOT EXISTS signup_source VARCHAR",
    "ALTER TABLE subscribers ADD COLUMN IF NOT EXISTS referred_by_id UUID REFERENCES subscribers(id)",
    "ALTER TABLE subscribers DROP CONSTRAINT IF EXISTS uq_subscriber_market_email",
    "DROP INDEX IF EXISTS ix_subscribers_active",
    """DO $$ BEGIN
         IF EXISTS (SELECT 1 FROM information_schema.columns
                    WHERE table_name='subscribers' AND column_name='market_id') THEN
           ALTER TABLE subscribers ALTER COLUMN market_id DROP NOT NULL;
         END IF;
       END $$""",
    "CREATE UNIQUE INDEX IF NOT EXISTS uq_subscribers_email ON subscribers (lower(email))",
    "CREATE INDEX IF NOT EXISTS ix_subscribers_status ON subscribers (status)",
    # issues
    "ALTER TABLE issues ADD COLUMN IF NOT EXISTS subject VARCHAR",
    "ALTER TABLE issues ADD COLUMN IF NOT EXISTS greeting TEXT",
    "ALTER TABLE issues ADD COLUMN IF NOT EXISTS editor_name VARCHAR",
    "ALTER TABLE issues ADD COLUMN IF NOT EXISTS last_error TEXT",
]


def _reconcile(sync_conn) -> list[str]:
    """
    Generic safety net: for every model table that already exists, add any
    column the model has and the table lacks, and relax NOT NULL on columns
    the model no longer uses (e.g. v1-era columns on a reused table name).
    """
    from database.models import Base

    insp = inspect(sync_conn)
    stmts = []
    for table in Base.metadata.sorted_tables:
        if not insp.has_table(table.name):
            continue
        existing = {c["name"]: c for c in insp.get_columns(table.name)}
        for col in table.columns:
            if col.name in existing:
                continue
            type_sql = col.type.compile(dialect=sync_conn.dialect)
            default = ""
            d = col.default
            if d is not None and getattr(d, "is_scalar", False):
                v = d.arg
                if isinstance(v, bool):
                    default = f" NOT NULL DEFAULT {'true' if v else 'false'}"
                elif isinstance(v, (int, float)):
                    default = f" NOT NULL DEFAULT {v}"
                elif isinstance(v, str):
                    default = " DEFAULT '" + v.replace("'", "''") + "'"
            stmts.append(f'ALTER TABLE "{table.name}" ADD COLUMN IF NOT EXISTS "{col.name}" {type_sql}{default}')
        model_cols = {c.name for c in table.columns}
        for name, info in existing.items():
            if name not in model_cols and not info.get("nullable", True):
                stmts.append(f'ALTER TABLE "{table.name}" ALTER COLUMN "{name}" DROP NOT NULL')
    return stmts


async def run(conn) -> None:
    try:
        generic = await conn.run_sync(_reconcile)
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[Migrate] reconcile inspection failed: {e}")
        generic = []
    for stmt in generic + STATEMENTS:
        try:
            async with conn.begin_nested():
                await conn.execute(text(stmt))
        except Exception as e:  # noqa: BLE001
            logger.warning(f"[Migrate] skipped: {stmt.splitlines()[0][:80]} — {e}")

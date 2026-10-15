import re
import secrets
import uuid
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

CATEGORIES = {
    "bakery": "Bakery",
    "produce": "Produce",
    "prepared_food": "Prepared food",
    "meat": "Meat & sausage",
    "seafood": "Seafood",
    "dairy_cheese": "Dairy & cheese",
    "preserves": "Preserves & sauces",
    "honey": "Honey",
    "coffee_tea": "Coffee & tea",
    "flowers": "Flowers & plants",
    "jewelry": "Jewelry",
    "crafts": "Crafts & goods",
}

CATEGORY_PAIRS = {
    "bakery": ["dairy_cheese", "preserves", "coffee_tea", "honey"],
    "produce": ["prepared_food", "dairy_cheese", "meat", "preserves"],
    "prepared_food": ["produce", "coffee_tea", "bakery"],
    "meat": ["produce", "bakery", "preserves"],
    "seafood": ["produce", "preserves", "bakery"],
    "dairy_cheese": ["bakery", "preserves", "honey", "produce"],
    "preserves": ["bakery", "dairy_cheese", "meat"],
    "honey": ["bakery", "dairy_cheese", "coffee_tea"],
    "coffee_tea": ["bakery", "honey", "prepared_food"],
    "flowers": ["crafts", "jewelry", "honey"],
    "jewelry": ["crafts", "flowers"],
    "crafts": ["jewelry", "flowers"],
}

SEATTLE_NEIGHBORHOODS = {
    "Downtown": {"adjacent": ["Belltown", "Capitol Hill", "Pioneer Square"], "city": "Seattle"},
    "Belltown": {"adjacent": ["Downtown", "Queen Anne"], "city": "Seattle"},
    "Pioneer Square": {"adjacent": ["Downtown", "International District"], "city": "Seattle"},
    "International District": {"adjacent": ["Pioneer Square", "Beacon Hill"], "city": "Seattle"},
    "Capitol Hill": {"adjacent": ["Downtown", "Central District"], "city": "Seattle"},
    "Central District": {"adjacent": ["Capitol Hill", "Beacon Hill"], "city": "Seattle"},
    "Queen Anne": {"adjacent": ["Belltown", "Fremont", "Magnolia"], "city": "Seattle"},
    "Magnolia": {"adjacent": ["Queen Anne", "Ballard"], "city": "Seattle"},
    "Ballard": {"adjacent": ["Fremont", "Magnolia"], "city": "Seattle"},
    "Fremont": {"adjacent": ["Ballard", "Wallingford", "Queen Anne"], "city": "Seattle"},
    "Wallingford": {"adjacent": ["Fremont", "University District"], "city": "Seattle"},
    "University District": {"adjacent": ["Wallingford", "Ravenna"], "city": "Seattle"},
    "Ravenna": {"adjacent": ["University District"], "city": "Seattle"},
    "Beacon Hill": {"adjacent": ["International District", "Columbia City", "Central District"], "city": "Seattle"},
    "Columbia City": {"adjacent": ["Beacon Hill", "Rainier Beach"], "city": "Seattle"},
    "Rainier Beach": {"adjacent": ["Columbia City"], "city": "Seattle"},
    "West Seattle": {"adjacent": [], "city": "Seattle"},
    "Bellevue": {"adjacent": [], "city": "Bellevue"},
}


def slugify(text: str, max_len: int = 48) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    return s[:max_len].strip("-") or "story"


def short_id(n: int = 5) -> str:
    alphabet = "abcdefghjkmnpqrstuvwxyz23456789"
    return "".join(secrets.choice(alphabet) for _ in range(n))


def scan_code() -> str:
    alphabet = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
    return "".join(secrets.choice(alphabet) for _ in range(5))


def week_start(tz: str = "America/Los_Angeles") -> date:
    today = datetime.now(ZoneInfo(tz)).date()
    return today - timedelta(days=today.weekday())


def as_uuid(value) -> uuid.UUID | None:
    try:
        return uuid.UUID(str(value))
    except (ValueError, TypeError):
        return None


def iso(dt) -> str | None:
    return dt.isoformat() if dt else None

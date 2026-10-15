"""
First-boot seed: the Seattle market, venues, category pairs, and clearly
marked SAMPLE vendors and stories so every page has something to show.

Runs only when no market exists. Sample content carries is_sample=True and
can be removed from the editor app in one click.
"""

import logging
import secrets
from datetime import timedelta

from sqlalchemy import func, select

from core.config import FROM_EMAIL, FROM_NAME, PUBLICATION_NAME
from core.util import CATEGORIES, CATEGORY_PAIRS, SEATTLE_NEIGHBORHOODS, scan_code, short_id, slugify
from database.models import (
    Block, BlockClass, BlockStatus, CategoryPair, InvitationCode, Market, ReaderShare,
    Vendor, Venue, utcnow,
)

logger = logging.getLogger(__name__)

VENUES = [
    ("Pike Place Market", "pike-place", "Downtown",
     "Seattle's public market since 1907: farmers, craftspeople and day-stall artisans.",
     "Daily, 9am–5pm. Day-stall tables change every morning."),
    ("Ballard Farmers Market", "ballard", "Ballard",
     "Year-round Sunday market on Ballard Avenue.", "Sundays, 9am–2pm."),
    ("Columbia City Farmers Market", "columbia-city", "Columbia City",
     "Wednesday afternoon market in Columbia City.", "Wednesdays, 3–7pm, May–October."),
]

SAMPLE_VENDORS = [
    {
        "name": "Lena Ruiz Jewelry", "venue": "pike-place", "neighborhood": "Downtown",
        "categories": ["jewelry"],
        "description": "Hammered silver necklaces and earrings, made on a railroad spike that was her grandfather's.",
        "schedule_note": "Day stall, usually the north arcade Thursdays and Saturdays.",
    },
    {
        "name": "Fortune Noodle", "venue": "ballard", "neighborhood": "Ballard",
        "categories": ["prepared_food"],
        "description": "Mei's hand-pulled noodles and small-batch chili oil.",
        "schedule_note": "Sundays at Ballard Farmers Market.",
    },
    {
        "name": "Hollow Ridge Farm", "venue": "ballard", "neighborhood": "Ballard",
        "categories": ["produce", "preserves"],
        "description": "Dan and Jen grow kale, chard and late tomatoes an hour north of the city.",
        "schedule_note": "Sundays at Ballard Farmers Market.",
    },
    {
        "name": "Kettle & Smoke Sausage", "venue": "columbia-city", "neighborhood": "Columbia City",
        "categories": ["meat"],
        "description": "Otto smokes bratwurst and seasonal sausages in small batches.",
        "schedule_note": "Wednesdays 3–7pm at Columbia City.",
    },
    {
        "name": "Pike Hill Honey", "venue": "pike-place", "neighborhood": "Downtown",
        "categories": ["honey"],
        "description": "Raw honey from hives on rooftops in Capitol Hill and Beacon Hill.",
        "schedule_note": "Fridays and Saturdays, south arcade.",
    },
]

SAMPLE_BLOCKS = [
    ("Fortune Noodle", BlockClass.STORY, "She's not famous. She's out of chili oil.",
     "Mei sold out by 11 on Saturday. She usually goes till two.\n\n"
     "She'd made forty jars. Last month she made sixty and carried twenty home, so forty seemed like the sensible number. "
     "There was a line before she finished setting up.\n\n"
     "A woman in the queue held up her phone to show her why: a video of Mei at the July demo, toasting peppercorns, "
     "filmed by someone she never noticed. Ninety thousand views. She doesn't have TikTok.\n\n"
     "\"Honestly a little strange,\" she said. \"My hands look old in it.\"\n\n"
     "Her twelve-year-old made her watch it four times. \"She said mom you're famous, and I said I'm not famous, I'm out of chili oil.\"\n\n"
     "This week there will be eighty jars. She was up until one in the morning on Tuesday toasting peppercorns, "
     "and at some point her neighbor knocked on the door to ask whether something was burning.", 34),
    ("Hollow Ridge Farm", BlockClass.STORY, "A third of the tomatoes split. Now there's sauce.",
     "The rain last week split about a third of Dan's late tomatoes. Split tomatoes don't sell.\n\n"
     "Normally they go to the pigs. There were too many for the pigs.\n\n"
     "So there is sauce now, thirty-something jars of it, which Hollow Ridge has never made before and never sold. "
     "The jars are labeled in marker on masking tape.\n\n"
     "Kale and chard as usual. The sauce is at the end of the table.", 26),
    ("Lena Ruiz Jewelry", BlockClass.UPDATE, "Back at the north arcade",
     "Lena has a table Thursday and Saturday this week, north arcade. New this week: a set of tiny hammered moon pendants.", 22),
    ("Kettle & Smoke Sausage", BlockClass.UPDATE, "Otto's five-minute apple-sage toast",
     "New this week: smoked apple-sage sausage. Otto's quick way with it: slice, brown in a dry pan, add a sliced onion "
     "and a splash of cider, cook until sticky, pile on toast. Wednesdays 3–7 at Columbia City.", 24),
    ("Pike Hill Honey", BlockClass.UPDATE, "The last of the blackberry honey",
     "The late-summer blackberry honey is down to two cases. After that it's the darker fall honey until next August.", 20),
]


async def seed_if_empty(db) -> None:
    count = (await db.execute(select(func.count()).select_from(Market))).scalar()
    if count:
        return
    logger.info("[Seed] Empty database — seeding Seattle market and sample content")

    market = Market(
        name="Seattle", slug="seattle", publication_name=PUBLICATION_NAME,
        from_email=FROM_EMAIL, from_name=FROM_NAME, neighborhoods=SEATTLE_NEIGHBORHOODS,
    )
    db.add(market)
    await db.flush()

    for cat, label in CATEGORIES.items():
        if not await db.get(CategoryPair, cat):
            db.add(CategoryPair(category=cat, display_name=label, complements=CATEGORY_PAIRS.get(cat, [])))

    venues = {}
    for name, slug, hood, desc, sched in VENUES:
        v = Venue(market_id=market.id, name=name, slug=slug, neighborhood=hood, description=desc,
                  schedule_note=sched, report_token=secrets.token_urlsafe(16))
        db.add(v)
        venues[slug] = v
    await db.flush()

    db.add(InvitationCode(market_id=market.id, code="PIKEPILOT", neighborhood="Downtown",
                          label="Pike Place pilot", max_uses=100))
    db.add(InvitationCode(market_id=market.id, code="SEATTLE26", label="General Seattle signup", max_uses=200))

    vendors = {}
    for i, sv in enumerate(SAMPLE_VENDORS):
        comps = sorted({c for cat in sv["categories"] for c in CATEGORY_PAIRS.get(cat, [])})
        v = Vendor(
            market_id=market.id, venue_id=venues[sv["venue"]].id, name=sv["name"],
            slug=slugify(sv["name"]), email=f"sample{i + 1}@example.com", scan_code=scan_code(),
            neighborhood=sv["neighborhood"], city="Seattle", categories=sv["categories"],
            complementary_categories=comps, description=sv["description"],
            schedule_note=sv["schedule_note"], is_sample=True,
        )
        db.add(v)
        vendors[sv["name"]] = v
    await db.flush()

    now = utcnow()
    for vendor_name, cls, headline, body, quality in SAMPLE_BLOCKS:
        v = vendors[vendor_name]
        db.add(Block(
            market_id=market.id, vendor_id=v.id, block_class=cls, status=BlockStatus.APPROVED,
            headline=headline, body=body, word_count=len(body.split()), categories=v.categories,
            quality_score=quality, perishable=(cls == BlockClass.UPDATE),
            expires_at=(now + timedelta(days=60)) if cls == BlockClass.UPDATE else None,
            slug=f"{slugify(headline)}-{short_id()}", is_public=True, is_sample=True,
            reviewed_at=now,
        ))
    db.add(ReaderShare(
        vendor_id=vendors["Kettle & Smoke Sausage"].id, reader_name="Priya, Beacon Hill (sample)",
        text="Made Otto's apple-sage toast for Sunday breakfast and added a fried egg on top. My kid asked for it again Monday.",
        status="approved", reviewed_at=now,
    ))
    await db.commit()
    logger.info("[Seed] Done")

"""
vendor_profiles.py

Central config for all vendor types Marlo supports.
Adding a new vendor type = add one entry to VENDOR_PROFILES. Nothing else changes.
"""

from dataclasses import dataclass


@dataclass
class ImageStyle:
    mood: str
    color_palette: str
    lighting: str
    backgrounds: list
    avoid: str
    preferred_model: str = "flux"  # "flux" or "ideogram" — ideogram for text-heavy images


@dataclass
class LifestyleSceneRules:
    scene_types: list
    model_guidance: str
    props: list
    composition: str
    platform_notes: dict


@dataclass
class VendorProfile:
    vendor_type: str
    display_name: str
    content_pillars: list
    image_style: ImageStyle
    lifestyle_scene_rules: LifestyleSceneRules
    caption_tone: str
    hashtag_clusters: list
    photo_prompts: list
    posting_frequency: str


VENDOR_PROFILES = {

    # ── Software / SaaS ───────────────────────────────────────────────────────
    "software_saas": VendorProfile(
        vendor_type="software_saas",
        display_name="Software & SaaS",
        content_pillars=[
            "product milestones and launches",
            "build in public / founder journey",
            "product demos and features",
            "customer stories and wins",
            "team and culture",
            "industry insights and opinion",
        ],
        image_style=ImageStyle(
            mood="clean, modern, confident, founder-authentic",
            color_palette="brand colors, dark mode aesthetics, clean whites",
            lighting="clean studio or natural light for people shots",
            backgrounds=["clean desk setup", "minimal workspace", "app interface on screen", "dark brand background"],
            avoid="stock photo feel, overly corporate, cluttered UI",
            preferred_model="ideogram",  # needs accurate text in mockups
        ),
        lifestyle_scene_rules=LifestyleSceneRules(
            scene_types=[
                "clean app interface mockup on phone showing key feature with real readable text",
                "founder at minimal desk with product visible on laptop screen",
                "before/after split: chaos (sticky notes, overwhelm) vs clarity (clean dashboard)",
                "product dashboard screenshot styled as social card with brand colors",
                "team working together on laptop in modern office or cafe",
            ],
            model_guidance=(
                "For mockup images: use Ideogram for accurate text rendering. "
                "Show real product UI with correct readable text. "
                "For people shots: authentic founder energy, not stock photo smiles."
            ),
            props=["laptop", "phone showing app", "minimal desk accessories", "coffee"],
            composition=(
                "Clean and purposeful. Product is the hero. "
                "For mockups: phone or laptop frame centered, text clearly readable. "
                "For people: candid over posed."
            ),
            platform_notes={
                "instagram_feed": "Square or portrait. Brand colors consistent. Product visible.",
                "instagram_story": "Behind the scenes build process, metrics wins, feature demos.",
            },
        ),
        caption_tone=(
            "Direct, confident, and honest. Write like a founder talking to other founders. "
            "Share real numbers, real challenges, real wins. "
            "No corporate speak. Short punchy sentences. "
            "Build in public energy — transparent about the journey."
        ),
        hashtag_clusters=[
            ["#buildinpublic", "#indiefounder", "#startuplife", "#solofounder"],
            ["#saas", "#productlaunch", "#indiehackers", "#makersgonnamake"],
            ["#smallbusiness", "#aitools", "#productivity", "#entrepreneurship"],
        ],
        photo_prompts=[
            "Your product on screen — show the feature you shipped this week",
            "You working — authentic founder moment, messy desk or coffee shop",
            "A metric or milestone screenshot styled as a shareable graphic",
            "Before/after of the problem your product solves",
        ],
        posting_frequency="4-5x per week — consistency builds audience for SaaS",
    ),

    # ── Jewelry / Accessories ─────────────────────────────────────────────────
    "maker_jewelry": VendorProfile(
        vendor_type="maker_jewelry",
        display_name="Jewelry Maker",
        content_pillars=[
            "product showcase", "making process / behind the scenes",
            "styling inspiration", "material story",
            "customer moments", "artisan story",
        ],
        image_style=ImageStyle(
            mood="editorial, elegant, intimate, aspirational",
            color_palette="muted neutrals, cream, warm white, gold, blush",
            lighting="soft diffused natural window light, no harsh shadows",
            backgrounds=["white marble", "linen fabric", "aged wood", "stone", "skin/hands"],
            avoid="cluttered backgrounds, harsh flash, plastic props, busy patterns",
        ),
        lifestyle_scene_rules=LifestyleSceneRules(
            scene_types=[
                "elegant hands wearing or holding the piece, soft natural light",
                "editorial flat lay on marble or linen with minimal props",
                "close-up detail shot highlighting texture and craftsmanship",
                "lifestyle model wearing piece in a minimal indoor setting",
                "styled still life with dried flowers, fabric, or candles",
            ],
            model_guidance=(
                "Use elegant hands as the primary model element. "
                "Show wrist, neck, or ear depending on piece type. "
                "Nails clean and simple. No face needed."
            ),
            props=["dried flowers", "fresh greenery", "linen fabric", "candles", "ribbon"],
            composition=(
                "Rule of thirds. Product is the clear hero. "
                "Negative space is your friend."
            ),
            platform_notes={
                "instagram_feed": "Square or portrait (4:5). Consistent color palette.",
                "instagram_story": "Portrait (9:16). Product centered.",
            },
        ),
        caption_tone=(
            "Warm, personal, and poetic. Write as if telling a friend about a beautiful discovery. "
            "Use sensory language — texture, light, feeling. Short sentences."
        ),
        hashtag_clusters=[
            ["#handmadejewelry", "#jewelrymaker", "#artisanjewelry", "#jewelrylover"],
            ["#minimalistjewelry", "#daintyjewelry", "#sterlingsilver", "#goldfilledjewelry"],
            ["#shopsmall", "#makersgonnamake", "#supporthandmade", "#wearableart"],
        ],
        photo_prompts=[
            "Close-up of your hands working on a piece",
            "Flat lay of your latest collection on white or linen",
            "Someone wearing your piece in natural window light",
            "Detail shot of your most intricate piece",
        ],
        posting_frequency="3-4x per week",
    ),

    # ── Ceramics / Pottery ────────────────────────────────────────────────────
    "maker_ceramics": VendorProfile(
        vendor_type="maker_ceramics",
        display_name="Ceramics & Pottery",
        content_pillars=[
            "product showcase", "making process",
            "in-use lifestyle", "glaze and material story",
            "home styling", "artisan story",
        ],
        image_style=ImageStyle(
            mood="earthy, warm, handmade, slow living, minimal",
            color_palette="terracotta, warm whites, sage, clay tones, muted earth",
            lighting="warm natural light, golden hour feel",
            backgrounds=["raw wood", "linen", "stone", "kitchen countertop"],
            avoid="bright artificial light, cold tones, shiny plastic surfaces",
        ),
        lifestyle_scene_rules=LifestyleSceneRules(
            scene_types=[
                "piece in use — coffee in a mug, flowers in a vase",
                "styled on a kitchen counter with natural props",
                "hands holding the piece, showing scale and texture",
                "flat lay with food, plants, and linen",
                "detail close-up of glaze and texture",
            ],
            model_guidance="Real maker hands are beautiful. In-use shots work best.",
            props=["fresh herbs", "flowers", "coffee beans", "linen napkins", "bread"],
            composition="Generous negative space. Slightly asymmetric feels natural.",
            platform_notes={
                "instagram_feed": "Square. Earthy consistent palette.",
                "instagram_story": "Show the making process.",
            },
        ),
        caption_tone=(
            "Honest, grounded, and warm. Talk about the making process. "
            "Use specific sensory details — weight, texture, imperfections."
        ),
        hashtag_clusters=[
            ["#handmadeceramics", "#pottery", "#ceramics", "#stoneware"],
            ["#potterylife", "#ceramicartist", "#makersgonnamake"],
            ["#slowliving", "#homedecor", "#minimalhome"],
        ],
        photo_prompts=[
            "Hands shaping clay at the wheel or table",
            "A finished piece with coffee or flowers inside",
            "Fresh-from-the-kiln pieces lined up",
            "Detail of glaze texture in window light",
        ],
        posting_frequency="3x per week",
    ),

    # ── Candles / Home Fragrance ──────────────────────────────────────────────
    "maker_candles": VendorProfile(
        vendor_type="maker_candles",
        display_name="Candles & Home Fragrance",
        content_pillars=[
            "product showcase", "mood and ambiance",
            "scent storytelling", "gifting occasions",
            "making process", "home styling",
        ],
        image_style=ImageStyle(
            mood="cozy, warm, intimate, luxurious calm",
            color_palette="warm amber, cream, deep forest, blush, charcoal",
            lighting="candle glow + soft natural light — warm tones",
            backgrounds=["dark matte surfaces", "marble", "linen", "books"],
            avoid="cold blue light, clinical white, cluttered frames",
        ),
        lifestyle_scene_rules=LifestyleSceneRules(
            scene_types=[
                "candle lit in a cozy home setting — evening ambiance",
                "styled flat lay with complementary objects (book, mug, crystals)",
                "close-up of flame and label in warm light",
                "gifting scene — wrapped with ribbon and tag",
                "hands holding the candle jar",
            ],
            model_guidance="The product can hero on its own. Evening/dusk settings feel most authentic.",
            props=["books", "crystals", "dried flowers", "matches", "mug of tea"],
            composition="Moody and intimate. Let candle glow create natural warmth.",
            platform_notes={
                "instagram_feed": "Consistent warm palette.",
                "instagram_story": "Show the ritual — lighting, unwrapping, gifting.",
            },
        ),
        caption_tone=(
            "Evocative and sensory. Describe what the scent feels like. "
            "Reference moments and emotions. Short, poetic."
        ),
        hashtag_clusters=[
            ["#handmadecandles", "#soycandles", "#candlemaker", "#smallbatchcandles"],
            ["#cozyhome", "#slowliving", "#selfcare", "#homefragrance"],
            ["#giftideas", "#shopsmall"],
        ],
        photo_prompts=[
            "Candle lit in your coziest corner at dusk",
            "Flat lay of your collection with seasonal props",
            "Pouring process — wax and fragrance being added",
            "Gifting setup — wrapped beautifully",
        ],
        posting_frequency="3x per week",
    ),

    # ── Bakery / Food ─────────────────────────────────────────────────────────
    "food_bakery": VendorProfile(
        vendor_type="food_bakery",
        display_name="Bakery & Baked Goods",
        content_pillars=[
            "product showcase", "seasonal specials",
            "behind the scenes", "ingredients story",
            "customer moments", "ordering info",
        ],
        image_style=ImageStyle(
            mood="warm, inviting, artisanal, real",
            color_palette="warm whites, golden browns, blush, sage, honey",
            lighting="bright but warm natural light",
            backgrounds=["white marble", "wood cutting board", "linen", "parchment paper"],
            avoid="artificial yellow light, cold tones, plastic surfaces",
        ),
        lifestyle_scene_rules=LifestyleSceneRules(
            scene_types=[
                "hero shot on marble or wood with minimal props",
                "hands breaking or holding product — showing texture",
                "cross-section showing interior layers",
                "full spread with coffee, jam, butter",
            ],
            model_guidance="Hands breaking bread feel authentic. Crumbs and imperfections are appetizing.",
            props=["coffee cup", "jam jars", "linen", "seasonal fruits"],
            composition="Show the inside when possible. Top-down for spreads.",
            platform_notes={
                "instagram_feed": "Bright and warm.",
                "instagram_story": "Behind the scenes — baking, packaging, early morning.",
            },
        ),
        caption_tone=(
            "Warm and community-focused. Talk about ingredients and process. "
            "Include practical info — available days, how to order."
        ),
        hashtag_clusters=[
            ["#sourdough", "#artisanbread", "#homebakery", "#freshbaked"],
            ["#foodphotography", "#bakersofinstagram", "#breadbaking"],
            ["#shoplocal", "#supportlocal", "#smallbakery"],
        ],
        photo_prompts=[
            "Fresh out of the oven — show the steam and golden color",
            "Cross section of your most popular item",
            "Your workspace early morning",
            "This week's special with one or two props",
        ],
        posting_frequency="4-5x per week",
    ),

    # ── Coffee Shop / Café ────────────────────────────────────────────────────
    "food_cafe": VendorProfile(
        vendor_type="food_cafe",
        display_name="Coffee Shop & Café",
        content_pillars=[
            "drinks and food showcase", "cafe atmosphere",
            "seasonal menu", "team and story",
            "community moments", "specials and hours",
        ],
        image_style=ImageStyle(
            mood="cozy, welcoming, community, third-place energy",
            color_palette="warm browns, cream, terracotta, forest green",
            lighting="warm window light, golden morning feel",
            backgrounds=["cafe tables", "window seats", "bar counter"],
            avoid="empty sterile spaces, harsh fluorescent, stock-photo feel",
        ),
        lifestyle_scene_rules=LifestyleSceneRules(
            scene_types=[
                "drink on cafe table with window light and gentle blur",
                "latte art close-up — overhead shot",
                "someone enjoying a drink in a cozy corner",
                "behind the bar — barista preparing drinks",
            ],
            model_guidance="Real customers or staff feel authentic. Hands around a warm mug is universal.",
            props=["book", "laptop", "journal", "flowers on table", "pastry"],
            composition="Overhead for latte art. Eye-level for atmosphere.",
            platform_notes={
                "instagram_feed": "Consistent warm tones. Morning light performs best.",
                "instagram_story": "Daily specials, team moments.",
            },
        ),
        caption_tone=(
            "Friendly, community-first. Talk about people and moments. "
            "Reference neighborhood, regulars, team. Include practical info."
        ),
        hashtag_clusters=[
            ["#coffeeshop", "#specialtycoffee", "#latteart", "#coffeetime"],
            ["#cafelife", "#coffeeculture", "#baristalife"],
            ["#shoplocal", "#localcafe", "#communityspot"],
        ],
        photo_prompts=[
            "This week's seasonal drink in your best window light",
            "Your team in action — the energy of a busy morning",
            "A cozy corner of your space",
            "Close-up latte art on your signature drink",
        ],
        posting_frequency="5x per week",
    ),

    # ── Farmer / Market ───────────────────────────────────────────────────────
    "farmer_market": VendorProfile(
        vendor_type="farmer_market",
        display_name="Farmer & Market Vendor",
        content_pillars=[
            "seasonal harvest", "market days",
            "farm life behind the scenes", "recipes and how-to",
            "community", "availability and pre-orders",
        ],
        image_style=ImageStyle(
            mood="honest, seasonal, earthy, abundant, real",
            color_palette="earth tones, deep greens, harvest golds, berry reds",
            lighting="natural outdoor light, golden hour for farm shots",
            backgrounds=["farm fields", "market stalls", "wooden crates", "baskets"],
            avoid="studio-looking images, overly polished",
        ),
        lifestyle_scene_rules=LifestyleSceneRules(
            scene_types=[
                "hands harvesting or holding produce in the field",
                "market stall abundance shot — full display",
                "close-up of produce showing freshness and color",
                "seasonal flat lay on wood or in basket",
            ],
            model_guidance="Real farmer hands are best — weathered and authentic.",
            props=["wooden crates", "baskets", "burlap", "seasonal leaves"],
            composition="Abundance reads well — fill the frame.",
            platform_notes={
                "instagram_feed": "Seasonal color palette.",
                "instagram_story": "Market day countdowns, harvest updates.",
            },
        ),
        caption_tone=(
            "Honest, direct, grounded. Talk about the season, weather, land. "
            "Be practical — when, where, how to order."
        ),
        hashtag_clusters=[
            ["#farmersmarket", "#localfarm", "#farmfresh", "#supportlocal"],
            ["#organicfarming", "#farmtotable", "#seasonal"],
            ["#communitysupported", "#localproduce"],
        ],
        photo_prompts=[
            "This week's harvest — show abundance and color",
            "You or your hands in the field",
            "Market stall setup before the rush",
            "Close-up of your most beautiful produce",
        ],
        posting_frequency="3-4x per week, timed around market days",
    ),

    # ── Health & Wellness ─────────────────────────────────────────────────────
    "health_wellness": VendorProfile(
        vendor_type="health_wellness",
        display_name="Health & Wellness",
        content_pillars=[
            "tips and education", "client transformations",
            "behind the scenes", "product or service showcase",
            "personal story and motivation", "community",
        ],
        image_style=ImageStyle(
            mood="calm, empowering, clean, aspirational but real",
            color_palette="soft greens, earth tones, warm whites, sage",
            lighting="bright natural light, airy and clean",
            backgrounds=["yoga studio", "nature outdoors", "clean minimal space", "gym"],
            avoid="overly posed, unrealistic body standards, clinical feel",
        ),
        lifestyle_scene_rules=LifestyleSceneRules(
            scene_types=[
                "person in movement — yoga pose, workout, walk in nature",
                "calm ritual moment — meditation, morning tea, journaling",
                "before/after result (with permission and sensitivity)",
                "product or supplement styled cleanly",
                "practitioner working with client",
            ],
            model_guidance=(
                "Authentic and diverse bodies. Movement feels natural, not posed. "
                "Emotion and wellbeing over perfection."
            ),
            props=["yoga mat", "water bottle", "plants", "journal", "healthy food"],
            composition="Space and light. Feels like a breath of fresh air.",
            platform_notes={
                "instagram_feed": "Consistent calm palette. Inspires without pressuring.",
                "instagram_story": "Tips, tutorials, day-in-the-life.",
            },
        ),
        caption_tone=(
            "Warm, encouraging, and educational. Lead with value. "
            "Share practical tips. Empowering not preachy."
        ),
        hashtag_clusters=[
            ["#wellness", "#healthylifestyle", "#selfcare", "#mindfulness"],
            ["#fitness", "#yoga", "#nutrition", "#mentalhealth"],
            ["#holistichealth", "#wellnesscommunity", "#healthcoach"],
        ],
        photo_prompts=[
            "A movement or practice moment — authentic, not posed",
            "Your workspace or tools — what your sessions look like",
            "A calm ritual from your own routine",
            "A client win or transformation (with permission)",
        ],
        posting_frequency="4-5x per week",
    ),

    # ── Retail / Fashion ──────────────────────────────────────────────────────
    "retail_fashion": VendorProfile(
        vendor_type="retail_fashion",
        display_name="Fashion & Retail",
        content_pillars=[
            "product showcase", "styling and outfits",
            "behind the scenes", "new arrivals",
            "customer styling", "brand story",
        ],
        image_style=ImageStyle(
            mood="stylish, aspirational, editorial, brand-consistent",
            color_palette="depends on brand — consistent season palette",
            lighting="clean natural or studio light, no harsh shadows",
            backgrounds=["minimal studio", "urban street", "nature", "brand aesthetic setting"],
            avoid="inconsistent aesthetic, bad lighting, cluttered backgrounds",
        ),
        lifestyle_scene_rules=LifestyleSceneRules(
            scene_types=[
                "model or person wearing product in lifestyle setting",
                "flat lay of product with complementary items",
                "detail close-up of fabric, texture, or craftsmanship",
                "styled outfit on location — urban, nature, or interior",
                "packaging and unboxing moment",
            ],
            model_guidance=(
                "Real people wearing products feel more authentic than mannequins. "
                "Show how the piece moves and fits in real life."
            ),
            props=["complementary accessories", "seasonal elements", "brand packaging"],
            composition="Product is always the hero. Clean consistent aesthetic.",
            platform_notes={
                "instagram_feed": "Grid aesthetic is critical — consistent mood and palette.",
                "instagram_story": "New arrivals, styling tips, behind the scenes.",
            },
        ),
        caption_tone=(
            "Confident and stylish. Short and punchy. "
            "Speak to the lifestyle the customer aspires to. "
            "Include practical info — size, availability, link."
        ),
        hashtag_clusters=[
            ["#fashion", "#style", "#ootd", "#outfitoftheday"],
            ["#shopsmall", "#independentbrand", "#slowfashion", "#sustainablestyle"],
            ["#newcollection", "#shoponline", "#fashionblogger"],
        ],
        photo_prompts=[
            "This week's new arrival styled on a real person",
            "Detail shot of your favorite fabric or texture",
            "Flat lay of a complete outfit with accessories",
            "Behind the scenes — packing orders or new stock arriving",
        ],
        posting_frequency="5x per week — fashion benefits from high frequency",
    ),

    # ── Local Service ─────────────────────────────────────────────────────────
    "service_local": VendorProfile(
        vendor_type="service_local",
        display_name="Local Service Business",
        content_pillars=[
            "before and after results", "team and culture",
            "tips and education", "customer stories",
            "behind the scenes", "specials and availability",
        ],
        image_style=ImageStyle(
            mood="professional, warm, trustworthy, real",
            color_palette="clean and consistent with brand colors",
            lighting="bright, clean, flattering natural or studio light",
            backgrounds=["your actual workspace", "clean branded environment"],
            avoid="blurry photos, unflattering lighting, cluttered backgrounds",
        ),
        lifestyle_scene_rules=LifestyleSceneRules(
            scene_types=[
                "your work environment showing professionalism and warmth",
                "team in action — candid moment of serving a client",
                "before and after pairing (with permission)",
                "detail shot of the service outcome",
            ],
            model_guidance="Real clients (with permission) are more powerful than stock. Team photos build trust.",
            props=["your actual tools", "branded elements", "workspace details"],
            composition="Clear and bright. Before/after: same lighting and angle.",
            platform_notes={
                "instagram_feed": "Consistent and professional.",
                "instagram_story": "Day-in-the-life, tips, tutorials.",
            },
        ),
        caption_tone=(
            "Warm, professional, community-oriented. "
            "Talk about clients, team, neighborhood. Include booking info."
        ),
        hashtag_clusters=[
            ["#smallbusiness", "#localservice", "#shoplocal"],
            ["#supportsmallbusiness", "#communityFirst"],
        ],
        photo_prompts=[
            "Your workspace ready for the day",
            "A great result from this week",
            "Your team in action",
            "A tip that shows your expertise",
        ],
        posting_frequency="3-4x per week",
    ),

    # ── Creative Professional ─────────────────────────────────────────────────
    "creative_professional": VendorProfile(
        vendor_type="creative_professional",
        display_name="Creative Professional",
        content_pillars=[
            "portfolio work", "process and behind the scenes",
            "tips and education", "client stories",
            "personal brand", "industry perspective",
        ],
        image_style=ImageStyle(
            mood="distinctive, confident, editorial, personal",
            color_palette="consistent with personal brand",
            lighting="depends on work type — consistent aesthetic is key",
            backgrounds=["workspace", "project context", "personal brand settings"],
            avoid="inconsistent aesthetic, stock photo feel, generic",
        ),
        lifestyle_scene_rules=LifestyleSceneRules(
            scene_types=[
                "work in progress — tools of the trade",
                "finished project hero shot",
                "you at work in your environment",
                "before and after of a project",
            ],
            model_guidance="For creatives, YOU are the brand. Include yourself naturally.",
            props=["your actual work tools", "projects in progress"],
            composition="Let your personal aesthetic lead. Grid should feel like a portfolio.",
            platform_notes={
                "instagram_feed": "Grid = portfolio. Consistent aesthetic.",
                "instagram_story": "Real-time process, tips, personality.",
            },
        ),
        caption_tone=(
            "Confident, knowledgeable, personal. Share perspective and expertise. "
            "Give value before asking for anything."
        ),
        hashtag_clusters=[
            ["#creativebusiness", "#freelance", "#creativeprofessional"],
            ["#makersgonnamake", "#createeveryday"],
        ],
        photo_prompts=[
            "Your best project this week",
            "Your workspace or tools",
            "A process shot — work in progress",
            "You working — make your personal brand visible",
        ],
        posting_frequency="3-4x per week",
    ),
}


def get_vendor_profile(vendor_type: str) -> VendorProfile:
    """Get a vendor profile by type. Falls back to service_local if unknown."""
    return VENDOR_PROFILES.get(vendor_type, VENDOR_PROFILES["service_local"])


async def detect_vendor_type_from_industry(industry: str) -> str:
    """
    Detect vendor type from industry string.
    Uses AI classification for ambiguous cases instead of pure keyword matching.
    """
    if not industry:
        return "service_local"

    industry_lower = industry.lower()

    # Fast keyword matching for clear cases
    if any(w in industry_lower for w in ["jewelry", "jewellery", "accessories", "gems"]):
        return "maker_jewelry"
    if any(w in industry_lower for w in ["ceramic", "pottery", "clay"]):
        return "maker_ceramics"
    if any(w in industry_lower for w in ["candle", "fragrance", "wax"]):
        return "maker_candles"
    if any(w in industry_lower for w in ["bakery", "baking", "pastry", "bread", "cake"]):
        return "food_bakery"
    if any(w in industry_lower for w in ["cafe", "coffee", "espresso", "tea room", "restaurant", "food & bev"]):
        return "food_cafe"
    if any(w in industry_lower for w in ["farm", "farmer", "market", "produce", "harvest", "flowers"]):
        return "farmer_market"
    if any(w in industry_lower for w in ["yoga", "fitness", "gym", "wellness", "health", "nutrition", "coaching", "therapy"]):
        return "health_wellness"
    if any(w in industry_lower for w in ["fashion", "clothing", "apparel", "boutique", "retail", "shoes"]):
        return "retail_fashion"
    if any(w in industry_lower for w in ["software", "saas", "app", "tech", "startup", "ai ", "platform", "tool", "developer", "professional services"]):
        return "software_saas"
    if any(w in industry_lower for w in ["photo", "design", "creative", "art", "illustrat"]):
        return "creative_professional"
    if any(w in industry_lower for w in ["craft", "handmade", "maker", "artisan", "textile", "leather"]):
        return "maker_jewelry"

    # For ambiguous cases, use AI classification
    try:
        import anthropic
        import os
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        vendor_types = list(VENDOR_PROFILES.keys())
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=20,
            messages=[{
                "role": "user",
                "content": f"""Classify this business industry into one vendor type.
Industry: "{industry}"
Options: {', '.join(vendor_types)}
Return ONLY the vendor type string, nothing else."""
            }]
        )
        result = response.content[0].text.strip().lower()
        if result in VENDOR_PROFILES:
            return result
    except Exception as e:
        print(f"[VendorProfiles] AI classification error: {e}")

    return "service_local"
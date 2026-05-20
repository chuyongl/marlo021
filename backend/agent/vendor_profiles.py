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
                "Negative space is your friend. "
                "For rings/earrings: close up at 45-degree angle."
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
            "Close-up of your hands working on a piece — show the process and texture",
            "Flat lay of your latest collection on white or linen background",
            "Someone wearing your piece in natural window light",
            "Detail shot of your most intricate piece — show the craftsmanship",
        ],
        posting_frequency="3-4x per week",
    ),

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
            model_guidance=(
                "Real maker hands are beautiful. In-use shots work best. "
                "No need for a face — hands and context tell the story."
            ),
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
            "A finished piece with coffee or flowers inside — in use",
            "Fresh-from-the-kiln pieces lined up",
            "Detail of glaze texture in window light",
        ],
        posting_frequency="3x per week",
    ),

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
                "instagram_feed": "Consistent warm palette. Dark and moody works well.",
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
        posting_frequency="3x per week, lean into seasonal moments",
    ),

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
                "styled on a cafe table or kitchen counter",
            ],
            model_guidance=(
                "Hands breaking bread feel authentic. Show steam if possible. "
                "Crumbs and imperfections are appetizing."
            ),
            props=["coffee cup", "small plants", "jam jars", "linen", "seasonal fruits"],
            composition="Show the inside when possible. Top-down for spreads.",
            platform_notes={
                "instagram_feed": "Bright and warm. Consistent warm palette.",
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
            "Your workspace early morning — dough, trays, the process",
            "This week's special with one or two props",
        ],
        posting_frequency="4-5x per week",
    ),

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
                "seasonal drink with seasonal props",
                "behind the bar — barista preparing drinks",
            ],
            model_guidance=(
                "Real customers or staff feel authentic. "
                "Hands wrapped around a warm mug is universally appealing."
            ),
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

    "farmer_market": VendorProfile(
        vendor_type="farmer_market",
        display_name="Farmer & Market Vendor",
        content_pillars=[
            "seasonal harvest", "market days",
            "farm life behind the scenes", "how to use / recipes",
            "community", "availability and pre-orders",
        ],
        image_style=ImageStyle(
            mood="honest, seasonal, earthy, abundant, real",
            color_palette="earth tones, deep greens, harvest golds, berry reds",
            lighting="natural outdoor light, golden hour for farm shots",
            backgrounds=["farm fields", "market stalls", "wooden crates", "baskets"],
            avoid="studio-looking images, overly polished, out-of-season colors",
        ),
        lifestyle_scene_rules=LifestyleSceneRules(
            scene_types=[
                "hands harvesting or holding produce in the field",
                "market stall abundance shot — full display",
                "close-up of produce showing freshness and color",
                "seasonal flat lay on wood or in basket",
                "farm landscape with product in foreground",
            ],
            model_guidance=(
                "Real farmer hands are best — weathered and authentic. "
                "Show scale by including hands with produce."
            ),
            props=["wooden crates", "baskets", "burlap", "seasonal leaves"],
            composition="Abundance reads well — fill the frame. Outdoor light beats studio.",
            platform_notes={
                "instagram_feed": "Seasonal color palette that shifts with harvest cycles.",
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
            "You or your hands in the field — show the real work",
            "Market stall setup before the rush",
            "Close-up of your most beautiful produce this week",
        ],
        posting_frequency="3-4x per week, timed around market days",
    ),

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
                "behind the scenes prep or tools",
            ],
            model_guidance=(
                "Real clients (with permission) are more powerful than stock. "
                "Team photos build trust."
            ),
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
                "tools and workspace detail",
            ],
            model_guidance=(
                "For creatives, YOU are the brand. "
                "Include yourself naturally — working, thinking, presenting."
            ),
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


def detect_vendor_type_from_industry(industry: str) -> str:
    """Auto-detect vendor type from industry string."""
    industry_lower = (industry or "").lower()
    if any(w in industry_lower for w in ["jewelry", "jewellery", "accessories", "gems"]):
        return "maker_jewelry"
    if any(w in industry_lower for w in ["ceramic", "pottery", "clay"]):
        return "maker_ceramics"
    if any(w in industry_lower for w in ["candle", "fragrance", "wax"]):
        return "maker_candles"
    if any(w in industry_lower for w in ["bakery", "baking", "pastry", "bread", "cake"]):
        return "food_bakery"
    if any(w in industry_lower for w in ["cafe", "coffee", "espresso", "tea room"]):
        return "food_cafe"
    if any(w in industry_lower for w in ["farm", "farmer", "market", "produce", "harvest", "flowers"]):
        return "farmer_market"
    if any(w in industry_lower for w in ["photo", "design", "creative", "art", "illustrat", "coach"]):
        return "creative_professional"
    if any(w in industry_lower for w in ["craft", "handmade", "maker", "artisan", "textile", "leather"]):
        return "maker_jewelry"
    return "service_local"
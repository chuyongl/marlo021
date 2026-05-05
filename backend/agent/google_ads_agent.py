"""
google_ads_agent.py
Generates Google Ads campaigns with budget-aware keyword strategy.
Tailors keyword type, volume, and match strategy to business size and budget.
"""
from agent.brain import brain
import json

# Budget tiers determine keyword strategy
BUDGET_TIERS = {
    "micro":  {"max": 100,  "daily": 3.33,  "keywords": 3,  "match": "exact",  "strategy": "hyper-local, ultra-specific long-tail only"},
    "small":  {"max": 300,  "daily": 10.0,  "keywords": 5,  "match": "exact+phrase", "strategy": "local intent + specific service keywords"},
    "medium": {"max": 700,  "daily": 23.33, "keywords": 8,  "match": "phrase",  "strategy": "service + competitor + local keywords"},
    "growth": {"max": 2000, "daily": 66.67, "keywords": 12, "match": "broad+phrase", "strategy": "full funnel: awareness + intent + local"},
}

# Industry-specific keyword patterns
INDUSTRY_PATTERNS = {
    "Food & Beverage": {
        "intent_signals": ["near me", "best", "delivery", "open now", "takeout"],
        "avoid": ["recipe", "how to make", "diy", "free"],
        "local_modifiers": True,
    },
    "Retail": {
        "intent_signals": ["buy", "shop", "store", "near me", "price", "sale"],
        "avoid": ["wholesale", "bulk", "manufacturer", "free sample"],
        "local_modifiers": True,
    },
    "Professional Services": {
        "intent_signals": ["hire", "consultant", "agency", "service", "expert", "help with"],
        "avoid": ["diy", "free template", "how to", "course", "job"],
        "local_modifiers": False,
    },
    "Health & Wellness": {
        "intent_signals": ["appointment", "near me", "clinic", "treatment", "results"],
        "avoid": ["free advice", "home remedy", "diy treatment"],
        "local_modifiers": True,
    },
    "Beauty & Personal Care": {
        "intent_signals": ["salon", "appointment", "near me", "prices", "best"],
        "avoid": ["diy", "at home", "tutorial", "free"],
        "local_modifiers": True,
    },
    "Fitness": {
        "intent_signals": ["gym", "classes", "membership", "personal trainer", "near me"],
        "avoid": ["free workout", "home workout", "youtube"],
        "local_modifiers": True,
    },
    "Technology": {
        "intent_signals": ["software", "tool", "platform", "automate", "solution", "pricing"],
        "avoid": ["free", "open source", "tutorial", "learn"],
        "local_modifiers": False,
    },
    "default": {
        "intent_signals": ["service", "near me", "professional", "best", "affordable"],
        "avoid": ["free", "diy", "how to", "tutorial"],
        "local_modifiers": True,
    }
}


def get_budget_tier(monthly_budget: float) -> dict:
    for tier_name, tier in BUDGET_TIERS.items():
        if monthly_budget <= tier["max"]:
            return {**tier, "name": tier_name}
    return {**BUDGET_TIERS["growth"], "name": "growth"}


def get_industry_pattern(industry: str) -> dict:
    for key in INDUSTRY_PATTERNS:
        if key.lower() in (industry or "").lower():
            return INDUSTRY_PATTERNS[key]
    return INDUSTRY_PATTERNS["default"]


class GoogleAdsAgent:

    async def generate_campaign(
        self,
        business: dict,
        strategy: dict,
        business_id: str,
    ) -> dict:
        """
        Generate a full Google Ads search campaign with budget-aware keyword strategy.
        Returns campaign dict with keywords, ad copy, budget, and match types.
        """
        monthly_budget = float(business.get("monthly_ad_budget", 300))
        tier = get_budget_tier(monthly_budget)
        industry_pattern = get_industry_pattern(business.get("industry", ""))

        prompt = f"""You are a Google Ads specialist creating a search campaign for a small business.

BUSINESS:
- Name: {business.get('name', 'Business')}
- Industry: {business.get('industry', 'General')}
- Description: {business.get('description', '')}
- Target audience: {business.get('target_audience', 'local customers')}
- Monthly ad budget: ${monthly_budget:.0f}/mo (${tier['daily']:.2f}/day)

BUDGET TIER: {tier['name'].upper()}
KEYWORD STRATEGY: {tier['strategy']}
MAX KEYWORDS: {tier['keywords']} (critical — do NOT exceed this)
MATCH TYPE FOCUS: {tier['match']}

INDUSTRY CONTEXT:
- High-intent signals to incorporate: {', '.join(industry_pattern['intent_signals'])}
- Negative keywords (MUST include these): {', '.join(industry_pattern['avoid'])}
- Use local modifiers (city/near me): {industry_pattern['local_modifiers']}

CONTENT STRATEGY INPUT:
- Key message: {strategy.get('key_message', '')}
- Call to action: {strategy.get('call_to_action', '')}
- Unique angle: {strategy.get('hook_strategy', '')}

KEYWORD RULES:
1. Every keyword must have clear purchase/hire intent — no informational queries
2. Long-tail preferred over broad (3+ words each for micro/small budgets)
3. No vanity keywords (just the business name) unless brand protection is needed
4. For micro/small budgets: exact match only — every click must count
5. Think like a customer who is READY TO BUY, not just browsing

AD COPY RULES:
- Headline 1 (max 30 chars): Lead with the strongest benefit or differentiator
- Headline 2 (max 30 chars): Include a trust signal or offer
- Headline 3 (max 30 chars): Clear call to action
- Description 1 (max 90 chars): Expand on the value proposition
- Description 2 (max 90 chars): Address an objection or reinforce CTA

Return ONLY valid JSON, no explanation:
{{
  "campaign_name": "descriptive campaign name",
  "campaign_goal": "one sentence describing what this campaign achieves",
  "daily_budget": {tier['daily']:.2f},
  "keywords": [
    {{"keyword": "exact keyword phrase", "match_type": "exact|phrase|broad", "intent": "why this converts"}}
  ],
  "negative_keywords": ["list", "of", "negative", "keywords"],
  "ad": {{
    "headline_1": "max 30 chars",
    "headline_2": "max 30 chars", 
    "headline_3": "max 30 chars",
    "description_1": "max 90 chars",
    "description_2": "max 90 chars",
    "final_url_suggestion": "what page this should land on"
  }},
  "bid_strategy": "recommended bid strategy for this budget",
  "estimated_clicks_per_day": "X-Y",
  "optimization_tip": "one specific tip for this business to improve performance"
}}"""

        raw = await brain.generate_content(
            content_type="google ads campaign JSON",
            business=business,
            context={},
            instructions=prompt
        )

        try:
            clean = raw.strip()
            if "```" in clean:
                clean = clean.split("```")[1]
                if clean.startswith("json"):
                    clean = clean[4:]
            campaign = json.loads(clean.strip())
        except Exception as e:
            print(f"[GoogleAdsAgent] JSON parse error: {e}")
            campaign = self._fallback_campaign(business, tier)

        # Enforce keyword count limit
        if "keywords" in campaign:
            campaign["keywords"] = campaign["keywords"][:tier["keywords"]]

        # Add metadata
        campaign["budget_tier"] = tier["name"]
        campaign["monthly_budget"] = monthly_budget

        return campaign

    def _fallback_campaign(self, business: dict, tier: dict) -> dict:
        name = business.get("name", "Business")
        industry = business.get("industry", "services")
        return {
            "campaign_name": f"{name} - Search",
            "campaign_goal": f"Drive qualified leads to {name}",
            "daily_budget": tier["daily"],
            "keywords": [
                {"keyword": f"{industry.lower()} near me", "match_type": "exact", "intent": "local purchase intent"},
                {"keyword": f"best {industry.lower()}", "match_type": "phrase", "intent": "comparison shopping"},
                {"keyword": f"hire {industry.lower()}", "match_type": "exact", "intent": "ready to buy"},
            ],
            "negative_keywords": ["free", "diy", "how to", "tutorial", "jobs"],
            "ad": {
                "headline_1": name[:30],
                "headline_2": "Professional Service",
                "headline_3": "Get Started Today",
                "description_1": f"Trusted {industry} for local customers. Results you can count on.",
                "description_2": "No contracts. Easy to get started. Contact us today.",
                "final_url_suggestion": "Homepage or dedicated landing page"
            },
            "bid_strategy": "Maximize clicks with a target CPC cap",
            "estimated_clicks_per_day": "5-10",
            "optimization_tip": "Start with exact match keywords only to control spend, then expand after 2 weeks of data."
        }


google_ads_agent = GoogleAdsAgent()
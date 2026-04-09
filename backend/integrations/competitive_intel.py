import httpx
import os

class CompetitiveIntel:

    async def get_competitor_keywords(self, domain: str) -> dict:
        """
        Get competitor's top keywords via SpyFu API.
        TODO: Enable when ready — requires SpyFu Basic plan (~$79/month).
        Sign up at spyfu.com, then add SPYFU_API_KEY to .env
        """
        api_key = os.getenv("SPYFU_API_KEY", "")
        if not api_key:
            return {
                "status": "not_configured",
                "message": "SpyFu API key not set. Add SPYFU_API_KEY to .env to enable this feature."
            }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://www.spyfu.com/apis/domain_stats_api/v2/getDomainStatsForExactDate",
                params={
                    "domain": domain,
                    "api_key": api_key,
                    "countryCode": "US"
                }
            )
        return response.json()

    async def get_meta_competitor_ads(self, search_terms: list) -> list:
        """
        Get competitor ads from Meta Ad Library (free, no API key needed).
        Search by keyword or page name to see what competitors are running.
        """
        access_token = os.getenv("META_APP_TOKEN", "")
        if not access_token:
            return []

        results = []
        async with httpx.AsyncClient() as client:
            for term in search_terms[:3]:  # Limit to 3 searches
                try:
                    response = await client.get(
                        "https://graph.facebook.com/v21.0/ads_archive",
                        params={
                            "access_token": access_token,
                            "ad_type": "ALL",
                            "ad_reached_countries": '["US"]',
                            "search_terms": term,
                            "fields": "id,ad_creative_bodies,ad_creative_link_captions,"
                                      "ad_creative_link_titles,page_name,spend,impressions,"
                                      "ad_delivery_start_time",
                            "limit": 10
                        }
                    )
                    data = response.json()
                    for ad in data.get("data", []):
                        results.append({
                            "term_searched": term,
                            "page_name": ad.get("page_name"),
                            "headline": ad.get("ad_creative_link_titles", [""])[0] if ad.get("ad_creative_link_titles") else "",
                            "body": ad.get("ad_creative_bodies", [""])[0] if ad.get("ad_creative_bodies") else "",
                            "started": ad.get("ad_delivery_start_time")
                        })
                except Exception as e:
                    print(f"Meta Ad Library error for term '{term}': {e}")
                    continue

        return results

    async def get_insights_for_business(self, business: dict) -> dict:
        """
        Main entry point — get competitive insights for a business.
        Called by the AI brain to inform ad strategy.
        """
        industry = business.get("industry", "")
        business_name = business.get("name", "")

        # Use industry + business name as search terms
        search_terms = [industry, f"{industry} near me", business_name]

        ads = await self.get_meta_competitor_ads(search_terms)

        return {
            "competitor_ads": ads,
            "ads_found": len(ads),
            "search_terms_used": search_terms,
            "spyfu_enabled": bool(os.getenv("SPYFU_API_KEY", ""))
        }

competitive_intel = CompetitiveIntel()
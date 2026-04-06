import httpx
from datetime import datetime, timedelta

class MetaIntegration:
    BASE_URL = "https://graph.facebook.com/v21.0"

    def __init__(self, access_token: str, ad_account_id: str):
        self.access_token = access_token
        self.ad_account_id = ad_account_id.replace("act_", "")

    async def get_campaign_insights(self, days_back: int = 7) -> list:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/act_{self.ad_account_id}/campaigns",
                params={
                    "access_token": self.access_token,
                    "fields": "id,name,status,objective,insights{impressions,clicks,reach,spend,"
                              "actions,purchase_roas,cpc,cpm,frequency,action_values}",
                    "date_preset": f"last_{days_back}_d",
                    "limit": 50
                }
            )
        data = response.json()
        campaigns = []
        for c in data.get("data", []):
            insights = (c.get("insights") or {}).get("data", [{}])[0]
            actions = {a["action_type"]: float(a["value"]) for a in insights.get("actions", [])}
            action_values = {a["action_type"]: float(a["value"]) for a in insights.get("action_values", [])}
            roas_list = insights.get("purchase_roas", [])
            roas = float(roas_list[0]["value"]) if roas_list else 0.0
            campaigns.append({
                "campaign_id": c["id"],
                "name": c["name"],
                "status": c["status"],
                "objective": c.get("objective"),
                "impressions": int(insights.get("impressions", 0)),
                "clicks": int(insights.get("clicks", 0)),
                "reach": int(insights.get("reach", 0)),
                "spend": float(insights.get("spend", 0)),
                "cpc": float(insights.get("cpc", 0)),
                "cpm": float(insights.get("cpm", 0)),
                "frequency": float(insights.get("frequency", 0)),
                "purchases": actions.get("purchase", 0),
                "purchase_value": action_values.get("purchase", 0),
                "roas": roas,
                "link_clicks": actions.get("link_click", 0),
                "add_to_cart": actions.get("add_to_cart", 0),
                "leads": actions.get("lead", 0)
            })
        return campaigns

    async def post_to_instagram(self, ig_account_id: str, image_url: str, caption: str) -> dict:
        async with httpx.AsyncClient() as client:
            container = await client.post(
                f"{self.BASE_URL}/{ig_account_id}/media",
                params={
                    "access_token": self.access_token,
                    "image_url": image_url,
                    "caption": caption
                }
            )
            container_data = container.json()
            if "id" not in container_data:
                return {"error": "Container creation failed", "details": container_data}

            publish = await client.post(
                f"{self.BASE_URL}/{ig_account_id}/media_publish",
                params={
                    "access_token": self.access_token,
                    "creation_id": container_data["id"]
                }
            )
        return publish.json()

    async def get_instagram_insights(self, ig_account_id: str, days_back: int = 7) -> dict:
        async with httpx.AsyncClient() as client:
            account = await client.get(
                f"{self.BASE_URL}/{ig_account_id}/insights",
                params={
                    "access_token": self.access_token,
                    "metric": "reach,impressions,follower_count,profile_views",
                    "period": "day",
                    "since": int((datetime.now() - timedelta(days=days_back)).timestamp()),
                    "until": int(datetime.now().timestamp())
                }
            )
            media = await client.get(
                f"{self.BASE_URL}/{ig_account_id}/media",
                params={
                    "access_token": self.access_token,
                    "fields": "id,caption,media_type,timestamp,like_count,comments_count,"
                              "insights.metric(reach,impressions,engagement,saves)",
                    "limit": 20
                }
            )
        return {
            "account_insights": account.json(),
            "recent_posts": media.json()
        }
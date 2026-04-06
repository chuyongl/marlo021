import httpx
from datetime import datetime
from typing import Optional

class MailchimpIntegration:
    def __init__(self, api_key: str, list_id: str = None):
        self.api_key = api_key
        datacenter = api_key.split("-")[-1]
        self.base_url = f"https://{datacenter}.api.mailchimp.com/3.0"
        self.list_id = list_id
        self.headers = {"Authorization": f"Bearer {api_key}"}

    async def get_list_stats(self) -> dict:
        async with httpx.AsyncClient() as client:
            r = await client.get(
                f"{self.base_url}/lists/{self.list_id}",
                headers=self.headers,
                params={"fields": "stats,name"}
            )
        stats = r.json().get("stats", {})
        return {
            "total_subscribers": stats.get("member_count", 0),
            "open_rate": round(stats.get("open_rate", 0) * 100, 1),
            "click_rate": round(stats.get("click_rate", 0) * 100, 1),
            "unsubscribe_rate": round(stats.get("unsubscribe_rate", 0) * 100, 2),
            "campaign_count": stats.get("campaign_count", 0)
        }

    async def get_recent_campaigns(self, count: int = 5) -> list:
        async with httpx.AsyncClient() as client:
            r = await client.get(
                f"{self.base_url}/campaigns",
                headers=self.headers,
                params={
                    "count": count, "list_id": self.list_id,
                    "status": "sent", "sort_field": "send_time", "sort_dir": "DESC",
                    "fields": "campaigns.id,campaigns.settings.subject_line,"
                              "campaigns.send_time,campaigns.report_summary"
                }
            )
        campaigns = []
        for c in r.json().get("campaigns", []):
            s = c.get("report_summary", {})
            campaigns.append({
                "id": c["id"],
                "subject": c.get("settings", {}).get("subject_line"),
                "sent_at": c.get("send_time"),
                "opens": s.get("opens", 0),
                "clicks": s.get("clicks", 0),
                "open_rate": round(s.get("open_rate", 0) * 100, 1),
                "click_rate": round(s.get("click_rate", 0) * 100, 1)
            })
        return campaigns

    async def create_and_send_campaign(
        self,
        subject: str,
        preview_text: str,
        body_html: str,
        from_name: str,
        from_email: str,
        segment_id: Optional[str] = None,
        schedule_time: Optional[datetime] = None
    ) -> dict:
        async with httpx.AsyncClient() as client:
            recipients = {"list_id": self.list_id}
            if segment_id:
                recipients["segment_opts"] = {"saved_segment_id": int(segment_id)}

            create_r = await client.post(
                f"{self.base_url}/campaigns",
                headers=self.headers,
                json={
                    "type": "regular",
                    "recipients": recipients,
                    "settings": {
                        "subject_line": subject,
                        "preview_text": preview_text,
                        "title": f"Marlo AI — {subject[:30]}",
                        "from_name": from_name,
                        "reply_to": from_email
                    }
                }
            )
            campaign_id = create_r.json().get("id")
            if not campaign_id:
                return {"error": "Campaign creation failed"}

            await client.put(
                f"{self.base_url}/campaigns/{campaign_id}/content",
                headers=self.headers,
                json={"html": body_html}
            )

            if schedule_time:
                action_r = await client.post(
                    f"{self.base_url}/campaigns/{campaign_id}/actions/schedule",
                    headers=self.headers,
                    json={"schedule_time": schedule_time.isoformat()}
                )
            else:
                action_r = await client.post(
                    f"{self.base_url}/campaigns/{campaign_id}/actions/send",
                    headers=self.headers
                )

        return {"campaign_id": campaign_id, "status": "scheduled" if schedule_time else "sent"}
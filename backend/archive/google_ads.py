from google.ads.googleads.client import GoogleAdsClient
from google.oauth2.credentials import Credentials
from datetime import datetime, timedelta
import os

class GoogleAdsIntegration:
    def __init__(self, access_token: str, refresh_token: str, customer_id: str):
        credentials = Credentials(
            token=access_token,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=os.getenv("GOOGLE_CLIENT_ID"),
            client_secret=os.getenv("GOOGLE_CLIENT_SECRET")
        )
        self.client = GoogleAdsClient(
            credentials=credentials,
            developer_token=os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN"),
            login_customer_id=customer_id
        )
        self.customer_id = customer_id.replace("-", "")

    def get_campaign_performance(self, days_back: int = 7) -> list:
        ga_service = self.client.get_service("GoogleAdsService")
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")

        query = f"""
        SELECT
          campaign.id, campaign.name, campaign.status,
          metrics.impressions, metrics.clicks, metrics.ctr,
          metrics.conversions, metrics.conversions_value,
          metrics.cost_micros, metrics.average_cpc,
          metrics.search_impression_share
        FROM campaign
        WHERE segments.date BETWEEN '{start_date}' AND '{end_date}'
          AND campaign.status != 'REMOVED'
        ORDER BY metrics.cost_micros DESC
        """

        response = ga_service.search_stream(customer_id=self.customer_id, query=query)
        campaigns = []
        for batch in response:
            for row in batch.results:
                campaigns.append({
                    "campaign_id": str(row.campaign.id),
                    "name": row.campaign.name,
                    "status": row.campaign.status.name,
                    "impressions": row.metrics.impressions,
                    "clicks": row.metrics.clicks,
                    "ctr": round(row.metrics.ctr * 100, 2),
                    "conversions": row.metrics.conversions,
                    "conversion_value": row.metrics.conversions_value,
                    "spend": round(row.metrics.cost_micros / 1_000_000, 2),
                    "avg_cpc": round(row.metrics.average_cpc / 1_000_000, 2),
                    "impression_share": round(row.metrics.search_impression_share * 100, 1)
                })
        return campaigns

    def update_campaign_budget(self, campaign_id: str, new_daily_budget_usd: float) -> bool:
        """Update daily budget. Only called after guardrail approval."""
        ga_service = self.client.get_service("GoogleAdsService")
        query = f"SELECT campaign.campaign_budget FROM campaign WHERE campaign.id = {campaign_id}"
        response = ga_service.search_stream(customer_id=self.customer_id, query=query)

        budget_resource = None
        for batch in response:
            for row in batch.results:
                budget_resource = row.campaign.campaign_budget

        if not budget_resource:
            return False

        budget_service = self.client.get_service("CampaignBudgetService")
        op = self.client.get_type("CampaignBudgetOperation")
        budget = op.update
        budget.resource_name = budget_resource
        budget.amount_micros = int(new_daily_budget_usd * 1_000_000)
        op.update_mask.paths.append("amount_micros")
        budget_service.mutate_campaign_budgets(customer_id=self.customer_id, operations=[op])
        return True
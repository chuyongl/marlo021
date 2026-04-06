from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    RunReportRequest, Dimension, Metric, DateRange
)
from google.oauth2.credentials import Credentials

class GA4Integration:
    def __init__(self, access_token: str, property_id: str):
        self.client = BetaAnalyticsDataClient(
            credentials=Credentials(token=access_token)
        )
        self.property = f"properties/{property_id}"

    def get_overview(self, days_back: int = 7) -> dict:
        request = RunReportRequest(
            property=self.property,
            date_ranges=[DateRange(start_date=f"{days_back}daysAgo", end_date="today")],
            dimensions=[
                Dimension(name="sessionSourceMedium"),
                Dimension(name="deviceCategory")
            ],
            metrics=[
                Metric(name="sessions"), Metric(name="activeUsers"),
                Metric(name="newUsers"), Metric(name="bounceRate"),
                Metric(name="averageSessionDuration"), Metric(name="conversions"),
                Metric(name="totalRevenue")
            ]
        )
        response = self.client.run_report(request)
        results = []
        for row in response.rows:
            results.append({
                "source": row.dimension_values[0].value,
                "device": row.dimension_values[1].value,
                "sessions": int(row.metric_values[0].value),
                "active_users": int(row.metric_values[1].value),
                "new_users": int(row.metric_values[2].value),
                "bounce_rate": round(float(row.metric_values[3].value) * 100, 1),
                "avg_session_duration": round(float(row.metric_values[4].value), 0),
                "conversions": int(row.metric_values[5].value),
                "revenue": round(float(row.metric_values[6].value), 2)
            })
        return {"traffic_sources": results}
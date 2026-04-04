"""
Mock data that mirrors the exact shape of real API responses.
Used in development when real accounts aren't connected.
Swap out by setting USE_MOCK_DATA=false in .env once accounts are connected.
"""

MOCK_GOOGLE_CAMPAIGNS = [
    {
        "campaign_id": "1234567890",
        "name": "Search — Brand Keywords",
        "status": "ENABLED",
        "impressions": 4200, "clicks": 210,
        "ctr": 5.0, "conversions": 18,
        "conversion_value": 540.0, "spend": 95.40,
        "avg_cpc": 0.45, "impression_share": 72.3
    },
    {
        "campaign_id": "9876543210",
        "name": "Search — Local Area",
        "status": "ENABLED",
        "impressions": 1800, "clicks": 54,
        "ctr": 3.0, "conversions": 3,
        "conversion_value": 90.0, "spend": 43.20,
        "avg_cpc": 0.80, "impression_share": 38.1
    }
]

MOCK_META_CAMPAIGNS = [
    {
        "campaign_id": "meta_111",
        "name": "Instagram Awareness — Spring",
        "status": "ACTIVE",
        "impressions": 8500, "clicks": 340,
        "reach": 6200, "spend": 45.00,
        "cpc": 0.13, "cpm": 5.29,
        "frequency": 1.37, "purchases": 6,
        "purchase_value": 180.0, "roas": 4.0,
        "link_clicks": 280, "add_to_cart": 14, "leads": 0
    }
]

MOCK_EMAIL_STATS = {
    "total_subscribers": 842,
    "open_rate": 28.4,
    "click_rate": 4.1,
    "unsubscribe_rate": 0.3,
    "campaign_count": 12
}

MOCK_EMAIL_CAMPAIGNS = [
    {"id": "c1", "subject": "Our spring menu is here 🌸", "sent_at": "2026-03-01",
     "opens": 238, "clicks": 34, "open_rate": 28.3, "click_rate": 4.0},
    {"id": "c2", "subject": "Weekend special: sourdough loaves", "sent_at": "2026-02-22",
     "opens": 251, "clicks": 41, "open_rate": 29.8, "click_rate": 4.9}
]

MOCK_GA4_DATA = {
    "traffic_sources": [
        {"source": "google / cpc", "sessions": 420, "new_users": 380, "bounce_rate": 42.1,
         "avg_session_duration": 95, "conversions": 18, "revenue": 540.0},
        {"source": "instagram / social", "sessions": 180, "new_users": 155, "bounce_rate": 61.2,
         "avg_session_duration": 45, "conversions": 4, "revenue": 120.0},
        {"source": "direct / (none)", "sessions": 310, "new_users": 48, "bounce_rate": 35.5,
         "avg_session_duration": 140, "conversions": 22, "revenue": 660.0}
    ]
}
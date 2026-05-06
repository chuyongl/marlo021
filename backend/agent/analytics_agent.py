"""
analytics_agent.py
Collects all available data for a business, feeds it to Claude for deep analysis,
and returns structured insights for the weekly analytics email.
"""
from agent.brain import brain
import json

class AnalyticsAgent:

    async def generate_weekly_insights(self, business_id: str, db) -> dict:
        """
        Collect all data from the past week and generate deep AI insights.
        Returns structured analytics dict for the email template.
        """
        from database.models import AgentAction, PlatformIntegration, Business, User
        from database.models import CampaignMetric
        from sqlalchemy import select
        from datetime import datetime, timedelta, timezone

        week_ago = datetime.now(timezone.utc) - timedelta(days=7)

        # Load business
        biz_result = await db.execute(select(Business).where(Business.id == business_id))
        biz = biz_result.scalar_one_or_none()
        if not biz:
            return {}

        business_dict = {
            "name": biz.name,
            "industry": biz.industry or "",
            "target_audience": biz.target_audience or "",
            "tone_of_voice": biz.tone_of_voice or "",
            "monthly_ad_budget": float(biz.monthly_ad_budget or 300),
        }

        # ── Posting performance ───────────────────────────────────────────────
        actions_result = await db.execute(
            select(AgentAction).where(
                AgentAction.business_id == business_id,
                AgentAction.created_at >= week_ago,
            )
        )
        actions = actions_result.scalars().all()

        post_actions   = [a for a in actions if a.action_type in ("post_instagram", "post_facebook")]
        approved_posts = [a for a in post_actions if a.status == "executed"]
        skipped_posts  = [a for a in post_actions if a.status == "rejected"]
        expired_posts  = [a for a in post_actions if a.status == "expired"]

        posting_stats = {
            "total_generated": len(post_actions),
            "approved": len(approved_posts),
            "skipped": len(skipped_posts),
            "expired": len(expired_posts),
            "approval_rate": round(len(approved_posts) / len(post_actions) * 100) if post_actions else 0,
        }

        # ── Instagram insights ────────────────────────────────────────────────
        instagram_data = {}
        meta_result = await db.execute(
            select(PlatformIntegration).where(
                PlatformIntegration.business_id == business_id,
                PlatformIntegration.platform == "meta",
                PlatformIntegration.is_active == True,
            )
        )
        meta_integration = meta_result.scalar_one_or_none()

        if meta_integration and meta_integration.platform_account_id:
            try:
                from integrations.meta import MetaIntegration
                meta = MetaIntegration(
                    access_token=meta_integration.access_token,
                    ad_account_id=meta_integration.platform_account_id
                )
                raw_insights = await meta.get_instagram_insights(
                    ig_account_id=meta_integration.platform_account_id,
                    days_back=7
                )
                account = raw_insights.get("account_insights", {})
                recent_media = raw_insights.get("recent_posts", {}).get("data", [])

                # Aggregate account metrics
                total_reach = 0
                total_impressions = 0
                for entry in account.get("data", []):
                    if entry.get("name") == "reach":
                        total_reach += sum(v.get("value", 0) for v in entry.get("values", []))
                    elif entry.get("name") == "impressions":
                        total_impressions += sum(v.get("value", 0) for v in entry.get("values", []))

                # Per-post engagement
                post_details = []
                for post in recent_media[:7]:
                    post_insights = {}
                    for metric in (post.get("insights", {}).get("data", [])):
                        post_insights[metric["name"]] = metric.get("values", [{}])[0].get("value", 0)
                    post_details.append({
                        "caption_preview": (post.get("caption") or "")[:80],
                        "likes": post.get("like_count", 0),
                        "comments": post.get("comments_count", 0),
                        "reach": post_insights.get("reach", 0),
                        "impressions": post_insights.get("impressions", 0),
                        "engagement": post_insights.get("engagement", 0),
                        "saves": post_insights.get("saves", 0),
                        "timestamp": post.get("timestamp", ""),
                    })

                instagram_data = {
                    "total_reach": total_reach,
                    "total_impressions": total_impressions,
                    "posts_analyzed": len(post_details),
                    "post_details": post_details,
                    "avg_likes": round(sum(p["likes"] for p in post_details) / len(post_details)) if post_details else 0,
                    "avg_reach": round(sum(p["reach"] for p in post_details) / len(post_details)) if post_details else 0,
                    "total_saves": sum(p["saves"] for p in post_details),
                }
            except Exception as e:
                print(f"[AnalyticsAgent] Instagram insights error: {e}")

        # ── Google Ads metrics ────────────────────────────────────────────────
        google_data = {}
        google_result = await db.execute(
            select(PlatformIntegration).where(
                PlatformIntegration.business_id == business_id,
                PlatformIntegration.platform == "google",
                PlatformIntegration.is_active == True,
            )
        )
        google_integration = google_result.scalar_one_or_none()

        if google_integration:
            try:
                metrics_result = await db.execute(
                    select(CampaignMetric).where(
                        CampaignMetric.date >= week_ago,
                    )
                )
                metrics = metrics_result.scalars().all()
                if metrics:
                    google_data = {
                        "total_impressions": sum(m.impressions for m in metrics),
                        "total_clicks": sum(m.clicks for m in metrics),
                        "total_spend": float(sum(m.spend for m in metrics)),
                        "total_conversions": sum(m.conversions for m in metrics),
                        "avg_cpc": round(float(sum(m.cpc or 0 for m in metrics)) / len(metrics), 2),
                        "avg_ctr": round(sum(m.clicks for m in metrics) / max(sum(m.impressions for m in metrics), 1) * 100, 2),
                    }
            except Exception as e:
                print(f"[AnalyticsAgent] Google metrics error: {e}")

        # ── AI Analysis ───────────────────────────────────────────────────────
        data_summary = {
            "business": business_dict,
            "posting_stats": posting_stats,
            "instagram": instagram_data,
            "google_ads": google_data,
        }

        prompt = f"""You are a senior digital marketing analyst reviewing one week of performance data for a small business.

BUSINESS:
- Name: {business_dict['name']}
- Industry: {business_dict['industry']}
- Target audience: {business_dict['target_audience']}
- Monthly ad budget: ${business_dict['monthly_ad_budget']}

WEEK'S DATA:
{json.dumps(data_summary, indent=2)}

Analyze this data deeply and return ONLY valid JSON with these fields:

{{
  "headline_metric": "the single most important number this week (e.g. '2,847 people reached')",
  "performance_summary": "2-3 sentence plain English summary of how the week went overall",
  "reach_analysis": {{
    "total_people_reached": number or null,
    "reach_breakdown": "where the reach came from (Instagram, Google, etc)",
    "reach_vs_budget": "how efficient was the spend at reaching people"
  }},
  "audience_insights": [
    "specific insight about who is engaging (time, demographics, behavior)",
    "another specific insight",
    "another specific insight"
  ],
  "content_performance": {{
    "best_performing_content": "what type/topic worked best and why",
    "worst_performing_content": "what didn't work and why",
    "engagement_pattern": "when and what drove the most engagement"
  }},
  "keyword_insights": [
    "specific keyword that performed well, why, and what audience it reached",
    "another keyword insight"
  ],
  "conversion_analysis": "what happened at the conversion level — clicks, leads, purchases",
  "next_week_strategy": [
    "specific, actionable recommendation based on this week's data",
    "another specific recommendation",
    "another specific recommendation"
  ],
  "budget_recommendation": "should they increase/decrease/reallocate budget and why",
  "one_thing_to_watch": "the single most important thing to monitor next week"
}}

Be specific and data-driven. If data is missing for a field, say so honestly rather than guessing."""

        raw = await brain.generate_content(
            content_type="weekly analytics JSON",
            business=business_dict,
            context={},
            instructions=prompt
        )

        try:
            clean = raw.strip()
            if "```" in clean:
                clean = clean.split("```")[1]
                if clean.startswith("json"):
                    clean = clean[4:]
            insights = json.loads(clean.strip())
        except Exception as e:
            print(f"[AnalyticsAgent] JSON parse error: {e}")
            insights = {
                "headline_metric": f"{posting_stats['approved']} posts published",
                "performance_summary": f"This week {business_dict['name']} published {posting_stats['approved']} posts with an approval rate of {posting_stats['approval_rate']}%.",
                "reach_analysis": {"total_people_reached": instagram_data.get("total_reach"), "reach_breakdown": "Instagram organic", "reach_vs_budget": "Data pending"},
                "audience_insights": ["More data needed for audience insights — check back next week"],
                "content_performance": {"best_performing_content": "Insufficient data", "worst_performing_content": "Insufficient data", "engagement_pattern": "Insufficient data"},
                "keyword_insights": ["Google Ads data pending"],
                "conversion_analysis": "Conversion data not yet available",
                "next_week_strategy": ["Continue publishing consistently", "Monitor engagement on approved posts", "Reply to any comments to boost reach"],
                "budget_recommendation": "Maintain current budget while establishing baseline metrics",
                "one_thing_to_watch": "Post engagement rate on the first week of content"
            }

        # Attach raw stats for template rendering
        insights["_raw"] = {
            "posting_stats": posting_stats,
            "instagram": instagram_data,
            "google_ads": google_data,
        }

        return insights


analytics_agent = AnalyticsAgent()
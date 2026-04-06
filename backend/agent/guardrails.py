import redis.asyncio as aioredis
import os
from datetime import datetime, date
from dotenv import load_dotenv

load_dotenv(dotenv_path="../../.env")

class GuardrailSystem:
    """
    Deterministic safety system. Runs BEFORE any agent action is executed.
    Budget limits are enforced here in Python — not in the LLM prompt.
    Even if the AI hallucinates, it physically cannot exceed these limits.
    """

    def __init__(self):
        self._redis = None

    async def _get_redis(self):
        if not self._redis:
            self._redis = await aioredis.from_url(
                os.getenv("REDIS_URL", "redis://localhost:6379")
            )
        return self._redis

    def _daily_key(self, business_id: str, platform: str) -> str:
        return f"spend:daily:{business_id}:{platform}:{date.today().isoformat()}"

    def _monthly_key(self, business_id: str) -> str:
        return f"spend:monthly:{business_id}:{datetime.now().strftime('%Y-%m')}"

    async def record_spend(self, business_id: str, platform: str, amount: float):
        r = await self._get_redis()
        pipe = r.pipeline()
        daily_key = self._daily_key(business_id, platform)
        monthly_key = self._monthly_key(business_id)
        pipe.incrbyfloat(daily_key, amount)
        pipe.expire(daily_key, 86400 * 2)
        pipe.incrbyfloat(monthly_key, amount)
        pipe.expire(monthly_key, 86400 * 35)
        await pipe.execute()

    async def get_current_spend(self, business_id: str, platform: str = "all") -> dict:
        r = await self._get_redis()
        daily = await r.get(self._daily_key(business_id, platform))
        monthly = await r.get(self._monthly_key(business_id))
        return {
            "daily": float(daily or 0),
            "monthly": float(monthly or 0)
        }

    async def check_spend_action(
        self,
        business_id: str,
        platform: str,
        proposed_spend: float,
        monthly_budget: float
    ) -> dict:
        current = await self.get_current_spend(business_id, platform)
        daily_budget = monthly_budget / 30

        if current["monthly"] + proposed_spend > monthly_budget:
            return {
                "allowed": False,
                "requires_approval": False,
                "risk": "blocked",
                "reason": f"Monthly budget cap reached. Spent ${current['monthly']:.2f} of ${monthly_budget:.2f} allowed."
            }

        if current["daily"] + proposed_spend > daily_budget * 2:
            return {
                "allowed": False,
                "requires_approval": False,
                "risk": "blocked",
                "reason": f"Daily spend would exceed 2× daily budget (${daily_budget * 2:.2f})."
            }

        if proposed_spend > 100:
            return {
                "allowed": True,
                "requires_approval": True,
                "risk": "high",
                "reason": "Single action over $100 requires your approval."
            }

        if proposed_spend > daily_budget * 0.5:
            return {
                "allowed": True,
                "requires_approval": True,
                "risk": "medium",
                "reason": f"Action is more than 50% of your daily budget (${daily_budget:.2f})."
            }

        return {
            "allowed": True,
            "requires_approval": False,
            "risk": "low",
            "reason": "Within normal parameters."
        }

    async def check_bid_change(self, current_bid: float, proposed_bid: float) -> dict:
        change_pct = abs(proposed_bid - current_bid) / max(current_bid, 0.01) * 100

        if change_pct > 50:
            return {
                "allowed": False,
                "requires_approval": False,
                "risk": "blocked",
                "reason": f"Bid change of {change_pct:.0f}% exceeds the 50% single-step limit."
            }

        if change_pct > 20:
            return {
                "allowed": True,
                "requires_approval": True,
                "risk": "medium",
                "reason": f"Bid change of {change_pct:.0f}% requires your approval (threshold is 20%)."
            }

        return {
            "allowed": True,
            "requires_approval": False,
            "risk": "low",
            "reason": f"Bid change of {change_pct:.0f}% is within safe limits."
        }

    async def check_email_send(self, recipient_count: int, business_id: str) -> dict:
        r = await self._get_redis()
        week_key = f"emails:sent:{business_id}:{datetime.now().strftime('%Y-%W')}"
        count = int(await r.get(week_key) or 0)

        if count >= 2:
            return {
                "allowed": False,
                "requires_approval": False,
                "risk": "blocked",
                "reason": f"Already sent {count} email campaigns this week. Max is 2 per week."
            }

        if recipient_count > 1000:
            return {
                "allowed": True,
                "requires_approval": True,
                "risk": "medium",
                "reason": f"Sending to {recipient_count:,} people requires your approval."
            }

        return {
            "allowed": True,
            "requires_approval": False,
            "risk": "low",
            "reason": f"Email send to {recipient_count:,} recipients approved."
        }

    async def circuit_breaker_check(self, business_id: str) -> dict:
        """Emergency stop if hourly spend is 3× the normal rate."""
        r = await self._get_redis()
        hour_key = f"spend:hourly:{business_id}:{datetime.now().strftime('%Y-%m-%d-%H')}"
        avg_key = f"spend:7day_avg:{business_id}"

        hourly = float(await r.get(hour_key) or 0)
        avg = float(await r.get(avg_key) or 0)

        if avg > 0 and hourly > avg * 3:
            return {
                "tripped": True,
                "reason": f"Unusual spend detected: ${hourly:.2f} this hour vs ${avg:.2f} average. All spending halted."
            }
        return {"tripped": False}

guardrails = GuardrailSystem()
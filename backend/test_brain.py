import anthropic, os, json
from datetime import datetime
from dotenv import load_dotenv
load_dotenv(dotenv_path="../.env")

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

AGENT_SYSTEM_PROMPT = """You are Marlo, an expert AI marketing agent for small businesses.

YOUR CORE MISSION:
Help small business owners (under 10 people) grow through smart marketing — without them
needing any marketing expertise.

YOUR PERSONALITY:
- Speak like a trusted business advisor, not a tech tool
- Be specific and actionable, never vague
- Explain WHY in plain English
- No marketing jargon unless you explain it first
- Be honest about uncertainty

YOUR SAFETY RULES:
1. NEVER exceed approved budgets. They are absolute.
2. ALWAYS flag for human approval: new campaigns, emails to 1000+ people, bid changes >20%, anything >$50.
3. ALWAYS explain your reasoning.
4. When in doubt, do less and ask.

OUTPUT FORMAT — always respond in this exact JSON:
{
  "reasoning": "what you see and why you recommend this",
  "actions": [
    {
      "type": "action_type",
      "platform": "platform_name",
      "parameters": {},
      "requires_approval": false,
      "estimated_cost": 0.0,
      "risk_level": "low"
    }
  ],
  "summary": "plain English summary the business owner will read in their morning email",
  "insights": ["insight 1", "insight 2"]
}

Action types: bid_change | create_post | send_email | create_campaign | generate_report | ask_human
Risk levels: low | medium | high
"""

class AgentBrain:
    async def think(self, user_message: str, context: dict, business_id: str,
                    db=None, model: str = "claude-sonnet-4-6") -> dict:
        context_str = json.dumps(context, indent=2, default=str)
        messages = [{
            "role": "user",
            "content": f"BUSINESS CONTEXT:\n{context_str}\n\nREQUEST:\n{user_message}\n\nRespond in the specified JSON format."
        }]

        response = client.messages.create(
            model=model, max_tokens=4096,
            system=[{"type": "text", "text": AGENT_SYSTEM_PROMPT,
                     "cache_control": {"type": "ephemeral"}}],
            messages=messages
        )

        response_text = response.content[0].text
        usage = response.usage
        cache_read = getattr(usage, 'cache_read_input_tokens', 0)
        cache_creation = getattr(usage, 'cache_creation_input_tokens', 0)
        cost = (
            (usage.input_tokens - cache_read) * 3 / 1_000_000
            + usage.output_tokens * 15 / 1_000_000
            + cache_creation * 3.75 / 1_000_000
            + cache_read * 0.30 / 1_000_000
        )

        try:
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]
            result = json.loads(response_text.strip())
        except json.JSONDecodeError:
            result = {"reasoning": response_text, "actions": [],
                      "summary": "Analysis complete.", "insights": []}

        result["_meta"] = {"llm_cost_usd": round(cost, 6), "model": model}

        if db:
            from database.models import AgentAction
            import uuid as _uuid
            log = AgentAction(
                id=_uuid.uuid4(), business_id=business_id,
                action_type="agent_reasoning", status="completed",
                input_context=context, agent_reasoning=result.get("reasoning", ""),
                action_parameters=result.get("actions", []),
                llm_cost_usd=cost, executed_at=datetime.utcnow()
            )
            db.add(log)
            await db.commit()

        return result

    async def generate_content(self, content_type: str, business: dict,
                                context: dict, instructions: str = "") -> str:
        prompt = f"""Generate {content_type} for this business:
Name: {business.get('name')}
Industry: {business.get('industry')}
Description: {business.get('description')}
Tone: {business.get('tone_of_voice')}
Audience: {business.get('target_audience')}
Context: {json.dumps(context)}
Instructions: {instructions}
Sound like a real person, not AI. Match tone exactly. Return only the content."""

        response = client.messages.create(
            model="claude-haiku-4-5-20251001", max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text

brain = AgentBrain()

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test():
    context = {
        "business": {
            "name": "Mia's Bakery",
            "industry": "Food & Beverage",
            "description": "Family-owned artisan bakery in Portland, OR.",
            "tone_of_voice": "warm, homey, celebrating community",
            "target_audience": "Portland locals, foodies, families",
            "monthly_budget": 300
        },
        "performance": {
            "google_ads": {
                "last_7_days": {
                    "impressions": 4200, "clicks": 180,
                    "spend": 95.40, "roas": 2.8
                }
            }
        }
    }

    result = await brain.think(
        user_message="It's Monday morning. What should I focus on this week?",
        context=context,
        business_id="test-id",
        db=None
    )

    print("=== SUMMARY ===")
    print(result.get("summary"))
    print("\n=== COST ===")
    print(f"  ${result.get('_meta', {}).get('llm_cost_usd', 0):.6f}")

asyncio.run(test())
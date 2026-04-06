import fal_client
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path="../../.env")
fal_client.api_key = os.getenv("FAL_API_KEY", "")

# Register at fal.ai to get an API key — $10 credit gets you ~180 images at Flux Pro pricing

PLATFORM_SIZES = {
    "instagram_feed":   {"width": 1024, "height": 1024},   # 1:1 square
    "instagram_story":  {"width": 1024, "height": 1792},   # 9:16 vertical
    "facebook_feed":    {"width": 1024, "height": 1024},
    "tiktok":           {"width": 1024, "height": 1792},
    "google_display":   {"width": 1792, "height": 1024},   # 16:9 landscape
    "email_header":     {"width": 1792, "height": 600},
}

class ImageGenerator:
    async def generate(
        self,
        subject: str,
        business: dict,
        platform: str = "instagram_feed",
        extra_instructions: str = ""
    ) -> dict:
        size = PLATFORM_SIZES.get(platform, {"width": 1024, "height": 1024})

        prompt = f"""
{subject}.
Business type: {business.get('industry', '')} business.
Mood and style: {business.get('tone_of_voice', 'professional, warm, inviting')}.
{extra_instructions}
High quality commercial photography, no text overlay, no watermarks,
clean composition optimized for {platform.replace('_', ' ')} format.
""".strip()

        result = await fal_client.run_async(
            "fal-ai/flux-pro/v1.1",
            arguments={
                "prompt": prompt,
                "image_size": f"{size['width']}x{size['height']}",
                "num_inference_steps": 25,
                "guidance_scale": 3.5,
                "num_images": 1,
                "safety_tolerance": "2"
            }
        )

        return {
            "url": result["images"][0]["url"],
            "width": size["width"],
            "height": size["height"],
            "platform": platform,
            "prompt": prompt
        }

    async def generate_campaign_set(self, business: dict, offer: str) -> list:
        """Generate a full set of assets for a campaign across all platforms."""
        import asyncio
        tasks = [
            self.generate(offer, business, "instagram_feed"),
            self.generate(offer, business, "instagram_story"),
            self.generate(offer, business, "google_display"),
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [r for r in results if not isinstance(r, Exception)]

image_gen = ImageGenerator()
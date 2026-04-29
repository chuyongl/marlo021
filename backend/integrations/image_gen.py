import fal_client
import os
import io
import uuid
import httpx
import aiofiles
from PIL import Image
from dotenv import load_dotenv

load_dotenv(dotenv_path="../../.env")
fal_client.api_key = os.getenv("FAL_API_KEY", "")

PLATFORM_SIZES = {
    "instagram_feed":   {"width": 1024, "height": 1024},
    "instagram_story":  {"width": 1024, "height": 1792},
    "facebook_feed":    {"width": 1024, "height": 1024},
    "tiktok":           {"width": 1024, "height": 1792},
    "google_display":   {"width": 1792, "height": 1024},
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
                "image_size": size,  # dict with width/height, not a string
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

    async def upload_image(self, file_path: str) -> dict:
        """Upload a local image file to fal.ai's storage and get a URL back."""
        result = await fal_client.upload_file_async(file_path)
        return {"url": result}

    async def enhance_photo(self, image_url: str) -> str:
        """Enhance a photo for ad use."""
        result = await fal_client.run_async(
            "fal-ai/clarity-upscaler",
            arguments={
                "image_url": image_url,
                "scale": 2,
                "creativity": 0.35,
                "resemblance": 0.9,
                "prompt": "professional product photography, clean background, good lighting",
            }
        )
        return result.get("image", {}).get("url", image_url)

    async def prepare_photo_for_platforms(
        self,
        enhanced_url: str,
        business: dict,
        caption_hint: str = ""
    ) -> dict:
        from agent.brain import brain

        temp_dir = os.environ.get("TEMP", "/tmp")

        async with httpx.AsyncClient() as client:
            response = await client.get(enhanced_url)
            image_data = response.content

        try:
            import pillow_heif
            pillow_heif.register_heif_opener()
        except ImportError:
            pass

        img = Image.open(io.BytesIO(image_data)).convert("RGB")

        SIZES = {
            "instagram_feed":   (1080, 1080),
            "instagram_story":  (1080, 1920),
            "facebook_feed":    (1200, 628),
            "google_display":   (1200, 628),
        }

        results = {}
        for platform_key, (w, h) in SIZES.items():
            img_copy = img.copy()
            img_ratio = img_copy.width / img_copy.height
            target_ratio = w / h

            if img_ratio > target_ratio:
                new_width = int(img_copy.height * target_ratio)
                left = (img_copy.width - new_width) // 2
                img_copy = img_copy.crop((left, 0, left + new_width, img_copy.height))
            else:
                new_height = int(img_copy.width / target_ratio)
                top = (img_copy.height - new_height) // 2
                img_copy = img_copy.crop((0, top, img_copy.width, top + new_height))

            img_copy = img_copy.resize((w, h), Image.LANCZOS)

            temp_path = os.path.join(temp_dir, f"marlo_{platform_key}_{uuid.uuid4().hex}.jpg")
            img_copy.save(temp_path, "JPEG", quality=90)
            upload_url = await self.upload_image(temp_path)

            instructions = f"""For {platform_key.replace('_', ' ')}.
{'Include relevant hashtags.' if 'instagram' in platform_key else 'No hashtags — keep it short and punchy.'}
{f'Context from user: {caption_hint}' if caption_hint else ''}
Max 150 chars for ads, 300 for organic posts."""

            caption = await brain.generate_content(
                f"{platform_key.replace('_', ' ')} caption for a product photo",
                business, {}, instructions
            )

            results[platform_key] = {"url": upload_url.get("url", ""), "caption": caption.strip()}

            try:
                os.remove(temp_path)
            except Exception:
                pass

        return results

image_gen = ImageGenerator()
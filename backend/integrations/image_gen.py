import fal_client
import os
import io
import uuid
import httpx
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
                "image_size": size,
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

    async def generate_lifestyle_from_product(
        self,
        product_image_url: str,
        business: dict,
        caption: str = "",
        platform: str = "instagram_feed",
        vendor_type: str = None,
    ) -> dict:
        """
        Takes a user's product photo and generates a commercial lifestyle image.
        Uses vendor profile to craft the right scene.
        """
        from agent.brain import brain
        from agent.vendor_profiles import get_vendor_profile, detect_vendor_type_from_industry

        size = PLATFORM_SIZES.get(platform, {"width": 1024, "height": 1024})

        if not vendor_type:
            vendor_type = detect_vendor_type_from_industry(business.get("industry", ""))
        profile = get_vendor_profile(vendor_type)

        print(f"[ImageGen] Vendor type: {vendor_type} ({profile.display_name})")

        scene_rules = profile.lifestyle_scene_rules
        image_style = profile.image_style

        analysis_prompt = f"""You are a commercial photography art director for {profile.display_name} brands.

Business: "{business.get('name', '')}"
Brand tone: {business.get('tone_of_voice', image_style.mood)}
Caption context: {caption[:200] if caption else "general product showcase"}

VISUAL STYLE:
- Mood: {image_style.mood}
- Color palette: {image_style.color_palette}
- Lighting: {image_style.lighting}
- Best backgrounds: {', '.join(image_style.backgrounds[:3])}
- Avoid: {image_style.avoid}

SCENE OPTIONS (pick the best one):
{chr(10).join(f'{i+1}. {scene}' for i, scene in enumerate(scene_rules.scene_types[:3]))}

MODEL GUIDANCE: {scene_rules.model_guidance}
PROPS: {', '.join(scene_rules.props[:5])}
COMPOSITION: {scene_rules.composition}

Write a detailed image generation prompt for the best scene.
Product must be clearly visible and the hero.
No text, no watermarks. Max 120 words. Return ONLY the prompt."""

        try:
            scene_prompt = await brain.generate_content(
                content_type="photography prompt",
                business=business,
                context={},
                instructions=analysis_prompt
            )
            scene_prompt = scene_prompt.strip().strip('"')
        except Exception as e:
            print(f"[ImageGen] Prompt generation error: {e}")
            scene_prompt = (
                f"{image_style.mood} product photography. "
                f"{image_style.lighting}. "
                f"Background: {image_style.backgrounds[0]}. "
                f"Color palette: {image_style.color_palette}."
            )

        platform_note = scene_rules.platform_notes.get(platform, "")
        full_prompt = (
            f"{scene_prompt}. Product photo reference — maintain product accuracy. "
            f"{platform_note} Photorealistic, no text."
        ).strip()

        print(f"[ImageGen] Prompt: {full_prompt[:100]}...")

        try:
            result = await fal_client.run_async(
                "fal-ai/flux-pro/v1.1-ultra",
                arguments={
                    "prompt": full_prompt,
                    "image_url": product_image_url,
                    "strength": 0.78,
                    "image_size": size,
                    "num_inference_steps": 28,
                    "guidance_scale": 3.5,
                    "num_images": 1,
                    "safety_tolerance": "2",
                    "output_format": "jpeg",
                }
            )
            generated_url = result["images"][0]["url"]
            print(f"[ImageGen] Generated: {generated_url[:60]}...")
            return {
                "url": generated_url,
                "width": size["width"],
                "height": size["height"],
                "platform": platform,
                "prompt": full_prompt,
                "vendor_type": vendor_type,
                "source": "lifestyle_from_product",
            }
        except Exception as e:
            print(f"[ImageGen] fal.ai error: {e}")
            try:
                fallback = await self.generate(subject=scene_prompt, business=business, platform=platform)
                fallback["source"] = "lifestyle_fallback"
                return fallback
            except Exception as e2:
                print(f"[ImageGen] Fallback failed: {e2}")
                return {"url": None, "error": str(e), "vendor_type": vendor_type}

    async def generate_campaign_set(self, business: dict, offer: str) -> list:
        import asyncio
        tasks = [
            self.generate(offer, business, "instagram_feed"),
            self.generate(offer, business, "instagram_story"),
            self.generate(offer, business, "google_display"),
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [r for r in results if not isinstance(r, Exception)]

    async def upload_image(self, file_path: str) -> dict:
        result = await fal_client.upload_file_async(file_path)
        return {"url": result}

    async def upload_image_from_bytes(self, image_bytes: bytes, filename: str = "product.jpg") -> str:
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            tmp.write(image_bytes)
            tmp_path = tmp.name
        try:
            result = await fal_client.upload_file_async(tmp_path)
            return result
        finally:
            try:
                os.remove(tmp_path)
            except Exception:
                pass

    async def enhance_photo(self, image_url: str) -> str:
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
{'Include relevant hashtags.' if 'instagram' in platform_key else 'No hashtags.'}
{f'Context: {caption_hint}' if caption_hint else ''}"""
            caption = await brain.generate_content(
                f"{platform_key.replace('_', ' ')} caption", business, {}, instructions
            )
            results[platform_key] = {"url": upload_url.get("url", ""), "caption": caption.strip()}
            try:
                os.remove(temp_path)
            except Exception:
                pass

        return results


image_gen = ImageGenerator()
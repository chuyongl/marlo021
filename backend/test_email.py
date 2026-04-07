# backend\test_email.py
import asyncio, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dotenv import load_dotenv
load_dotenv(dotenv_path="../.env")
from email_system.sender import email_sender
from email_system.templates import onboarding_email_1

async def test():
    html = onboarding_email_1("Mia's Bakery", "Mia", "test-business-id", "http://localhost:8000")
    result = await email_sender.send(
        to_email="1818liu@gmail.com",  # Use your own email to test
        subject="Test: Marlo Onboarding Step 1",
        html_body=html,
        email_type="test",
        business_id=None,
        db=None
    )
    print("Result:", result)

asyncio.run(test())
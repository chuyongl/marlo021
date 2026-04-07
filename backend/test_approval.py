import asyncio, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dotenv import load_dotenv
load_dotenv(dotenv_path="../.env")

from database.session import AsyncSessionLocal
from database.models import AgentAction, Business, User
from auth.utils import generate_secure_token, hash_password
from datetime import datetime, timedelta
import uuid

async def create_test():
    async with AsyncSessionLocal() as db:
        # Create a test user first
        user_id = uuid.uuid4()
        user = User(
            id=user_id,
            email=f"test-approval-{uuid.uuid4()}@example.com",
            hashed_password=hash_password("test123"),
            full_name="Test User",
            is_active=True
        )
        db.add(user)
        await db.flush()

        # Create a test business
        business_id = uuid.uuid4()
        business = Business(
            id=business_id,
            owner_id=user_id,
            name="Test Bakery",
            industry="Food & Beverage",
            monthly_ad_budget=300
        )
        db.add(business)
        await db.flush()

        # Create the pending action
        approval_token = generate_secure_token()
        decline_token = generate_secure_token()
        action = AgentAction(
            id=uuid.uuid4(),
            business_id=business_id,
            action_type='bid_change',
            status='pending_approval',
            input_context={},
            action_parameters={'platform': 'google_ads'},
            agent_reasoning='Test approval',
            requires_approval=True,
            approval_token=approval_token,
            decline_token=decline_token,
            token_expires_at=datetime.utcnow() + timedelta(hours=48),
            created_at=datetime.utcnow()
        )
        db.add(action)
        await db.commit()
        print(f"Approve URL: http://localhost:8000/actions/approve?token={approval_token}")
        print(f"Decline URL: http://localhost:8000/actions/decline?token={decline_token}")

asyncio.run(create_test())
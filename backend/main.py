from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

load_dotenv(dotenv_path="../.env")

app = FastAPI(title="Marlo API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "http://localhost:3000")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "0.1.0"}

from auth.router import router as auth_router
app.include_router(auth_router)

from businesses.router import router as businesses_router
from integrations.oauth import router as oauth_router
app.include_router(businesses_router)
app.include_router(oauth_router)

from agent.approval_router import router as approval_router
app.include_router(approval_router)

from email_system.inbound import router as inbound_router
app.include_router(inbound_router)
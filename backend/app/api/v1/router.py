"""Central v1 router — mounts all endpoint sub-routers."""
from fastapi import APIRouter

from app.api.v1.endpoints import admin, auth, faqs, kb, tickets, users

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(tickets.router)
api_router.include_router(users.router)
api_router.include_router(faqs.router)
api_router.include_router(kb.router)
api_router.include_router(admin.router)

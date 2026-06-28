from fastapi import APIRouter, Depends

from app.api.deps import verify_api_key
from app.api.v1.endpoints import health, memories, projects, tasks

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(projects.router, dependencies=[Depends(verify_api_key)])
api_router.include_router(tasks.router, dependencies=[Depends(verify_api_key)])
api_router.include_router(memories.router, dependencies=[Depends(verify_api_key)])

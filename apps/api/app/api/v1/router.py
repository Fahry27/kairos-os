from fastapi import APIRouter, Depends
from app.api.deps import verify_api_key
from app.api.v1.endpoints import health, memories, plugins, commands, connectors, projects, tasks

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(projects.router, dependencies=[Depends(verify_api_key)])
api_router.include_router(tasks.router, dependencies=[Depends(verify_api_key)])
api_router.include_router(memories.router, dependencies=[Depends(verify_api_key)])
api_router.include_router(plugins.router, prefix="/plugins")
api_router.include_router(commands.router, prefix="/commands")
api_router.include_router(connectors.router, prefix="/connectors")

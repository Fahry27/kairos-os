from fastapi import APIRouter, Depends
from app.api.deps import verify_api_key
from app.api.v1.endpoints import (
    ai,
    approvals,
    commands,
    connectors,
    decision_plans,
    health,
    memories,
    plugins,
    projects,
    tasks,
    workflow_runs,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(projects.router, dependencies=[Depends(verify_api_key)])
api_router.include_router(tasks.router, dependencies=[Depends(verify_api_key)])
api_router.include_router(memories.router, dependencies=[Depends(verify_api_key)])
api_router.include_router(decision_plans.router, dependencies=[Depends(verify_api_key)])
api_router.include_router(plugins.router, prefix="/plugins")
api_router.include_router(commands.router, prefix="/commands")
api_router.include_router(connectors.router, prefix="/connectors")
api_router.include_router(ai.router, prefix="/ai")
api_router.include_router(approvals.router)
api_router.include_router(workflow_runs.router)

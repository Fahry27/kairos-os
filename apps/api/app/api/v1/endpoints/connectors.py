from fastapi import APIRouter, Depends, HTTPException, Query
from app.core.config import get_settings
from app.core.connectors import connector_registry, ConnectorManifest
from app.api.deps import verify_api_key

router = APIRouter()


@router.get("", response_model=list[ConnectorManifest])
def list_connectors(
    include_disabled: bool = Query(default=False),
    settings=Depends(get_settings),
    _=Depends(verify_api_key),
):
    if not settings.kairos_connectors_enabled:
        return []
    return connector_registry.get_all_connectors(include_disabled=include_disabled)


@router.get("/{connector_id}", response_model=ConnectorManifest)
def get_connector(
    connector_id: str,
    settings=Depends(get_settings),
    _=Depends(verify_api_key),
):
    if not settings.kairos_connectors_enabled:
        raise HTTPException(
            status_code=404,
            detail="Connectors are disabled by system configuration",
        )
    connector = connector_registry.get_connector(connector_id)
    if not connector:
        raise HTTPException(
            status_code=404, detail=f"Connector '{connector_id}' not found"
        )
    return connector

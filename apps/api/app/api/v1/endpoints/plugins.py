from fastapi import APIRouter, Depends, HTTPException, Query
from app.core.config import get_settings
from app.core.plugins import plugin_registry, PluginManifest
from app.api.deps import verify_api_key

router = APIRouter()


@router.get("", response_model=list[PluginManifest])
def list_plugins(
    include_disabled: bool = Query(default=False),
    settings=Depends(get_settings),
    _=Depends(verify_api_key),
):
    if not settings.kairos_plugins_enabled:
        return []
    return plugin_registry.get_all_plugins(include_disabled=include_disabled)


@router.get("/{plugin_id}", response_model=PluginManifest)
def get_plugin(
    plugin_id: str,
    settings=Depends(get_settings),
    _=Depends(verify_api_key),
):
    if not settings.kairos_plugins_enabled:
        raise HTTPException(
            status_code=404, detail="Plugins are disabled by system configuration"
        )
    plugin = plugin_registry.get_plugin(plugin_id)
    if not plugin:
        raise HTTPException(
            status_code=404, detail=f"Plugin '{plugin_id}' not found"
        )
    return plugin

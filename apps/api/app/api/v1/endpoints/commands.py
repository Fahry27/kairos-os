from fastapi import APIRouter, Depends, HTTPException, Query
from app.core.config import get_settings
from app.core.plugins import plugin_registry, CommandManifest
from app.api.deps import verify_api_key

router = APIRouter()


@router.get("", response_model=list[CommandManifest])
def list_commands(
    include_disabled: bool = Query(default=False),
    settings=Depends(get_settings),
    _=Depends(verify_api_key),
):
    if not settings.kairos_plugins_enabled:
        return []

    all_commands = []
    # Collect commands across all registered plugins
    for plugin in plugin_registry.get_all_plugins(
        include_disabled=include_disabled
    ):
        for cmd in plugin.commands:
            if include_disabled or cmd.enabled:
                all_commands.append(cmd)
    return all_commands


@router.get("/{command_id}", response_model=CommandManifest)
def get_command(
    command_id: str,
    settings=Depends(get_settings),
    _=Depends(verify_api_key),
):
    if not settings.kairos_plugins_enabled:
        raise HTTPException(
            status_code=404, detail="Plugins are disabled by system configuration"
        )

    # Search commands
    for plugin in plugin_registry.get_all_plugins(include_disabled=True):
        for cmd in plugin.commands:
            if cmd.id == command_id:
                return cmd

    raise HTTPException(
        status_code=404, detail=f"Command '{command_id}' not found"
    )

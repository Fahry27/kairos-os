import json
import logging
import shutil
import subprocess
import tempfile
import os
import time
from typing import Any

from pydantic import BaseModel

from app.core.ai_runtime import (
    AIOllamaDispatchRequest,
    AIOllamaDispatchResponse,
    AIPromptDryRunRequest,
    AIProviderReadiness,
    AIParsedPlan,
    ai_runtime,
)

logger = logging.getLogger(__name__)

class CodexCliRuntime:
    """
    Production-ready Codex Runtime Provider.
    Detects codex installation, checks auth, and dispatches prompts using `codex exec`.
    """

    def __init__(self):
        self.executable_path = shutil.which("codex")

    def check_readiness(self) -> AIProviderReadiness:
        """
        Check if Codex is installed and authenticated.
        """
        if not self.executable_path:
            return AIProviderReadiness(
                provider_id="ai.codex",
                checked=True,
                reachable=False,
                message="Codex CLI is not installed or not in PATH.",
                error_type="not_installed",
            )
            
        start_time = time.time()
        try:
            # Run codex doctor --json
            result = subprocess.run(
                [self.executable_path, "doctor", "--json"],
                capture_output=True,
                text=True,
                check=True,
            )
            data = json.loads(result.stdout)
            
            auth_state = data.get("checks", {}).get("auth.credentials", {})
            if auth_state.get("status") == "ok":
                latency = int((time.time() - start_time) * 1000)
                return AIProviderReadiness(
                    provider_id="ai.codex",
                    checked=True,
                    reachable=True,
                    latency_ms=latency,
                    message=f"Codex is authenticated. Mode: {auth_state.get('details', {}).get('auth mode', 'unknown')}",
                )
            else:
                return AIProviderReadiness(
                    provider_id="ai.codex",
                    checked=True,
                    reachable=False,
                    message="Codex is installed but not authenticated.",
                    error_type="auth_error",
                )
        except Exception as e:
            latency = int((time.time() - start_time) * 1000)
            return AIProviderReadiness(
                provider_id="ai.codex",
                checked=True,
                reachable=False,
                latency_ms=latency,
                message=f"Failed to check Codex readiness: {e}",
                error_type="doctor_error",
            )

    def dispatch(
        self,
        request: AIOllamaDispatchRequest,
        settings: Any,
        plugin_registry: Any,
        connector_registry: Any
    ) -> AIOllamaDispatchResponse:
        """
        Builds the prompt and dispatches it via `codex exec`.
        """
        if not self.executable_path:
            raise RuntimeError("Codex CLI is not installed.")

        start_time = time.time()
        
        # 1. Generate the dry-run prompt package using the existing ai_runtime logic
        dry_req = AIPromptDryRunRequest(
            user_goal=request.user_goal,
            context=request.context,
            preferred_model=request.model,
            include_commands=request.include_commands,
            include_plugins=request.include_plugins,
            include_connectors=request.include_connectors,
        )
        pkg = ai_runtime.generate_prompt_dry_run(dry_req, settings, plugin_registry, connector_registry)
        
        # 2. Build the Markdown string prompt
        prompt_lines = []
        
        if pkg.system_instructions:
            prompt_lines.append("# System Instructions")
            for inst in pkg.system_instructions:
                prompt_lines.append(f"- {inst}")
            prompt_lines.append("")
            
        if pkg.safety_policy:
            prompt_lines.append("# Safety Policy")
            for policy in pkg.safety_policy:
                prompt_lines.append(f"- {policy}")
            prompt_lines.append("")
            
        if pkg.context:
            prompt_lines.append("# Context")
            for key, val in pkg.context.items():
                prompt_lines.append(f"## {key}")
                if isinstance(val, (dict, list)):
                    prompt_lines.append(json.dumps(val, indent=2))
                else:
                    prompt_lines.append(str(val))
            prompt_lines.append("")
            
        prompt_lines.append("# Goal")
        prompt_lines.append(pkg.user_goal)
        prompt_lines.append("")
        
        prompt_text = "\n".join(prompt_lines)
        
        # 3. Send to Codex CLI
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                schema_path = os.path.join(temp_dir, "planner_schema.json")
                result_path = os.path.join(temp_dir, "result.json")
                
                # Write the schema
                with open(schema_path, "w") as f:
                    json.dump(AIParsedPlan.model_json_schema(), f)
                
                cmd = [
                    self.executable_path, "exec",
                    "--output-schema", schema_path,
                    "--output-last-message", result_path,
                    prompt_text
                ]
                
                proc = subprocess.run(
                    cmd,
                    stdin=subprocess.DEVNULL,
                    capture_output=True,
                    text=True
                )
                
                raw_output = proc.stdout + proc.stderr
                
                if proc.returncode != 0:
                    logger.error(f"codex exec failed with code {proc.returncode}: {proc.stderr}")
                    if not os.path.exists(result_path):
                        raise RuntimeError(f"Codex execution failed: {proc.stderr}")
                
                if os.path.exists(result_path):
                    with open(result_path, "r") as f:
                        clean_response = f.read()
                else:
                    clean_response = ""
                    logger.warning("No result.json was produced by Codex.")
                    
        except Exception as e:
            raise RuntimeError(f"Failed to execute codex: {e}")

        latency = int((time.time() - start_time) * 1000)
        
        return AIOllamaDispatchResponse(
            provider_id="ai.codex",
            model="codex-default",
            prompt_sent=True,
            response_text=clean_response,
            raw_response_metadata={"raw": "".join(raw_output)},
            safety_notes=pkg.safety_policy,
            latency_ms=latency,
            truncated=False,
        )

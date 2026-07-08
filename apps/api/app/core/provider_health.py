import datetime
import json
import time
import urllib.request
import urllib.error
import threading
from urllib.parse import urljoin
from typing import Any, Optional
from pydantic import BaseModel, Field


class ProviderHealth(BaseModel):
    provider_id: str
    status: str = "unknown"  # "healthy", "unhealthy", "unknown"
    reachable: bool = False
    latency_ms: Optional[float] = None
    last_successful_check: Optional[datetime.datetime] = None
    last_failed_check: Optional[datetime.datetime] = None
    error_message: Optional[str] = None


class HealthCache:
    def __init__(self) -> None:
        self._cache: dict[str, ProviderHealth] = {}

    def get(self, provider_id: str) -> Optional[ProviderHealth]:
        return self._cache.get(provider_id)

    def set(self, provider_id: str, health: ProviderHealth) -> None:
        self._cache[provider_id] = health

    def clear(self) -> None:
        self._cache.clear()


health_cache = HealthCache()


class HealthMonitor:
    def __init__(self, settings) -> None:
        self.settings = settings
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def check_health(self, provider_id: str) -> ProviderHealth:
        prev = health_cache.get(provider_id)
        last_success = prev.last_successful_check if prev else None
        last_failed = prev.last_failed_check if prev else None

        start_time = time.time()
        reachable = False
        status = "unhealthy"
        error_msg = None

        try:
            if provider_id == "ai.ollama":
                base_url = self.settings.kairos_ollama_base_url
                tags_path = self.settings.kairos_ollama_tags_path
                url = urljoin(base_url, tags_path)
                req = urllib.request.Request(url, method="GET")
                with urllib.request.urlopen(req, timeout=self.settings.kairos_ollama_timeout_seconds) as resp:
                    if resp.status == 200:
                        reachable = True
                        status = "healthy"
                    else:
                        error_msg = f"HTTP {resp.status}"
            elif provider_id in ("ai.openai", "ai.gemini", "ai.claude", "ai.openrouter"):
                if not self.settings.kairos_cloud_provider_health_enabled:
                    reachable = False
                    status = "unhealthy"
                    error_msg = (
                        "Cloud provider health checks are disabled. "
                        "Set KAIROS_CLOUD_PROVIDER_HEALTH_ENABLED=true to enable."
                    )
                elif provider_id == "ai.openai":
                    import os
                    api_key = os.environ.get("OPENAI_API_KEY")
                    if not api_key:
                        error_msg = "Missing credentials"
                    else:
                        url = "https://api.openai.com/v1/models"
                        req = urllib.request.Request(url, method="GET")
                        req.add_header("Authorization", f"Bearer {api_key}")
                        with urllib.request.urlopen(req, timeout=5) as resp:
                            if resp.status == 200:
                                reachable = True
                                status = "healthy"
                            else:
                                error_msg = f"HTTP {resp.status}"
                elif provider_id == "ai.openrouter":
                    import os
                    api_key = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("KAIROS_OPENROUTER_API_KEY")
                    if not api_key:
                        error_msg = "Missing credentials"
                    else:
                        url = "https://openrouter.ai/api/v1/models"
                        req = urllib.request.Request(url, method="GET")
                        req.add_header("Authorization", f"Bearer {api_key}")
                        with urllib.request.urlopen(req, timeout=5) as resp:
                            if resp.status == 200:
                                reachable = True
                                status = "healthy"
                            else:
                                error_msg = f"HTTP {resp.status}"
                elif provider_id == "ai.gemini":
                    import os
                    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("KAIROS_GEMINI_API_KEY")
                    if not api_key:
                        error_msg = "Missing credentials"
                    else:
                        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
                        req = urllib.request.Request(url, method="GET")
                        with urllib.request.urlopen(req, timeout=5) as resp:
                            if resp.status == 200:
                                reachable = True
                                status = "healthy"
                            else:
                                error_msg = f"HTTP {resp.status}"
                else:
                    error_msg = "Cloud provider health not implemented"
            else:
                error_msg = "Unsupported provider"
        except urllib.error.URLError as e:
            error_msg = str(e.reason) if hasattr(e, "reason") else str(e)
        except Exception as e:
            error_msg = str(e)

        latency = (time.time() - start_time) * 1000

        now = datetime.datetime.utcnow()
        if reachable:
            last_success = now
        else:
            last_failed = now

        health = ProviderHealth(
            provider_id=provider_id,
            status=status,
            reachable=reachable,
            latency_ms=latency,
            last_successful_check=last_success,
            last_failed_check=last_failed,
            error_message=error_msg
        )
        health_cache.set(provider_id, health)
        return health

    def poll_all(self) -> dict[str, ProviderHealth]:
        results = {}
        for provider_id in ["ai.ollama", "ai.openai", "ai.gemini", "ai.openrouter"]:
            results[provider_id] = self.check_health(provider_id)
        return results

    def start_polling(self, interval_seconds: int = 60) -> None:
        if self._running:
            return
        self._running = True
        def _loop():
            while self._running:
                try:
                    self.poll_all()
                except Exception:
                    pass
                time.sleep(interval_seconds)
        self._thread = threading.Thread(target=_loop, daemon=True)
        self._thread.start()

    def stop_polling(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=1)
            self._thread = None

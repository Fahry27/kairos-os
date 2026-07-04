import datetime
import time
from unittest.mock import MagicMock, patch
import urllib.error
import pytest
from app.core.provider_health import (
    ProviderHealth,
    HealthCache,
    health_cache,
    HealthMonitor
)


def test_provider_health_model():
    h = ProviderHealth(
        provider_id="ai.test",
        status="healthy",
        reachable=True,
        latency_ms=12.5,
        last_successful_check=datetime.datetime.utcnow()
    )
    assert h.provider_id == "ai.test"
    assert h.status == "healthy"
    assert h.reachable is True
    assert h.latency_ms == 12.5
    assert h.last_successful_check is not None


def test_health_cache():
    cache = HealthCache()
    h = ProviderHealth(provider_id="ai.ollama", status="healthy", reachable=True)
    cache.set("ai.ollama", h)
    
    assert cache.get("ai.ollama") == h
    assert cache.get("ai.openai") is None
    cache.clear()
    assert cache.get("ai.ollama") is None


@patch("urllib.request.urlopen")
def test_health_monitor_ollama_success(mock_urlopen):
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_urlopen.return_value.__enter__.return_value = mock_resp

    settings = MagicMock()
    settings.kairos_ollama_base_url = "http://localhost:11434"
    settings.kairos_ollama_tags_path = "/api/tags"
    settings.kairos_ollama_timeout_seconds = 2

    monitor = HealthMonitor(settings)
    health = monitor.check_health("ai.ollama")

    assert health.reachable is True
    assert health.status == "healthy"
    assert health.last_successful_check is not None
    assert health.last_failed_check is None


@patch("urllib.request.urlopen")
def test_health_monitor_ollama_failure(mock_urlopen):
    health_cache.clear()
    mock_urlopen.side_effect = urllib.error.URLError("Refused")

    settings = MagicMock()
    settings.kairos_ollama_base_url = "http://localhost:11434"
    settings.kairos_ollama_tags_path = "/api/tags"
    settings.kairos_ollama_timeout_seconds = 2

    monitor = HealthMonitor(settings)
    health = monitor.check_health("ai.ollama")

    assert health.reachable is False
    assert health.status == "unhealthy"
    assert health.last_successful_check is None
    assert health.last_failed_check is not None
    assert "Refused" in health.error_message


@patch("urllib.request.urlopen")
def test_health_monitor_openai_success(mock_urlopen, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_urlopen.return_value.__enter__.return_value = mock_resp

    settings = MagicMock()
    monitor = HealthMonitor(settings)
    health = monitor.check_health("ai.openai")

    assert health.reachable is True
    assert health.status == "healthy"


def test_health_monitor_openai_no_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    settings = MagicMock()
    monitor = HealthMonitor(settings)
    health = monitor.check_health("ai.openai")

    assert health.reachable is False
    assert health.status == "unhealthy"
    assert "Missing credentials" in health.error_message


def test_background_polling():
    settings = MagicMock()
    settings.kairos_ollama_base_url = "http://localhost:11434"
    settings.kairos_ollama_tags_path = "/api/tags"
    settings.kairos_ollama_timeout_seconds = 2

    monitor = HealthMonitor(settings)
    
    # Mock check_health to avoid actual request
    monitor.check_health = MagicMock(return_value=ProviderHealth(provider_id="ai.test"))

    monitor.start_polling(interval_seconds=1)
    assert monitor._running is True
    
    # Let it run briefly
    time.sleep(0.5)
    
    monitor.stop_polling()
    assert monitor._running is False

import time
from typing import Optional
from pydantic import BaseModel, Field


class CircuitBreaker(BaseModel):
    provider_id: str
    failure_threshold: int = 3
    cooldown_seconds: int = 30
    
    failure_count: int = 0
    state: str = "closed"  # "closed", "open", "half-open"
    last_failure_time: Optional[float] = None

    def record_failure(self) -> None:
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = "open"

    def record_success(self) -> None:
        self.failure_count = 0
        self.state = "closed"
        self.last_failure_time = None

    def is_available(self) -> bool:
        if self.state == "closed":
            return True
        if self.state == "open":
            if time.time() - (self.last_failure_time or 0.0) > self.cooldown_seconds:
                self.state = "half-open"
                return True
            return False
        return True


class CircuitBreakerRegistry:
    def __init__(self) -> None:
        self._breakers: dict[str, CircuitBreaker] = {}

    def get(self, provider_id: str) -> CircuitBreaker:
        if provider_id not in self._breakers:
            self._breakers[provider_id] = CircuitBreaker(provider_id=provider_id)
        return self._breakers[provider_id]

    def clear(self) -> None:
        self._breakers.clear()


circuit_breakers = CircuitBreakerRegistry()


class RetryPolicy(BaseModel):
    max_retries: int = 3
    backoff_factor: float = 1.5
    backoff_max_seconds: float = 5.0


class FallbackPolicy(BaseModel):
    fallback_enabled: bool = True
    cooldown_period_seconds: int = 30

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class ServiceHealthResponse(BaseModel):
    id: int
    checked_at: datetime
    service_name: str
    status: str  # UP | DEGRADED | DOWN
    latency_ms: Optional[float] = None
    details: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ServiceHealthListResponse(BaseModel):
    items: List[ServiceHealthResponse]


class LatencyTrendHistoryPoint(BaseModel):
    ts: str  # ISO-8601 or formatted date/time string representing bucket start
    avg_latency_ms: Optional[float] = None


class ServiceMetrics(BaseModel):
    service_name: str
    uptime_pct: float
    error_rate_pct: float
    p95_latency_ms: Optional[float] = None
    p99_latency_ms: Optional[float] = None
    sample_count: int
    history: List[LatencyTrendHistoryPoint] = []


class MetricsResponse(BaseModel):
    items: List[ServiceMetrics]
    range: str

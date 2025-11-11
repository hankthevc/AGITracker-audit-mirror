"""
Dashboard data schemas for FiveThirtyEight-style homepage.

Pydantic schemas that mirror TypeScript types in apps/web/lib/types/dashboard.ts
for API contract consistency.
"""

from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field


MetricKey = Literal[
    'events_per_day',
    'swebench_score',
    'mmlu_score',
    'compute_flops',
    'safety_incidents_per_month',
    'signposts_completed'
]


class TimePoint(BaseModel):
    """Single point in a timeseries."""
    t: str = Field(..., description="ISO date string")
    v: float = Field(..., description="Numeric value")


class Timeseries(BaseModel):
    """Timeseries data for charts."""
    metric: MetricKey
    series: list[TimePoint]
    meta: Optional[dict[str, str | int | float | bool]] = None


class KpiCard(BaseModel):
    """Key performance indicator card data."""
    key: MetricKey
    label: str
    value: str | float
    deltaPct: Optional[float] = None
    trend: Optional[list[TimePoint]] = None


class NewsItem(BaseModel):
    """News item for feed."""
    id: str
    title: str
    source: str
    url: str = Field(..., description="Must be sanitized via SafeLink on frontend")
    published_at: str
    tags: list[str]
    summary: Optional[str] = None


class AnalysisSection(BaseModel):
    """AI-generated or templated analysis."""
    headline: str
    bullets: list[str]
    paragraphs: list[str]


class HomepageSnapshot(BaseModel):
    """Complete homepage data snapshot."""
    generated_at: str
    kpis: list[KpiCard]
    featured: list[Timeseries]
    news: list[NewsItem]
    analysis: AnalysisSection


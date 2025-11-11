"""
Pydantic schemas for validating LLM outputs (P1-4).

All LLM responses should be validated against these schemas
to ensure type safety and prevent hallucinations.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field, validator


class EventAnalysisOutput(BaseModel):
    """Schema for event analysis LLM output."""
    
    summary: str = Field(..., min_length=10, max_length=500, description="2-3 sentence summary")
    relevance_explanation: str = Field(..., min_length=10, max_length=1000, description="Why this matters for AGI")
    significance_score: float = Field(..., ge=0.0, le=1.0, description="Significance score (0-1)")
    impact_json: Dict[str, str] = Field(..., description="Impact timeline (short/medium/long)")
    confidence_reasoning: Optional[str] = Field(None, max_length=500, description="Confidence explanation")
    
    @validator("significance_score")
    def validate_score(cls, v):
        """Ensure score is in valid range."""
        if not (0.0 <= v <= 1.0):
            raise ValueError("Significance score must be between 0 and 1")
        return v
    
    @validator("impact_json")
    def validate_impact_structure(cls, v):
        """Ensure impact_json has required keys."""
        required_keys = ["short", "medium", "long"]
        for key in required_keys:
            if key not in v:
                raise ValueError(f"impact_json missing required key: {key}")
            if not isinstance(v[key], str) or len(v[key]) < 5:
                raise ValueError(f"impact_json[{key}] must be a non-empty string")
        return v


class EventMappingOutput(BaseModel):
    """Schema for event-to-signpost mapping LLM output."""
    
    signpost_code: str = Field(..., min_length=1, max_length=100)
    confidence: float = Field(..., ge=0.0, le=1.0)
    rationale: str = Field(..., min_length=10, max_length=1000)
    extracted_value: Optional[float] = Field(None, description="Extracted numeric value if applicable")
    
    @validator("confidence")
    def validate_confidence(cls, v):
        """Ensure confidence is in valid range."""
        if not (0.0 <= v <= 1.0):
            raise ValueError("Confidence must be between 0 and 1")
        return v


class WeeklyDigestOutput(BaseModel):
    """Schema for weekly digest LLM output."""
    
    headline: str = Field(..., min_length=10, max_length=200)
    key_developments: List[str] = Field(..., min_items=1, max_items=10)
    velocity_assessment: str = Field(..., min_length=50, max_length=500)
    surprise_factor: str = Field(..., min_length=50, max_length=500)
    outlook: str = Field(..., min_length=50, max_length=500)
    
    @validator("key_developments")
    def validate_developments(cls, v):
        """Ensure all developments are non-empty."""
        for dev in v:
            if not dev or len(dev) < 10:
                raise ValueError("Each development must be at least 10 characters")
        return v


class ChatResponse(BaseModel):
    """Schema for RAG chatbot response."""
    
    answer: str = Field(..., min_length=10, description="Generated answer")
    sources_used: List[int] = Field(default_factory=list, description="List of source indices used")
    confidence: Optional[str] = Field(None, description="Confidence level: high/medium/low")
    
    @validator("answer")
    def validate_answer(cls, v):
        """Ensure answer is meaningful."""
        if len(v.strip()) < 10:
            raise ValueError("Answer must be at least 10 characters")
        return v.strip()


class SurpriseScoreOutput(BaseModel):
    """Schema for surprise score calculation."""
    
    event_id: int = Field(..., gt=0)
    signpost_code: str = Field(..., min_length=1)
    surprise_score: float = Field(..., ge=0.0, le=10.0, description="Surprise score (0-10)")
    explanation: str = Field(..., min_length=20, max_length=500)
    
    @validator("surprise_score")
    def validate_score(cls, v):
        """Ensure score is in valid range."""
        if not (0.0 <= v <= 10.0):
            raise ValueError("Surprise score must be between 0 and 10")
        return v


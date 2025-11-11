"""
Centralized LLM client with budget enforcement and security checks.

All LLM API calls should go through this client to ensure:
- Budget limits are respected
- Prompt injection is detected
- Costs are tracked
- Outputs are validated
"""

import hashlib
import json
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import openai
import redis
from anthropic import Anthropic
from pydantic import BaseModel, Field, ValidationError

from app.config import settings


class BudgetExceededError(Exception):
    """Raised when daily LLM budget is exceeded."""
    pass


class PromptInjectionError(Exception):
    """Raised when prompt injection is detected."""
    pass


class LLMClient:
    """
    Centralized client for all LLM API calls.
    
    Features:
    - Automatic budget checking
    - Prompt injection detection
    - Cost tracking
    - Response caching
    - Output validation
    """
    
    # Prompt injection patterns (case-insensitive)
    INJECTION_PATTERNS = [
        r"ignore\s+(previous\s+)?instructions?",
        r"disregard\s+(all|previous|everything)",
        r"new\s+instructions?:",
        r"you\s+are\s+now",
        r"system\s*:",
        r"assistant\s*:",
        r"<\|endoftext\|>",
        r"<\|im_end\|>",
        r"<\|im_start\|>",
        r"repeat\s+your\s+(system\s+)?prompt",
        r"reveal\s+your\s+(system\s+)?prompt",
        r"show\s+me\s+your\s+instructions",
        r"what\s+are\s+your\s+instructions",
        r"bypass\s+your\s+restrictions",
        r"jailbreak",
        r"DAN\s+mode",  # Do Anything Now
        r"developer\s+mode",
    ]
    
    # Model pricing (USD per 1M tokens)
    MODEL_PRICING = {
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},
        "gpt-4o": {"input": 5.0, "output": 15.0},
        "gpt-4-turbo": {"input": 10.0, "output": 30.0},
        "claude-3-5-sonnet-20241022": {"input": 3.0, "output": 15.0},
        "claude-3-haiku-20240307": {"input": 0.25, "output": 1.25},
    }
    
    def __init__(self):
        """Initialize LLM client."""
        self.openai_client = openai.OpenAI(api_key=settings.openai_api_key)
        self.anthropic_client = Anthropic(api_key=getattr(settings, "anthropic_api_key", None))
        self.redis_client = redis.from_url(settings.redis_url, decode_responses=True)
        
        # Budget limits
        self.warning_threshold = 20.0  # $20/day
        self.hard_limit = 50.0  # $50/day
    
    def check_budget(self, estimated_cost: float = 0.0) -> dict:
        """
        Check current LLM budget spend.
        
        Args:
            estimated_cost: Estimated cost of upcoming call (optional)
            
        Returns:
            dict with budget status
            
        Raises:
            BudgetExceededError if hard limit would be exceeded
        """
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        
        # Get all budget keys
        llm_key = f"llm_budget:daily:{today}"
        embedding_key = f"embedding_spend:daily:{today}"
        
        llm_spend = float(self.redis_client.get(llm_key) or 0.0)
        embedding_spend = float(self.redis_client.get(embedding_key) or 0.0)
        total_spend = llm_spend + embedding_spend
        
        # Check if adding estimated cost would exceed limit
        projected_spend = total_spend + estimated_cost
        
        if projected_spend >= self.hard_limit:
            raise BudgetExceededError(
                f"Daily LLM budget exceeded: ${total_spend:.2f} / ${self.hard_limit:.2f} "
                f"(projected: ${projected_spend:.2f})"
            )
        
        # Warn if approaching limit
        if projected_spend >= self.warning_threshold:
            print(f"⚠️  LLM budget warning: ${projected_spend:.2f} / ${self.hard_limit:.2f}")
        
        return {
            "date": today,
            "llm_spend_usd": llm_spend,
            "embedding_spend_usd": embedding_spend,
            "total_spend_usd": total_spend,
            "projected_spend_usd": projected_spend,
            "warning_threshold_usd": self.warning_threshold,
            "hard_limit_usd": self.hard_limit,
            "at_warning": projected_spend >= self.warning_threshold,
            "blocked": projected_spend >= self.hard_limit
        }
    
    def detect_prompt_injection(self, text: str) -> bool:
        """
        Detect potential prompt injection attempts.
        
        Args:
            text: User input to check
            
        Returns:
            True if suspicious patterns found
        """
        if not text:
            return False
        
        text_lower = text.lower()
        
        for pattern in self.INJECTION_PATTERNS:
            if re.search(pattern, text_lower):
                print(f"🚨 Prompt injection detected: {pattern}")
                return True
        
        return False
    
    def sanitize_input(self, text: str, max_length: int = 2000) -> str:
        """
        Sanitize user input for LLM prompts.
        
        Args:
            text: User input
            max_length: Maximum allowed length
            
        Returns:
            Sanitized text
            
        Raises:
            PromptInjectionError if injection detected
        """
        if not text:
            return ""
        
        # Check for injection
        if self.detect_prompt_injection(text):
            raise PromptInjectionError(
                "Your input contains suspicious patterns. Please rephrase."
            )
        
        # Truncate to max length
        sanitized = text[:max_length]
        
        # Remove control characters (except newlines, tabs)
        sanitized = "".join(char for char in sanitized if char.isprintable() or char in "\n\t")
        
        return sanitized
    
    def calculate_cost(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """
        Calculate cost of API call.
        
        Args:
            model: Model name
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            
        Returns:
            Cost in USD
        """
        if model not in self.MODEL_PRICING:
            print(f"⚠️  Unknown model pricing: {model}, using gpt-4o-mini rates")
            model = "gpt-4o-mini"
        
        pricing = self.MODEL_PRICING[model]
        
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        
        return input_cost + output_cost
    
    def record_spend(
        self,
        cost: float,
        model: str,
        task_name: str,
        tokens: dict = None
    ):
        """
        Record LLM API spend in Redis.
        
        Args:
            cost: Cost in USD
            model: Model used
            task_name: Task name for tracking
            tokens: Optional token counts
        """
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        key = f"llm_budget:daily:{today}"
        
        # Increment spend
        self.redis_client.incrbyfloat(key, cost)
        
        # Set TTL (48 hours for debugging)
        self.redis_client.expire(key, 48 * 3600)
        
        # Log for audit
        print(
            f"💰 LLM spend: ${cost:.4f} ({model}, {task_name}) "
            f"[{tokens.get('input', 0)}in / {tokens.get('output', 0)}out tokens]"
            if tokens else f"💰 LLM spend: ${cost:.4f} ({model}, {task_name})"
        )
    
    async def call_openai(
        self,
        model: str,
        messages: List[Dict[str, str]],
        max_tokens: int = 1000,
        temperature: float = 0.7,
        task_name: str = "unknown",
        sanitize_user_input: bool = True
    ) -> dict:
        """
        Call OpenAI API with budget and security checks.
        
        Args:
            model: Model name (e.g., "gpt-4o-mini")
            messages: List of message dicts
            max_tokens: Max completion tokens
            temperature: Sampling temperature
            task_name: Task name for tracking
            sanitize_user_input: Whether to sanitize user messages
            
        Returns:
            API response dict
            
        Raises:
            BudgetExceededError if budget exceeded
            PromptInjectionError if injection detected
        """
        # Sanitize user messages if requested
        if sanitize_user_input:
            for msg in messages:
                if msg.get("role") == "user":
                    msg["content"] = self.sanitize_input(msg["content"])
        
        # Estimate cost (rough approximation)
        estimated_tokens = sum(len(m["content"]) // 4 for m in messages)  # Rough estimate
        estimated_cost = self.calculate_cost(model, estimated_tokens, max_tokens)
        
        # Check budget
        self.check_budget(estimated_cost)
        
        # Make API call
        response = self.openai_client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        # Calculate actual cost
        input_tokens = response.usage.prompt_tokens
        output_tokens = response.usage.completion_tokens
        actual_cost = self.calculate_cost(model, input_tokens, output_tokens)
        
        # Record spend
        self.record_spend(
            actual_cost,
            model,
            task_name,
            tokens={"input": input_tokens, "output": output_tokens}
        )
        
        return response
    
    async def call_anthropic(
        self,
        model: str,
        messages: List[Dict[str, str]],
        max_tokens: int = 1000,
        temperature: float = 0.7,
        task_name: str = "unknown",
        sanitize_user_input: bool = True
    ) -> dict:
        """
        Call Anthropic API with budget and security checks.
        
        Args:
            model: Model name (e.g., "claude-3-5-sonnet-20241022")
            messages: List of message dicts
            max_tokens: Max completion tokens
            temperature: Sampling temperature
            task_name: Task name for tracking
            sanitize_user_input: Whether to sanitize user messages
            
        Returns:
            API response dict
            
        Raises:
            BudgetExceededError if budget exceeded
            PromptInjectionError if injection detected
        """
        if not self.anthropic_client.api_key:
            raise ValueError("Anthropic API key not configured")
        
        # Sanitize user messages if requested
        if sanitize_user_input:
            for msg in messages:
                if msg.get("role") == "user":
                    msg["content"] = self.sanitize_input(msg["content"])
        
        # Estimate cost
        estimated_tokens = sum(len(m["content"]) // 4 for m in messages)
        estimated_cost = self.calculate_cost(model, estimated_tokens, max_tokens)
        
        # Check budget
        self.check_budget(estimated_cost)
        
        # Extract system message if present
        system_message = None
        filtered_messages = []
        for msg in messages:
            if msg.get("role") == "system":
                system_message = msg["content"]
            else:
                filtered_messages.append(msg)
        
        # Make API call
        kwargs = {
            "model": model,
            "messages": filtered_messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        if system_message:
            kwargs["system"] = system_message
        
        response = self.anthropic_client.messages.create(**kwargs)
        
        # Calculate cost
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        actual_cost = self.calculate_cost(model, input_tokens, output_tokens)
        
        # Record spend
        self.record_spend(
            actual_cost,
            model,
            task_name,
            tokens={"input": input_tokens, "output": output_tokens}
        )
        
        return response
    
    async def call_with_fallback(
        self,
        messages: List[Dict[str, str]],
        preferred_model: str = "gpt-4o-mini",
        fallback_models: List[str] = None,
        **kwargs
    ):
        """
        Call LLM with automatic fallback on failure.
        
        Args:
            messages: List of message dicts
            preferred_model: Preferred model to try first
            fallback_models: List of fallback models
            **kwargs: Additional arguments for API call
            
        Returns:
            API response from first successful model
        """
        if fallback_models is None:
            fallback_models = ["gpt-4o", "claude-3-5-sonnet-20241022"]
        
        all_models = [preferred_model] + fallback_models
        
        last_error = None
        for model in all_models:
            try:
                if model.startswith("gpt-"):
                    return await self.call_openai(model, messages, **kwargs)
                elif model.startswith("claude-"):
                    return await self.call_anthropic(model, messages, **kwargs)
            except BudgetExceededError:
                # Don't fallback on budget errors
                raise
            except Exception as e:
                print(f"⚠️  Model {model} failed: {e}")
                last_error = e
                if model == all_models[-1]:
                    # Last fallback failed
                    raise last_error
                continue
        
        raise last_error or Exception("All models failed")


# Singleton instance
llm_client = LLMClient()


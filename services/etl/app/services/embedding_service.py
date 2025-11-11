"""
Embedding service for generating and caching vector embeddings.

Uses OpenAI text-embedding-3-small for cost-effective semantic search.
Supports batch processing, Redis caching, and retry logic.
"""

import hashlib
import json
from typing import List, Optional
import time

import openai
import redis
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings


class EmbeddingService:
    """Service for generating and caching embeddings."""

    def __init__(self):
        """Initialize embedding service."""
        self.client = openai.OpenAI(api_key=settings.openai_api_key)
        self.redis_client = redis.from_url(settings.redis_url, decode_responses=True)
        
        # OpenAI text-embedding-3-small config
        self.model = "text-embedding-3-small"
        self.dimensions = 1536
        self.batch_size = 100  # OpenAI allows up to 2048, but we'll be conservative
        
        # Cost tracking
        self.cost_per_1k_tokens = 0.00002  # $0.00002 per 1K tokens for text-embedding-3-small
        
        # Cache TTL: 24 hours
        self.cache_ttl = 24 * 3600

    def _cache_key(self, text: str) -> str:
        """Generate cache key for text."""
        text_hash = hashlib.sha256(text.encode()).hexdigest()
        return f"embedding:v1:{self.model}:{text_hash}"

    def _get_cached(self, text: str) -> Optional[List[float]]:
        """Get cached embedding if available."""
        key = self._cache_key(text)
        cached = self.redis_client.get(key)
        
        if cached:
            return json.loads(cached)
        return None

    def _set_cache(self, text: str, embedding: List[float]):
        """Cache embedding with TTL."""
        key = self._cache_key(text)
        self.redis_client.setex(
            key,
            self.cache_ttl,
            json.dumps(embedding)
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def _api_call(self, texts: List[str]) -> dict:
        """Make API call with retry logic."""
        response = self.client.embeddings.create(
            model=self.model,
            input=texts,
            dimensions=self.dimensions
        )
        return response

    def embed_single(self, text: str, use_cache: bool = True) -> List[float]:
        """
        Generate embedding for single text.
        
        Args:
            text: Text to embed
            use_cache: Whether to use cache
            
        Returns:
            Embedding vector (list of floats)
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        # Check cache
        if use_cache:
            cached = self._get_cached(text)
            if cached:
                print(f"✅ Cache hit for text (length={len(text)})")
                return cached
        
        # Generate embedding
        try:
            response = self._api_call([text])
            embedding = response.data[0].embedding
            
            # Track cost
            tokens = response.usage.total_tokens
            cost = (tokens / 1000) * self.cost_per_1k_tokens
            self._record_spend(cost)
            
            print(f"💰 Embedding cost: ${cost:.6f} ({tokens} tokens)")
            
            # Cache result
            if use_cache:
                self._set_cache(text, embedding)
            
            return embedding
            
        except Exception as e:
            print(f"❌ Embedding API error: {e}")
            raise

    def embed_batch(
        self,
        texts: List[str],
        use_cache: bool = True,
        show_progress: bool = True
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts efficiently.
        
        Args:
            texts: List of texts to embed
            use_cache: Whether to use cache
            show_progress: Whether to print progress
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        embeddings = [None] * len(texts)
        uncached_indices = []
        uncached_texts = []
        
        # Check cache for all texts
        if use_cache:
            for i, text in enumerate(texts):
                if not text or not text.strip():
                    continue
                    
                cached = self._get_cached(text)
                if cached:
                    embeddings[i] = cached
                else:
                    uncached_indices.append(i)
                    uncached_texts.append(text)
        else:
            uncached_indices = list(range(len(texts)))
            uncached_texts = texts
        
        if show_progress:
            print(f"📊 Batch embedding: {len(texts)} total, {len(uncached_texts)} uncached")
        
        # Process uncached texts in batches
        total_cost = 0.0
        
        for batch_start in range(0, len(uncached_texts), self.batch_size):
            batch_end = min(batch_start + self.batch_size, len(uncached_texts))
            batch_texts = uncached_texts[batch_start:batch_end]
            
            if show_progress:
                print(f"  Processing batch {batch_start // self.batch_size + 1}/{(len(uncached_texts) + self.batch_size - 1) // self.batch_size}...")
            
            try:
                # API call
                response = self._api_call(batch_texts)
                
                # Track cost
                tokens = response.usage.total_tokens
                cost = (tokens / 1000) * self.cost_per_1k_tokens
                total_cost += cost
                self._record_spend(cost)
                
                # Store results
                for i, embedding_obj in enumerate(response.data):
                    original_index = uncached_indices[batch_start + i]
                    embedding = embedding_obj.embedding
                    embeddings[original_index] = embedding
                    
                    # Cache
                    if use_cache:
                        self._set_cache(batch_texts[i], embedding)
                
                # Rate limiting (be nice to API)
                if batch_end < len(uncached_texts):
                    time.sleep(0.5)
                    
            except Exception as e:
                print(f"❌ Batch embedding error at batch {batch_start}: {e}")
                raise
        
        if show_progress and uncached_texts:
            print(f"💰 Total embedding cost: ${total_cost:.6f}")
        
        return embeddings

    def _record_spend(self, cost_usd: float):
        """Record embedding spend in Redis."""
        from datetime import datetime, timezone
        
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        key = f"embedding_spend:daily:{today}"
        
        # Increment spend
        self.redis_client.incrbyfloat(key, cost_usd)
        
        # Set TTL (48 hours for debugging)
        self.redis_client.expire(key, 48 * 3600)

    def get_daily_spend(self) -> float:
        """Get total embedding spend for today."""
        from datetime import datetime, timezone
        
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        key = f"embedding_spend:daily:{today}"
        
        spend = self.redis_client.get(key)
        return float(spend) if spend else 0.0


# Singleton instance
embedding_service = EmbeddingService()


"""
RAG (Retrieval-Augmented Generation) chatbot service.

Provides conversational AI that answers questions about AGI progress
with citations from the event and signpost database.
"""

import hashlib
import json
from typing import AsyncIterator, Dict, List, Optional

import redis
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferWindowMemory
from langchain.prompts import PromptTemplate
from langchain_community.vectorstores.pgvector import PGVector
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from sqlalchemy import select, text

from app.config import settings
from app.database import SessionLocal
from app.models import Event, Signpost


class RAGChatbot:
    """RAG chatbot for AGI progress questions."""

    def __init__(self):
        """Initialize RAG chatbot."""
        self.redis_client = redis.from_url(settings.redis_url, decode_responses=True)
        
        # LLM configuration
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.7,
            streaming=True,
            openai_api_key=settings.openai_api_key
        )
        
        # Embeddings (must match embedding_service)
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            dimensions=1536,
            openai_api_key=settings.openai_api_key
        )
        
        # Conversation memory (last 5 messages)
        self.memory_window = 5
        
        # System prompt
        self.system_prompt = """You are an AI assistant specialized in AGI (Artificial General Intelligence) progress tracking.

You have access to a database of:
- Events: Recent AI news, papers, and announcements (A/B/C/D tier evidence)
- Signposts: Measurable milestones toward AGI across capabilities, agents, inputs, and security

When answering questions:
1. ONLY use information from the retrieved context
2. ALWAYS cite sources (event titles or signpost codes)
3. Distinguish between A/B tier (moves gauges) and C/D tier (for context only)
4. Be precise about dates and metrics
5. If the question is out of scope (not about AGI/AI progress), politely decline

Out of scope examples:
- Weather, sports, entertainment
- General knowledge questions unrelated to AI
- Personal advice
- Code debugging (unless about AI systems)

Format your responses in Markdown with:
- **Bold** for key terms
- Citations as [Source Title](url) when available
- Bullet points for lists
- Code blocks for metrics/numbers
"""

    def _get_vectorstore(self):
        """Get pgvector vector store for retrieval."""
        connection_string = settings.database_url
        collection_name = "agi_tracker_docs"
        
        vectorstore = PGVector(
            connection_string=connection_string,
            embedding_function=self.embeddings,
            collection_name=collection_name,
        )
        
        return vectorstore

    def _is_out_of_scope(self, question: str) -> bool:
        """Check if question is out of scope."""
        # Simple keyword-based detection
        agi_keywords = [
            "agi", "ai", "artificial intelligence", "llm", "gpt", "claude",
            "machine learning", "neural network", "benchmark", "swe-bench",
            "osworld", "webarena", "gpqa", "compute", "flop", "signpost",
            "capability", "security", "alignment", "safety"
        ]
        
        question_lower = question.lower()
        
        # Check if any AGI keyword is in question
        for keyword in agi_keywords:
            if keyword in question_lower:
                return False
        
        # Check for obvious out-of-scope patterns
        out_of_scope_patterns = [
            "weather", "sports", "recipe", "movie", "song", "game",
            "personal advice", "medical", "legal"
        ]
        
        for pattern in out_of_scope_patterns:
            if pattern in question_lower:
                return True
        
        # Default: assume in-scope (let LLM handle edge cases)
        return False

    async def chat_stream(
        self,
        message: str,
        session_id: str,
        top_k: int = 5
    ) -> AsyncIterator[Dict]:
        """
        Stream chat response with retrieved sources.
        
        Args:
            message: User message
            session_id: Conversation session ID
            top_k: Number of documents to retrieve
            
        Yields:
            Chunks of response: {"type": "token"|"sources"|"done", ...}
        """
        # Check if out of scope
        if self._is_out_of_scope(message):
            yield {
                "type": "token",
                "content": "I can only answer questions about AGI/AI progress tracking. Please ask about AI capabilities, benchmarks, security, or related topics."
            }
            yield {"type": "done"}
            return
        
        # Retrieve relevant documents
        db = SessionLocal()
        try:
            sources = await self._retrieve_sources(message, top_k, db)
            
            # Build context from sources
            context = self._build_context(sources)
            
            # Generate response with streaming
            response_chunks = []
            
            async for chunk in self._generate_response_stream(message, context, session_id):
                if chunk:
                    yield {"type": "token", "content": chunk}
                    response_chunks.append(chunk)
            
            # Yield sources
            yield {"type": "sources", "sources": sources}
            
            # Done
            yield {"type": "done"}
            
            # Cache conversation
            self._cache_conversation(session_id, message, "".join(response_chunks))
            
        finally:
            db.close()

    async def _retrieve_sources(
        self,
        query: str,
        top_k: int,
        db
    ) -> List[Dict]:
        """Retrieve relevant sources using vector similarity."""
        from app.services.embedding_service import embedding_service
        
        # Generate query embedding
        query_embedding = embedding_service.embed_single(query, use_cache=True)
        
        # Query events using cosine similarity
        event_query = text("""
            SELECT 
                id, title, summary, source_url, evidence_tier, published_at, publisher,
                1 - (embedding <=> :query_embedding::vector) as similarity
            FROM events
            WHERE embedding IS NOT NULL
                AND retracted = false
                AND evidence_tier IN ('A', 'B', 'C')
            ORDER BY embedding <=> :query_embedding::vector
            LIMIT :limit
        """)
        
        event_results = db.execute(
            event_query,
            {"query_embedding": str(query_embedding), "limit": top_k}
        ).fetchall()
        
        # Query signposts
        signpost_query = text("""
            SELECT 
                id, code, name, description, category, short_explainer,
                1 - (embedding <=> :query_embedding::vector) as similarity
            FROM signposts
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> :query_embedding::vector
            LIMIT :limit
        """)
        
        signpost_results = db.execute(
            signpost_query,
            {"query_embedding": str(query_embedding), "limit": top_k // 2}
        ).fetchall()
        
        # Format sources
        sources = []
        
        for row in event_results:
            sources.append({
                "type": "event",
                "id": row.id,
                "title": row.title,
                "summary": row.summary,
                "url": row.source_url,
                "tier": row.evidence_tier,
                "published_at": row.published_at.isoformat() if row.published_at else None,
                "publisher": row.publisher,
                "similarity": float(row.similarity)
            })
        
        for row in signpost_results:
            sources.append({
                "type": "signpost",
                "id": row.id,
                "code": row.code,
                "name": row.name,
                "description": row.description,
                "category": row.category,
                "explainer": row.short_explainer,
                "similarity": float(row.similarity)
            })
        
        # Sort by similarity
        sources.sort(key=lambda x: x["similarity"], reverse=True)
        
        return sources[:top_k]

    def _build_context(self, sources: List[Dict]) -> str:
        """Build context string from retrieved sources."""
        if not sources:
            return "No relevant information found."
        
        context_parts = []
        
        for i, source in enumerate(sources, 1):
            if source["type"] == "event":
                context_parts.append(
                    f"{i}. [Event] {source['title']} ({source['tier']}-tier, {source.get('publisher', 'Unknown')}, {source.get('published_at', 'Unknown date')})\n"
                    f"   {source.get('summary', 'No summary')}\n"
                    f"   URL: {source['url']}"
                )
            elif source["type"] == "signpost":
                context_parts.append(
                    f"{i}. [Signpost] {source['name']} ({source['code']}, {source['category']})\n"
                    f"   {source.get('description', 'No description')}\n"
                    f"   {source.get('explainer', '')}"
                )
        
        return "\n\n".join(context_parts)

    async def _generate_response_stream(
        self,
        message: str,
        context: str,
        session_id: str
    ) -> AsyncIterator[str]:
        """Generate streaming response using LLM."""
        # Get conversation history
        history = self._get_conversation_history(session_id)
        
        # Build prompt
        prompt = f"""{self.system_prompt}

Context (retrieved documents):
{context}

Conversation history:
{history}

User question: {message}

Assistant response:"""
        
        # Stream response
        async for chunk in self.llm.astream(prompt):
            if hasattr(chunk, 'content'):
                yield chunk.content

    def _get_conversation_history(self, session_id: str) -> str:
        """Get conversation history from Redis."""
        key = f"chat_history:{session_id}"
        history_json = self.redis_client.get(key)
        
        if not history_json:
            return "No previous conversation."
        
        history = json.loads(history_json)
        
        # Format last N messages
        messages = history[-self.memory_window * 2:]  # User + assistant pairs
        
        formatted = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            formatted.append(f"{role.capitalize()}: {content}")
        
        return "\n".join(formatted) if formatted else "No previous conversation."

    def _cache_conversation(self, session_id: str, user_message: str, assistant_message: str):
        """Cache conversation in Redis."""
        key = f"chat_history:{session_id}"
        
        # Get existing history
        history_json = self.redis_client.get(key)
        history = json.loads(history_json) if history_json else []
        
        # Append new messages
        history.append({"role": "user", "content": user_message})
        history.append({"role": "assistant", "content": assistant_message})
        
        # Keep last 20 messages
        history = history[-20:]
        
        # Save with 1 hour TTL
        self.redis_client.setex(key, 3600, json.dumps(history))

    def get_suggested_questions(self) -> List[str]:
        """Get suggested starter questions."""
        return [
            "What's the current progress on SWE-bench?",
            "How are we doing on AGI security measures?",
            "What are the most recent A-tier AI breakthroughs?",
            "Compare current AI capabilities to expert predictions",
            "What signposts have moved the most this quarter?",
            "Explain the OSWorld benchmark and recent progress",
            "What's the latest on compute scaling?",
            "How does GPT-4 compare to AGI milestones?"
        ]


# Singleton instance
rag_chatbot = RAGChatbot()


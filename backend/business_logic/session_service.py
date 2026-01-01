"""
Chat Session Service.

Business logic for managing chat sessions with Supabase.
Uses Gemini Flash Lite for title generation.
"""

import logging
from typing import Optional, List, Any, Dict
from uuid import UUID, uuid4
from datetime import datetime

from supabase import create_client, Client
from google import genai

from core.config import get_config

logger = logging.getLogger(__name__)


class SessionService:
    """
    Service for managing chat sessions.
    
    Handles CRUD operations on chat_sessions table and title generation.
    """
    
    def __init__(self, supabase_client: Client):
        """
        Initialize session service.
        
        Args:
            supabase_client: Supabase client instance
        """
        self.supabase = supabase_client
        self._genai_client = None
    
    @property
    def genai_client(self):
        """Lazy-load Gemini client."""
        if self._genai_client is None:
            config = get_config()
            self._genai_client = genai.Client(
                vertexai=True,
                project=config.google_cloud.project_id,
                location=config.google_cloud.location
            )
        return self._genai_client
    
    async def generate_title(self, first_message: str) -> str:
        """
        Generate a short title for a chat session using Gemini Flash Lite.
        
        Args:
            first_message: The first user message in the chat
            
        Returns:
            A 3-5 word title string
        """
        try:
            prompt = f"""Generate a very short title (3-5 words max) for a chat that starts with this message. 
Return ONLY the title, no quotes, no explanation.

Message: {first_message[:500]}"""

            response = self.genai_client.models.generate_content(
                model="gemini-2.0-flash-lite",
                contents=prompt,
                config={
                    "temperature": 0.7,
                    "max_output_tokens": 20
                }
            )
            
            title = response.text.strip().strip('"\'')
            
            # Fallback if title is too long or empty
            if not title or len(title) > 50:
                title = first_message[:30] + "..." if len(first_message) > 30 else first_message
            
            logger.info(f"Generated title: {title}")
            return title
            
        except Exception as e:
            logger.warning(f"Title generation failed: {e}, using fallback")
            return first_message[:30] + "..." if len(first_message) > 30 else first_message
    
    async def create_session(
        self,
        user_id: UUID,
        session_id: Optional[UUID] = None,
        first_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new chat session.
        
        Args:
            user_id: The user's ID
            session_id: Optional session ID (matches GCS prefix). Auto-generated if not provided.
            first_message: Optional first message for title generation
            
        Returns:
            Created session data
        """
        # Auto-generate session_id if not provided
        if session_id is None:
            session_id = uuid4()
        
        # Generate title if first message provided
        if first_message:
            title = await self.generate_title(first_message)
        else:
            title = "New Chat"
        
        data = {
            "id": str(session_id),
            "user_id": str(user_id),
            "title": title,
            "messages": [],
            "composition": []
        }
        
        result = self.supabase.table("chat_sessions").insert(data).execute()
        
        if result.data:
            logger.info(f"Created session {session_id} for user {user_id}")
            return result.data[0]
        else:
            raise Exception("Failed to create session")
    
    async def get_session(self, user_id: UUID, session_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get a single session by ID.
        
        Args:
            user_id: The user's ID (for verification)
            session_id: The session ID
            
        Returns:
            Session data or None if not found
        """
        result = self.supabase.table("chat_sessions").select("*").eq(
            "id", str(session_id)
        ).eq(
            "user_id", str(user_id)
        ).execute()
        
        if result.data:
            return result.data[0]
        return None
    
    async def list_sessions(
        self,
        user_id: UUID,
        limit: int = 50,
        offset: int = 0
    ) -> tuple[List[Dict[str, Any]], int]:
        """
        List sessions for a user, sorted by most recent.
        
        Args:
            user_id: The user's ID
            limit: Max sessions to return
            offset: Pagination offset
            
        Returns:
            Tuple of (sessions list, total count)
        """
        # Get sessions with only metadata (not full messages/composition)
        result = self.supabase.table("chat_sessions").select(
            "id, title, created_at, updated_at",
            count="exact"
        ).eq(
            "user_id", str(user_id)
        ).order(
            "updated_at", desc=True
        ).range(
            offset, offset + limit - 1
        ).execute()
        
        total = result.count or 0
        sessions = result.data or []
        
        logger.info(f"Listed {len(sessions)} sessions for user {user_id}")
        return sessions, total
    
    async def update_session(
        self,
        user_id: UUID,
        session_id: UUID,
        title: Optional[str] = None,
        messages: Optional[List[Dict[str, Any]]] = None,
        composition: Optional[Any] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Update a session's data.
        
        Args:
            user_id: The user's ID (for verification)
            session_id: The session ID
            title: New title (optional)
            messages: New messages array (optional)
            composition: New composition blueprint (optional)
            
        Returns:
            Updated session data or None if not found
        """
        update_data = {}
        
        if title is not None:
            update_data["title"] = title
        if messages is not None:
            update_data["messages"] = messages
        if composition is not None:
            update_data["composition"] = composition
        
        if not update_data:
            # Nothing to update, just return current session
            return await self.get_session(user_id, session_id)
        
        result = self.supabase.table("chat_sessions").update(
            update_data
        ).eq(
            "id", str(session_id)
        ).eq(
            "user_id", str(user_id)
        ).execute()
        
        if result.data:
            logger.info(f"Updated session {session_id}")
            return result.data[0]
        return None
    
    async def save_state(
        self,
        user_id: UUID,
        session_id: UUID,
        messages: List[Dict[str, Any]],
        composition: Optional[Any] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Save session state (messages and composition).
        Convenience wrapper around update_session.
        
        Args:
            user_id: The user's ID
            session_id: The session ID  
            messages: Messages array
            composition: Composition blueprint
            
        Returns:
            Updated session data or None if not found
        """
        return await self.update_session(
            user_id=user_id,
            session_id=session_id,
            messages=messages,
            composition=composition
        )
    
    async def delete_session(self, user_id: UUID, session_id: UUID) -> bool:
        """
        Delete a session.
        
        Args:
            user_id: The user's ID (for verification)
            session_id: The session ID
            
        Returns:
            True if deleted, False if not found
        """
        result = self.supabase.table("chat_sessions").delete().eq(
            "id", str(session_id)
        ).eq(
            "user_id", str(user_id)
        ).execute()
        
        if result.data:
            logger.info(f"Deleted session {session_id}")
            return True
        return False
    
    async def get_or_create_session(
        self,
        user_id: UUID,
        session_id: UUID,
        first_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get existing session or create new one.
        
        Args:
            user_id: The user's ID
            session_id: The session ID
            first_message: First message for title generation (if creating)
            
        Returns:
            Session data
        """
        session = await self.get_session(user_id, session_id)
        
        if session:
            return session
        
        return await self.create_session(user_id, session_id, first_message)

"""
OpenAI Whisper API service for audio transcription with word-level timestamps.

Provides high-precision word-level timestamps for generated voiceovers.
"""

import logging
import os
import io
from typing import List, Optional
from openai import AsyncOpenAI

from services.base.VoiceGenerationProvider import WhisperTimestamp

logger = logging.getLogger(__name__)


class WhisperService:
    """
    Service for transcribing audio with word-level timestamps using OpenAI Whisper API.
    
    Uses the latest Whisper model with timestamp_granularities for millisecond precision.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Whisper service.
        
        Args:
            api_key: OpenAI API key (optional, will use env var if not provided)
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        self.client = AsyncOpenAI(api_key=self.api_key)
        logger.info("Initialized Whisper service with OpenAI API")
    
    async def transcribe_with_timestamps(
        self,
        audio_bytes: bytes,
        audio_format: str = "mp3",
        language: Optional[str] = None
    ) -> List[WhisperTimestamp]:
        """
        Transcribe audio and extract word-level timestamps.
        
        Args:
            audio_bytes: Raw audio data
            audio_format: Audio format (mp3, wav, etc.)
            language: Optional language code (e.g., "en") for better accuracy
            
        Returns:
            List of WhisperTimestamp objects with word-level timing
            
        Raises:
            RuntimeError: If transcription fails
        """
        try:
            logger.info(f"Transcribing {len(audio_bytes)} bytes of {audio_format} audio")
            
            # Create file-like object for API
            audio_file = io.BytesIO(audio_bytes)
            audio_file.name = f"audio.{audio_format}"
            
            # Call Whisper API with word-level timestamps
            # Using verbose_json response_format to get word-level timestamps
            transcription = await self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="verbose_json",
                timestamp_granularities=["word"],
                language=language
            )
            
            # Extract word-level timestamps
            word_timestamps = []
            if hasattr(transcription, 'words') and transcription.words:
                for word_data in transcription.words:
                    word_timestamps.append(WhisperTimestamp(
                        word=word_data.word.strip(),
                        start=word_data.start,
                        end=word_data.end
                    ))
                
                logger.info(f"Extracted {len(word_timestamps)} word timestamps")
            else:
                logger.warning("No word-level timestamps returned from Whisper")
            
            return word_timestamps
            
        except Exception as e:
            logger.error(f"Whisper transcription failed: {str(e)}", exc_info=True)
            raise RuntimeError(f"Failed to transcribe audio: {str(e)}")

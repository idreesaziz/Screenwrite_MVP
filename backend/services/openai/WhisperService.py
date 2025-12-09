"""
OpenAI Whisper API service for audio transcription with word-level timestamps.

Provides high-precision word-level timestamps for generated voiceovers.
"""

import logging
import os
import io
from typing import List, Optional
from openai import AsyncOpenAI
import numpy as np
from pydub import AudioSegment

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
                
                # Refine timestamps by snapping to zero-crossings for cleaner cuts
                word_timestamps = self._refine_timestamps(word_timestamps, audio_bytes, audio_format)
            else:
                logger.warning("No word-level timestamps returned from Whisper")
            
            return word_timestamps
            
        except Exception as e:
            logger.error(f"Whisper transcription failed: {str(e)}", exc_info=True)
            raise RuntimeError(f"Failed to transcribe audio: {str(e)}")
    
    def _refine_timestamps(
        self,
        timestamps: List[WhisperTimestamp],
        audio_bytes: bytes,
        audio_format: str,
        window_ms: int = 100
    ) -> List[WhisperTimestamp]:
        """
        Refine timestamps by snapping to nearest zero-crossings.
        
        Zero-crossing detection ensures clean audio cuts without pops or clicks.
        
        Args:
            timestamps: Original timestamps from Whisper
            audio_bytes: Raw audio data
            audio_format: Audio format (mp3, wav, etc.)
            window_ms: Search window in milliseconds (±window_ms around original timestamp)
            
        Returns:
            Refined timestamps snapped to zero-crossings
        """
        try:
            # Load audio with pydub
            audio = AudioSegment.from_file(io.BytesIO(audio_bytes), format=audio_format)
            samples = np.array(audio.get_array_of_samples())
            sample_rate = audio.frame_rate
            
            logger.info(f"Refining {len(timestamps)} timestamps using zero-crossing detection (±{window_ms}ms window)")
            
            refined = []
            for ts in timestamps:
                # Snap both start and end to zero-crossings
                refined_start = self._snap_to_zero_crossing(ts.start, samples, sample_rate, window_ms)
                refined_end = self._snap_to_zero_crossing(ts.end, samples, sample_rate, window_ms)
                
                refined.append(WhisperTimestamp(
                    word=ts.word,
                    start=refined_start,
                    end=refined_end
                ))
            
            logger.info(f"Timestamp refinement complete")
            return refined
            
        except Exception as e:
            logger.warning(f"Timestamp refinement failed, using original timestamps: {str(e)}")
            return timestamps  # Graceful degradation
    
    def _snap_to_zero_crossing(
        self,
        time_s: float,
        samples: np.ndarray,
        sample_rate: int,
        window_ms: int
    ) -> float:
        """
        Find nearest zero-crossing within window around given time.
        
        Args:
            time_s: Target time in seconds
            samples: Audio samples array
            sample_rate: Sample rate in Hz
            window_ms: Search window in milliseconds
            
        Returns:
            Time of nearest zero-crossing in seconds
        """
        center_sample = int(time_s * sample_rate)
        window_samples = int((window_ms / 1000) * sample_rate)
        
        # Define search window
        start = max(0, center_sample - window_samples)
        end = min(len(samples), center_sample + window_samples)
        
        # Extract window
        window = samples[start:end]
        
        # Find zero-crossings (sign changes)
        # np.diff(np.sign(window)) will be non-zero at zero-crossings
        sign_changes = np.diff(np.sign(window))
        zero_crossings = np.where(sign_changes != 0)[0]
        
        if len(zero_crossings) > 0:
            # Pick crossing nearest to center
            relative_center = center_sample - start
            nearest_idx = zero_crossings[np.argmin(np.abs(zero_crossings - relative_center))]
            absolute_sample = start + nearest_idx
            return absolute_sample / sample_rate
        
        # Fallback to original time if no zero-crossing found
        return time_s

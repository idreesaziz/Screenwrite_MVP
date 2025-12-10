"""
OpenAI Whisper API service for audio transcription with word-level timestamps.

Provides high-precision word-level timestamps for generated voiceovers.
"""

import logging
import os
import io
from typing import List, Optional, Tuple
from openai import AsyncOpenAI
import numpy as np
from pydub import AudioSegment
from pydub.silence import detect_silence

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
                
                # Refine timestamps by snapping to silence gaps (for clean narration)
                # Higher min_silence_duration filters out mid-word pauses
                word_timestamps = self._refine_with_silence_detection(
                    word_timestamps, 
                    audio_bytes, 
                    audio_format,
                    silence_thresh_db=-40,
                    min_silence_duration_ms=100,  # Increased to avoid mid-word pauses
                    snap_window_ms=200
                )
            else:
                logger.warning("No word-level timestamps returned from Whisper")
            
            return word_timestamps
            
        except Exception as e:
            logger.error(f"Whisper transcription failed: {str(e)}", exc_info=True)
            raise RuntimeError(f"Failed to transcribe audio: {str(e)}")
    
    def _refine_with_silence_detection(
        self,
        timestamps: List[WhisperTimestamp],
        audio_bytes: bytes,
        audio_format: str,
        silence_thresh_db: int = -40,
        min_silence_duration_ms: int = 50,
        snap_window_ms: int = 150
    ) -> List[WhisperTimestamp]:
        """
        Refine word timestamps by snapping to nearest silence gaps.
        
        For clean narration, natural pauses between words are silence gaps.
        This snaps word boundaries to these gaps for cleaner cuts.
        
        Args:
            timestamps: Original timestamps from Whisper
            audio_bytes: Raw audio data
            audio_format: Audio format (mp3, wav, etc.)
            silence_thresh_db: Silence threshold in dB (default: -40dB)
            min_silence_duration_ms: Minimum silence duration to consider (default: 50ms)
            snap_window_ms: Maximum distance to snap timestamps (default: 150ms)
            
        Returns:
            Refined timestamps snapped to silence gaps
        """
        try:
            # Load audio
            audio = AudioSegment.from_file(io.BytesIO(audio_bytes), format=audio_format)
            
            logger.info(f"Detecting silence gaps (thresh={silence_thresh_db}dB, min_duration={min_silence_duration_ms}ms)")
            
            # Detect all silence spans
            silence_ranges = detect_silence(
                audio,
                min_silence_len=min_silence_duration_ms,
                silence_thresh=silence_thresh_db
            )
            
            # Convert to seconds and filter by duration threshold
            silence_gaps = [
                (start_ms / 1000.0, end_ms / 1000.0)
                for start_ms, end_ms in silence_ranges
                if (end_ms - start_ms) >= min_silence_duration_ms
            ]
            
            # Add synthetic silence gap at the end of audio
            audio_duration_s = len(audio) / 1000.0
            silence_gaps.append((audio_duration_s, audio_duration_s + 0.1))
            
            logger.info(f"Found {len(silence_gaps)-1} silence gaps (>={min_silence_duration_ms}ms), added end gap")
            
            if not silence_gaps:
                logger.warning("No silence gaps detected, using original timestamps")
                return timestamps
            
            # Refine each timestamp by snapping to nearest silence
            refined = []
            snap_window_s = snap_window_ms / 1000.0
            
            for i, ts in enumerate(timestamps):
                gap_for_start, dist_start = self._find_closest_gap(ts.start, silence_gaps)
                if gap_for_start and dist_start <= snap_window_s:
                    new_start = gap_for_start[1]
                else:
                    new_start = ts.start

                gap_for_end, dist_end = self._find_closest_gap(ts.end, silence_gaps)
                if gap_for_end and dist_end <= snap_window_s:
                    new_end = gap_for_end[0]
                else:
                    new_end = ts.end

                if new_end <= new_start:
                    new_start, new_end = ts.start, ts.end
                
                refined.append(WhisperTimestamp(
                    word=ts.word,
                    start=new_start,
                    end=new_end
                ))
            
            # Count how many were refined
            refined_count = sum(
                1 for i, ts in enumerate(timestamps)
                if abs(refined[i].start - ts.start) > 0.001 or abs(refined[i].end - ts.end) > 0.001
            )
            
            logger.info(f"Refined {refined_count}/{len(timestamps)} timestamps using silence detection")
            return refined
            
        except Exception as e:
            logger.warning(f"Silence detection failed, using original timestamps: {str(e)}")
            return timestamps
    
    def _find_closest_gap(
        self,
        time: float,
        silence_gaps: List[Tuple[float, float]]
    ) -> Tuple[Optional[Tuple[float, float]], float]:
        """Return the closest silence gap and its distance to the timestamp."""
        closest_gap = None
        best_dist = float('inf')

        for gap_start, gap_end in silence_gaps:
            dist = min(abs(time - gap_start), abs(time - gap_end))
            if dist < best_dist:
                best_dist = dist
                closest_gap = (gap_start, gap_end)

        return closest_gap, best_dist

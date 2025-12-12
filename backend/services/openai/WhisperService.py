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
            full_text = transcription.text if hasattr(transcription, 'text') else ""
            
            if hasattr(transcription, 'words') and transcription.words:
                for word_data in transcription.words:
                    word_timestamps.append(WhisperTimestamp(
                        word=word_data.word.strip(),
                        start=word_data.start,
                        end=word_data.end
                    ))
                
                # Group words into sentences based on full text punctuation
                word_timestamps = self._group_into_sentences(word_timestamps, full_text)
                
                # Refine timestamps by snapping to silence gaps (for clean narration)
                # Higher min_silence_duration filters out mid-word pauses
                word_timestamps = self._refine_with_silence_detection(
                    word_timestamps, 
                    audio_bytes, 
                    audio_format,
                    silence_thresh_db=-60,
                    min_silence_duration_ms=150,
                    snap_window_ms=500
                )
            else:
                logger.warning("No word-level timestamps returned from Whisper")
            
            return word_timestamps
            
        except Exception as e:
            logger.error(f"Whisper transcription failed: {str(e)}", exc_info=True)
            raise RuntimeError(f"Failed to transcribe audio: {str(e)}")
    
    def _group_into_sentences(self, word_timestamps: List[WhisperTimestamp], full_text: str) -> List[WhisperTimestamp]:
        """Group word-level timestamps into sentences based on punctuation in full text."""
        if not word_timestamps or not full_text:
            return word_timestamps
        
        # Split full text into sentences
        import re
        sentences_text = re.split(r'([.!?])\s+', full_text)
        
        # Reconstruct sentences with their punctuation
        sentences = []
        for i in range(0, len(sentences_text) - 1, 2):
            if i + 1 < len(sentences_text):
                sentences.append(sentences_text[i] + sentences_text[i + 1])
        # Handle last sentence if no punctuation at end
        if len(sentences_text) % 2 == 1 and sentences_text[-1].strip():
            sentences.append(sentences_text[-1])
        
        # Map words to sentences
        result = []
        word_idx = 0
        
        for sentence_text in sentences:
            # Count words in this sentence (approximate)
            sentence_words = sentence_text.strip().split()
            sentence_word_count = len(sentence_words)
            
            # Collect timestamps for this sentence
            sentence_timestamps = []
            for _ in range(min(sentence_word_count, len(word_timestamps) - word_idx)):
                if word_idx < len(word_timestamps):
                    sentence_timestamps.append(word_timestamps[word_idx])
                    word_idx += 1
            
            if sentence_timestamps:
                result.append(WhisperTimestamp(
                    word=sentence_text.strip(),
                    start=sentence_timestamps[0].start,
                    end=sentence_timestamps[-1].end
                ))
        
        return result
    
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
            
            # Add synthetic silence gaps at the start and end of audio
            silence_gaps.insert(0, (-0.1, 0.0))  # Start gap
            audio_duration_s = len(audio) / 1000.0
            silence_gaps.append((audio_duration_s, audio_duration_s + 0.1))  # End gap
            
            if not silence_gaps:
                logger.warning("No silence gaps detected, using original timestamps")
                return timestamps
            
            # Refine each timestamp by snapping to nearest silence
            refined = []
            snap_window_s = snap_window_ms / 1000.0
            
            for i, ts in enumerate(timestamps):
                gap_for_start, dist_start = self._find_closest_gap(ts.start, silence_gaps)
                gap_for_end, dist_end = self._find_closest_gap(ts.end, silence_gaps)
                
                new_start = gap_for_start[1] if gap_for_start else ts.start
                new_end = gap_for_end[0] if gap_for_end else ts.end
                
                refined.append(WhisperTimestamp(
                    word=ts.word,
                    start=new_start,
                    end=new_end
                ))
            
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

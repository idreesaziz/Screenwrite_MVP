"""
Abstract base class for voice/speech generation providers.

This module defines the contract that all voice generation provider implementations must follow.
It provides a consistent interface for different TTS services (Google TTS, ElevenLabs, AWS Polly, etc.).
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class WhisperTimestamp:
    """
    Word-level timestamp from Whisper transcription.
    
    Attributes:
        word: The transcribed word
        start: Start time in seconds (decimal)
        end: End time in seconds (decimal)
    """
    word: str
    start: float
    end: float


@dataclass
class VoiceGenerationRequest:
    """
    Represents a request to generate speech from text.
    
    Attributes:
        text: The text script to convert to speech
        voice_id: Voice model identifier (e.g., "Aoede", "Charon")
        language_code: BCP-47 language code (e.g., "en-US", "es-ES")
        style_prompt: Optional delivery style prompt (e.g., "Speak dramatically", "Whisper quietly [whispering]")
                      If None, defaults to natural conversational tone
        speaking_rate: Speech speed (0.25 to 4.0, where 1.0 is normal)
        pitch: Voice pitch adjustment (-20.0 to 20.0, where 0.0 is normal)
        audio_encoding: Output format ("MP3", "WAV", "OGG")
        sample_rate_hertz: Audio sample rate (8000, 16000, 24000, etc.)
        effects_profile_id: Optional audio effects (e.g., ["telephony-class-application"])
        metadata: Optional additional parameters
    """
    text: str
    voice_id: str
    language_code: str = "en-US"
    style_prompt: Optional[str] = None
    speaking_rate: float = 1.0
    pitch: float = 0.0
    audio_encoding: str = "MP3"
    sample_rate_hertz: int = 24000
    effects_profile_id: List[str] = field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class GeneratedVoiceResult:
    """
    Represents the result of voice generation.
    
    Attributes:
        audio_bytes: Raw audio data
        duration_seconds: Length of audio in seconds (CRITICAL for timeline placement)
        audio_url: Cloud storage URL (set after upload)
        sample_rate: Audio sample rate in Hz
        voice_model: Voice model used for generation
        audio_encoding: Format of audio (MP3, WAV, etc.)
        text_length: Number of characters in original text
        word_timestamps: Word-level timestamps from Whisper (if available)
        metadata: Additional information about the generation
    """
    audio_bytes: bytes
    duration_seconds: float
    audio_url: str
    sample_rate: int
    voice_model: str
    audio_encoding: str
    text_length: int
    word_timestamps: Optional[List[WhisperTimestamp]] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class VoiceInfo:
    """
    Information about an available voice model.
    
    Attributes:
        voice_id: Unique identifier for the voice
        name: Human-readable name
        language_code: Supported language
        gender: Voice gender ("MALE", "FEMALE", "NEUTRAL")
        voice_type: Type/quality ("NEURAL2", "STANDARD", "WAVENET", "STUDIO")
    """
    voice_id: str
    name: str
    language_code: str
    gender: str
    voice_type: str


class VoiceGenerationProvider(ABC):
    """
    Abstract base class for voice/speech generation providers.
    
    All voice generation implementations must inherit from this class and implement
    the required methods. This ensures consistent interface across different TTS services.
    """
    
    @abstractmethod
    async def generate_voice(self, request: VoiceGenerationRequest) -> GeneratedVoiceResult:
        """
        Generate speech audio from text.
        
        Args:
            request: Voice generation request with text, voice settings, etc.
            
        Returns:
            GeneratedVoiceResult with audio bytes, duration, and metadata
            
        Raises:
            RuntimeError: If voice generation fails
        """
        pass
    
    @abstractmethod
    def list_voices(self, language_code: Optional[str] = None) -> List[VoiceInfo]:
        """
        List available voice models.
        
        Args:
            language_code: Optional filter by language (e.g., "en-US")
            
        Returns:
            List of available voices with their properties
        """
        pass
    
    @abstractmethod
    def get_voice_info(self, voice_id: str) -> Optional[VoiceInfo]:
        """
        Get information about a specific voice.
        
        Args:
            voice_id: Voice identifier
            
        Returns:
            Voice information or None if not found
        """
        pass

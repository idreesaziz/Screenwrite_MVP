"""
Google Cloud Text-to-Speech provider implementation.

Implements VoiceGenerationProvider using Google Cloud TTS API with Neural2 and Studio voices.
"""

import logging
import io
from typing import List, Optional, Dict, Any
from google.cloud import texttospeech
from pydub import AudioSegment

from services.base.VoiceGenerationProvider import (
    VoiceGenerationProvider,
    VoiceGenerationRequest,
    GeneratedVoiceResult,
    VoiceInfo
)

logger = logging.getLogger(__name__)


class GoogleTTSProvider(VoiceGenerationProvider):
    """
    Google Cloud Text-to-Speech implementation with Gemini 2.5 Pro TTS.
    
    Supports:
    - Gemini 2.5 Pro TTS (highest quality, prompt-based style control)
    - Gemini 2.5 Flash TTS (low latency, cost-efficient)
    - 30+ voice options (Aoede, Charon, Kore, etc.)
    - 100+ languages
    """
    
    def __init__(self):
        """Initialize Google TTS client for Gemini 2.5 Pro TTS."""
        self.client = texttospeech.TextToSpeechClient()
        logger.info("GoogleTTSProvider initialized with Gemini 2.5 Pro TTS")
    
    async def generate_voice(self, request: VoiceGenerationRequest) -> GeneratedVoiceResult:
        """
        Generate speech using Gemini 2.5 Pro TTS with prompt-based style control.
        
        Args:
            request: Voice generation request with text and settings
            
        Returns:
            GeneratedVoiceResult with audio bytes and metadata
            
        Raises:
            RuntimeError: If TTS generation fails
        """
        try:
            logger.info(f"Generating voice with Gemini 2.5 Pro TTS: {len(request.text)} chars, voice={request.voice_id}")
            
            # Gemini TTS uses BOTH text AND prompt for style control
            # Use custom style_prompt if provided, otherwise default to natural tone
            style_prompt = request.style_prompt or "Read aloud in a natural, conversational tone with appropriate expression and emotion."
            logger.info(f"Style prompt: {style_prompt}")
            
            synthesis_input = texttospeech.SynthesisInput(
                text=request.text,
                prompt=style_prompt
            )
            
            # Configure voice with Gemini 2.5 Pro model
            voice = texttospeech.VoiceSelectionParams(
                language_code=request.language_code,
                name=request.voice_id,  # Simple names: "Aoede", "Charon", "Kore", etc.
                model_name="gemini-2.5-pro-tts"
            )
            
            # Map audio encoding
            encoding_map = {
                "MP3": texttospeech.AudioEncoding.MP3,
                "WAV": texttospeech.AudioEncoding.LINEAR16,
                "OGG": texttospeech.AudioEncoding.OGG_OPUS,
            }
            audio_encoding = encoding_map.get(request.audio_encoding, texttospeech.AudioEncoding.MP3)
            
            # Audio config - Gemini TTS handles quality internally
            audio_config = texttospeech.AudioConfig(
                audio_encoding=audio_encoding,
                speaking_rate=request.speaking_rate,
                pitch=request.pitch,
                sample_rate_hertz=request.sample_rate_hertz
            )
            
            # Generate speech
            response = self.client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            
            logger.info(f"TTS generated {len(response.audio_content)} bytes")
            
            # Calculate duration from audio bytes
            duration = self._calculate_duration(response.audio_content, request.audio_encoding)
            logger.info(f"Audio duration: {duration:.2f} seconds")
            
            return GeneratedVoiceResult(
                audio_bytes=response.audio_content,
                duration_seconds=duration,
                audio_url="",  # Will be set after upload to GCS
                sample_rate=request.sample_rate_hertz,
                voice_model=request.voice_id,
                audio_encoding=request.audio_encoding,
                text_length=len(request.text),
                metadata={
                    "language_code": request.language_code,
                    "speaking_rate": request.speaking_rate,
                    "pitch": request.pitch,
                    "provider": "google_tts"
                }
            )
            
        except Exception as e:
            logger.error(f"Google TTS generation failed: {str(e)}")
            raise RuntimeError(f"Voice generation failed: {str(e)}")
    
    def _calculate_duration(self, audio_bytes: bytes, encoding: str) -> float:
        """
        Calculate audio duration from bytes.
        
        Args:
            audio_bytes: Raw audio data
            encoding: Audio format (MP3, WAV, OGG)
            
        Returns:
            Duration in seconds
        """
        try:
            # Load audio with pydub
            audio_io = io.BytesIO(audio_bytes)
            
            if encoding == "MP3":
                audio = AudioSegment.from_mp3(audio_io)
            elif encoding == "WAV":
                audio = AudioSegment.from_wav(audio_io)
            elif encoding == "OGG":
                audio = AudioSegment.from_ogg(audio_io)
            else:
                audio = AudioSegment.from_file(audio_io)
            
            # Duration in seconds
            return len(audio) / 1000.0
            
        except Exception as e:
            logger.error(f"Failed to calculate duration: {str(e)}")
            # Rough estimate: 150 characters per second for normal speech
            return len(audio_bytes) / 1000.0
    
    def list_voices(self, language_code: Optional[str] = None) -> List[VoiceInfo]:
        """
        List available Google TTS voices.
        
        Args:
            language_code: Optional filter by language (e.g., "en-US")
            
        Returns:
            List of available voices
        """
        try:
            response = self.client.list_voices(language_code=language_code)
            
            voices = []
            for voice in response.voices:
                # Get primary language code (first one if multiple)
                lang_code = voice.language_codes[0] if voice.language_codes else "unknown"
                
                # Determine voice type from name
                voice_type = "STANDARD"
                if "Neural2" in voice.name:
                    voice_type = "NEURAL2"
                elif "Studio" in voice.name:
                    voice_type = "STUDIO"
                elif "Wavenet" in voice.name:
                    voice_type = "WAVENET"
                
                voices.append(VoiceInfo(
                    voice_id=voice.name,
                    name=voice.name,
                    language_code=lang_code,
                    gender=voice.ssml_gender.name,
                    voice_type=voice_type
                ))
            
            return voices
            
        except Exception as e:
            logger.error(f"Failed to list voices: {str(e)}")
            return []
    
    def get_voice_info(self, voice_id: str) -> Optional[VoiceInfo]:
        """
        Get information about a specific voice.
        
        Args:
            voice_id: Voice identifier (e.g., "en-US-Neural2-J")
            
        Returns:
            Voice information or None if not found
        """
        # Extract language code from voice_id (e.g., "en-US" from "en-US-Neural2-J")
        lang_code = "-".join(voice_id.split("-")[:2]) if "-" in voice_id else None
        
        if lang_code:
            voices = self.list_voices(language_code=lang_code)
            for voice in voices:
                if voice.voice_id == voice_id:
                    return voice
        
        return None

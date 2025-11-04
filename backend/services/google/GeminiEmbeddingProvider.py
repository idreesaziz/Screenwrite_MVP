"""Google Text Embedding Provider using Vertex AI."""

import logging
import os
from typing import List, Optional
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)


class GeminiEmbeddingProvider:
    """
    Google Text Embedding Provider using text-embedding-004.
    
    Supports both single and batch embedding generation for RAG systems.
    Authentication uses Application Default Credentials (ADC).
    """
    
    def __init__(
        self,
        project_id: Optional[str] = None,
        location: str = "us-central1",
        model_name: str = "text-embedding-004"
    ):
        """
        Initialize embedding provider.
        
        Args:
            project_id: Google Cloud project ID (optional, will use from ADC if not provided)
            location: GCP region (default: us-central1)
            model_name: Embedding model to use (default: text-embedding-004)
        
        Authentication:
            Uses Application Default Credentials (ADC) in this order:
            1. GOOGLE_APPLICATION_CREDENTIALS environment variable
            2. gcloud auth application-default login
            3. Workload Identity (in GKE/Cloud Run)
        """
        self.project_id = project_id or os.getenv('GOOGLE_CLOUD_PROJECT')
        self.location = location
        self.model_name = model_name
        
        # Determine authentication mode: Vertex AI (ADC) or API Key
        # Only use Vertex if explicitly enabled via GOOGLE_GENAI_USE_VERTEXAI=true
        use_vertex = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "").lower() == "true"
        
        # Check for API key first (simpler auth)
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        
        if use_vertex and self.project_id:
            # Use Vertex AI with Application Default Credentials
            logger.info(f"Using Vertex AI mode (project={self.project_id})")
            
            # Ensure Vertex AI environment variable is set
            os.environ['GOOGLE_GENAI_USE_VERTEXAI'] = 'True'
            
            from google.genai.types import HttpOptions
            self.client = genai.Client(
                http_options=HttpOptions(api_version="v1")
            )
            logger.info(f"Initialized Vertex AI embedding client: {model_name}, project: {self.project_id}")
        elif api_key:
            # Use Google AI API with API key (default)
            logger.info("Using Google AI API with API key")
            self.client = genai.Client(api_key=api_key)
            logger.info(f"Initialized Google AI API embedding client: {model_name}")
        else:
            raise ValueError("Either GEMINI_API_KEY or (GOOGLE_GENAI_USE_VERTEXAI=true + GOOGLE_CLOUD_PROJECT) is required")
    
    def embed_single(self, text: str) -> List[float]:
        """
        Generate embedding for a single text (for runtime query embedding).
        
        Args:
            text: Text to embed
            
        Returns:
            List of float values representing the embedding vector
        """
        try:
            response = self.client.models.embed_content(
                model=self.model_name,
                contents=text
            )
            
            # Extract embedding vector
            if hasattr(response, 'embeddings') and len(response.embeddings) > 0:
                embedding = response.embeddings[0]
                if hasattr(embedding, 'values'):
                    return list(embedding.values)
            
            raise ValueError("No embedding returned from API")
            
        except Exception as e:
            logger.error(f"Error embedding single text: {e}")
            raise
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts (for corpus building).
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors (each is a list of floats)
        """
        embeddings = []
        
        # Process one at a time to avoid rate limits and handle errors gracefully
        for i, text in enumerate(texts):
            try:
                logger.info(f"Embedding text {i+1}/{len(texts)}")
                embedding = self.embed_single(text)
                embeddings.append(embedding)
            except Exception as e:
                logger.error(f"Error embedding text {i+1}: {e}")
                # Append None to maintain index alignment
                embeddings.append(None)
        
        return embeddings

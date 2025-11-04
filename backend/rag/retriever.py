"""
Runtime retrieval module for RAG-based example selection.

Loads precomputed embeddings and performs cosine similarity search
to find the most relevant examples for a given query.
"""

import json
import logging
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional

from services.google.GeminiEmbeddingProvider import GeminiEmbeddingProvider

logger = logging.getLogger(__name__)

# Global cache for embeddings (loaded once at startup)
_EMBEDDINGS_CACHE: Optional[List[Dict[str, Any]]] = None
_EMBEDDING_PROVIDER: Optional[GeminiEmbeddingProvider] = None


def load_embeddings(force_reload: bool = False) -> List[Dict[str, Any]]:
    """
    Load precomputed embeddings from embeddings.json.
    
    Embeddings are cached globally after first load for performance.
    
    Args:
        force_reload: Force reload from disk even if cached
        
    Returns:
        List of embedding records with 'filename', 'content', 'embedding' keys
    """
    global _EMBEDDINGS_CACHE
    
    if _EMBEDDINGS_CACHE is not None and not force_reload:
        return _EMBEDDINGS_CACHE
    
    embeddings_path = Path(__file__).parent / "embeddings.json"
    
    if not embeddings_path.exists():
        logger.error(f"Embeddings file not found: {embeddings_path}")
        logger.error("Run 'python -m backend.rag.build_embeddings' to generate embeddings")
        return []
    
    try:
        with open(embeddings_path, 'r', encoding='utf-8') as f:
            embeddings = json.load(f)
        
        logger.info(f"Loaded {len(embeddings)} example embeddings from cache")
        _EMBEDDINGS_CACHE = embeddings
        return embeddings
        
    except Exception as e:
        logger.error(f"Error loading embeddings: {e}")
        return []


def get_embedding_provider() -> GeminiEmbeddingProvider:
    """Get or initialize the embedding provider (singleton)."""
    global _EMBEDDING_PROVIDER
    
    if _EMBEDDING_PROVIDER is None:
        _EMBEDDING_PROVIDER = GeminiEmbeddingProvider()
    
    return _EMBEDDING_PROVIDER


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Compute cosine similarity between two vectors.
    
    Returns:
        Similarity score between -1 and 1 (higher is more similar)
    """
    v1 = np.array(vec1)
    v2 = np.array(vec2)
    
    dot_product = np.dot(v1, v2)
    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return dot_product / (norm1 * norm2)


def retrieve_examples(query: str, k: int = 1) -> List[Dict[str, Any]]:
    """
    Retrieve top-K most relevant examples for a query.
    
    Args:
        query: User query to find examples for
        k: Number of examples to retrieve (default: 1)
        
    Returns:
        List of dicts with 'filename', 'content', 'similarity' keys,
        sorted by similarity (highest first)
    """
    # Load embeddings
    embeddings = load_embeddings()
    if not embeddings:
        logger.warning("No embeddings available for retrieval")
        return []
    
    try:
        # Embed query
        provider = get_embedding_provider()
        logger.info(f"Embedding query: {query[:100]}...")
        query_embedding = provider.embed_single(query)
        
        # Compute similarities
        similarities = []
        for item in embeddings:
            sim = cosine_similarity(query_embedding, item['embedding'])
            similarities.append({
                'filename': item['filename'],
                'content': item['content'],
                'similarity': float(sim)
            })
        
        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        
        # Return top-K
        results = similarities[:k]
        
        # Log retrieval results
        logger.info(f"Retrieved {len(results)} examples:")
        for i, result in enumerate(results):
            logger.info(f"  {i+1}. {result['filename']} (similarity={result['similarity']:.4f})")
        
        return results
        
    except Exception as e:
        logger.error(f"Error during retrieval: {e}")
        return []


def get_example_by_filename(filename: str) -> Optional[str]:
    """
    Get example content by filename (for testing/debugging).
    
    Args:
        filename: Name of the example file (e.g., 'coffee_shop.md')
        
    Returns:
        Example content or None if not found
    """
    embeddings = load_embeddings()
    
    for item in embeddings:
        if item['filename'] == filename:
            return item['content']
    
    return None

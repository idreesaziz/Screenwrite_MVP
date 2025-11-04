#!/usr/bin/env python3
"""
Build embeddings for all example files in the rag/examples/ directory.

This script:
1. Reads all .md files from examples/
2. Generates embeddings using GeminiEmbeddingProvider
3. Saves embeddings and metadata to embeddings.json

Run this script whenever you add/modify examples:
    python -m backend.rag.build_embeddings
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load environment variables
backend_dir = Path(__file__).parent.parent
env_path = backend_dir / ".env"
if env_path.exists():
    load_dotenv(env_path)
    logging.info(f"Loaded environment from {env_path}")

# Add backend to path for imports
sys.path.insert(0, str(backend_dir))

from services.google.GeminiEmbeddingProvider import GeminiEmbeddingProvider

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def read_example_files(examples_dir: Path) -> List[Dict[str, str]]:
    """
    Read all markdown files from examples directory.
    
    Returns:
        List of dicts with 'filename' and 'content' keys
    """
    examples = []
    
    if not examples_dir.exists():
        logger.error(f"Examples directory not found: {examples_dir}")
        return examples
    
    for md_file in sorted(examples_dir.glob("*.md")):
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            examples.append({
                'filename': md_file.name,
                'content': content
            })
            logger.info(f"Read example: {md_file.name} ({len(content)} chars)")
        except Exception as e:
            logger.error(f"Error reading {md_file.name}: {e}")
    
    return examples


def build_embeddings(examples: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    """
    Generate embeddings for all examples.
    
    Returns:
        List of dicts with 'filename', 'content', and 'embedding' keys
    """
    if not examples:
        logger.warning("No examples to embed")
        return []
    
    logger.info(f"Initializing embedding provider...")
    provider = GeminiEmbeddingProvider()
    
    logger.info(f"Generating embeddings for {len(examples)} examples...")
    texts = [ex['content'] for ex in examples]
    embeddings = provider.embed_batch(texts)
    
    # Combine examples with embeddings
    results = []
    for example, embedding in zip(examples, embeddings):
        if embedding is None:
            logger.warning(f"Skipping {example['filename']} due to embedding error")
            continue
        
        results.append({
            'filename': example['filename'],
            'content': example['content'],
            'embedding': embedding,
            'embedding_dim': len(embedding)
        })
        logger.info(f"✓ Embedded {example['filename']} (dim={len(embedding)})")
    
    return results


def save_embeddings(embeddings: List[Dict[str, Any]], output_path: Path):
    """Save embeddings to JSON file."""
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(embeddings, f, indent=2)
        
        logger.info(f"✓ Saved {len(embeddings)} embeddings to {output_path}")
        
        # Print summary
        total_size = output_path.stat().st_size / 1024 / 1024  # MB
        logger.info(f"  File size: {total_size:.2f} MB")
        
    except Exception as e:
        logger.error(f"Error saving embeddings: {e}")
        raise


def main():
    """Main execution."""
    rag_dir = Path(__file__).parent
    examples_dir = rag_dir / "examples"
    output_path = rag_dir / "embeddings.json"
    
    logger.info("=" * 60)
    logger.info("RAG Embedding Builder")
    logger.info("=" * 60)
    logger.info(f"Examples directory: {examples_dir}")
    logger.info(f"Output file: {output_path}")
    logger.info("")
    
    # Read examples
    examples = read_example_files(examples_dir)
    if not examples:
        logger.error("No examples found. Exiting.")
        sys.exit(1)
    
    logger.info(f"Found {len(examples)} example files")
    logger.info("")
    
    # Generate embeddings
    embedded = build_embeddings(examples)
    if not embedded:
        logger.error("Failed to generate embeddings. Exiting.")
        sys.exit(1)
    
    logger.info("")
    
    # Save to file
    save_embeddings(embedded, output_path)
    
    logger.info("")
    logger.info("=" * 60)
    logger.info("✓ Build complete!")
    logger.info("=" * 60)
    logger.info("")
    logger.info("Next steps:")
    logger.info("1. Review embeddings.json to verify results")
    logger.info("2. Test retrieval with backend.rag.retriever")
    logger.info("3. Integrate into invoke_agent.py")


if __name__ == "__main__":
    main()

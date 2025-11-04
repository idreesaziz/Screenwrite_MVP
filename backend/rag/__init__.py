"""
RAG (Retrieval-Augmented Generation) module for example-based agent prompting.

Provides semantic retrieval of relevant example workflows to improve agent consistency.
"""

from .retriever import retrieve_examples, load_embeddings

__all__ = ["retrieve_examples", "load_embeddings"]

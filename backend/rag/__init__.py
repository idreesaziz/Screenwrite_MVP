"""
RAG (Retrieval-Augmented Generation) module for example-based agent prompting.

Provides LLM-based selection of relevant example workflows to improve agent consistency.
"""

from .llm_selector import select_example

__all__ = ["select_example"]

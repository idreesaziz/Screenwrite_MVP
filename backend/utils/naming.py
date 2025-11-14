"""Centralized naming utilities for media assets."""

import re
from typing import Set


def sanitize_name(text: str, max_length: int = 30) -> str:
    """
    Sanitize text to create safe, short names.
    
    Rules:
    - Lowercase
    - Replace spaces and special chars with underscores
    - Keep only alphanumeric and underscores
    - Remove consecutive underscores
    - Truncate to max_length
    
    Args:
        text: Input text to sanitize
        max_length: Maximum length of result (default 30)
        
    Returns:
        Sanitized name string
    """
    if not text:
        return "file"
    
    # Lowercase
    name = text.lower()
    
    # Replace spaces and hyphens with underscores
    name = name.replace(' ', '_').replace('-', '_')
    
    # Keep only alphanumeric and underscores
    name = re.sub(r'[^a-z0-9_]', '_', name)
    
    # Remove consecutive underscores
    name = re.sub(r'_+', '_', name)
    
    # Remove leading/trailing underscores
    name = name.strip('_')
    
    # Truncate to max_length
    if len(name) > max_length:
        name = name[:max_length].rstrip('_')
    
    return name or "file"


def generate_unique_name(base_name: str, existing_names: Set[str]) -> str:
    """
    Generate unique name by appending counter if collision exists.
    
    Args:
        base_name: Base name to use
        existing_names: Set of names that already exist
        
    Returns:
        Unique name (base_name or base_name_2, base_name_3, etc.)
    """
    if base_name not in existing_names:
        return base_name
    
    counter = 2
    while f"{base_name}_{counter}" in existing_names:
        counter += 1
    
    return f"{base_name}_{counter}"


def create_stock_name(creator_name: str, query: str, index: int) -> str:
    """
    Create name for stock media.
    
    Format: {creator_last_name}_{keyword}_{index}
    Example: "cottonbro_coffee_1"
    
    Args:
        creator_name: Creator/photographer name (e.g., "cottonbro studio")
        query: Search query (e.g., "coffee shop cinematic")
        index: 1-based index in results
        
    Returns:
        Sanitized stock media name
    """
    # Extract last word from creator name (usually surname or studio name)
    creator_parts = creator_name.split()
    creator_short = creator_parts[-1] if creator_parts else "unknown"
    
    # Extract first meaningful word from query
    query_parts = query.split()
    keyword = query_parts[0] if query_parts else "media"
    
    # Build base name
    base = f"{creator_short}_{keyword}_{index}"
    
    return sanitize_name(base, max_length=30)


def create_generated_name(suggested_name: str, content_type: str, uuid_short: str) -> str:
    """
    Create name for generated media.
    
    Uses suggested_name if provided, else generates: gen_{type}_{uuid_short}
    Example: "coffee_endcard" or "gen_image_abc123"
    
    Args:
        suggested_name: AI-suggested name (may be empty)
        content_type: Type of content (image/video/logo/audio)
        uuid_short: First 6 chars of UUID
        
    Returns:
        Sanitized generated media name
    """
    if suggested_name and suggested_name.strip():
        return sanitize_name(suggested_name, max_length=30)
    
    # Fallback: gen_{type}_{uuid}
    fallback = f"gen_{content_type}_{uuid_short}"
    return sanitize_name(fallback, max_length=30)


def create_upload_name(original_filename: str) -> str:
    """
    Create name for user upload.
    
    Sanitizes original filename (without extension).
    Example: "My Video.mp4" -> "my_video"
    
    Args:
        original_filename: Original file name from user
        
    Returns:
        Sanitized upload name
    """
    from pathlib import Path
    
    # Remove extension
    name_without_ext = Path(original_filename).stem
    
    return sanitize_name(name_without_ext, max_length=30)

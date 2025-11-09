"""
LLM-based RAG example selector using Gemini Flash Lite.

Uses a fast, cheap LLM to intelligently select the most relevant
example workflow from available guides based on conversation context.
"""

import logging
import os
import re
import json
from typing import List, Dict, Optional
from pathlib import Path
import google.generativeai as genai

logger = logging.getLogger(__name__)

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Model to use (same as fetch sorting)
SELECTOR_MODEL = "gemini-2.0-flash-exp"

# System prompt for the selector
SELECTOR_SYSTEM_PROMPT = """You are a workflow pattern matcher for a video editing AI assistant.

Your job: Analyze the conversation history and select the MOST RELEVANT example workflow guide.

CRITICAL RULES:
1. Analyze the ENTIRE conversation to understand the user's PRIMARY intent
2. Ignore simple confirmations ("yes", "ok", "proceed") - look at the substantive requests
3. For multi-turn conversations, identify the ORIGINAL request that started the workflow
4. Match on workflow PATTERN, not just keywords
5. If no example is truly relevant, return "NONE"
6. Consider whether the user is:
   - Starting a new workflow (select based on new request)
   - Continuing an existing workflow (select based on original request)
   - Making a simple atomic request (may not need example → return NONE)

OUTPUT:
- selected_file: The filename of best match, or "NONE"
- confidence: "high", "medium", or "low"
- reasoning: Brief explanation of your choice (one sentence)
"""


def _extract_when_to_use(content: str) -> str:
    """
    Extract the 'When to Use' section from an example file.
    
    Args:
        content: Full example file content
        
    Returns:
        The 'When to Use' section text, or empty string if not found
    """
    # Pattern: **When to Use:** followed by bullet points until next **Section:**
    pattern = r'\*\*When to Use:\*\*\s*\n((?:[-•]\s+.+\n?)+)'
    match = re.search(pattern, content)
    
    if match:
        return match.group(1).strip()
    
    return ""


def _get_available_examples() -> List[Dict[str, str]]:
    """
    Scan examples directory and extract metadata.
    
    Returns:
        List of dicts with 'filename', 'title', and 'when_to_use' keys
    """
    examples_dir = Path(__file__).parent / "examples"
    examples = []
    
    for filepath in sorted(examples_dir.glob("*.md")):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract title (first # heading)
            title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
            title = title_match.group(1) if title_match else filepath.stem
            
            # Extract when_to_use section
            when_to_use = _extract_when_to_use(content)
            
            examples.append({
                "filename": filepath.name,
                "title": title,
                "when_to_use": when_to_use or "No criteria specified"
            })
            
        except Exception as e:
            logger.warning(f"Error reading example {filepath.name}: {e}")
            continue
    
    return examples


def _format_conversation(conversation_history: List[Dict[str, str]]) -> str:
    """
    Format conversation history for the prompt.
    
    Args:
        conversation_history: List of messages with 'role' and 'content'
        
    Returns:
        Formatted conversation string
    """
    lines = []
    for msg in conversation_history:
        role = msg.get('role', 'user').upper()
        content = msg.get('content', '').strip()
        lines.append(f"{role}: {content}")
    
    return "\n\n".join(lines)


def _load_example_content(filename: str) -> str:
    """
    Load full content of an example file.
    
    Args:
        filename: Name of the example file (e.g., 'short_promo.md')
        
    Returns:
        Full file content
    """
    examples_dir = Path(__file__).parent / "examples"
    filepath = examples_dir / filename
    
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()


async def select_example(
    conversation_history: List[Dict[str, str]]
) -> Optional[Dict[str, str]]:
    """
    Select the most relevant example using Gemini Flash Lite.
    
    Args:
        conversation_history: Full conversation with 'role' and 'content' keys
        
    Returns:
        Dict with 'filename' and 'content' keys, or None if no match
    """
    if not conversation_history:
        logger.warning("No conversation history provided for RAG selection")
        return None
    
    try:
        # Get available examples with metadata
        examples = _get_available_examples()
        
        if not examples:
            logger.warning("No example files found in examples directory")
            return None
        
        logger.info(f"Selecting from {len(examples)} available examples")
        
        # Build prompt
        examples_section = []
        filenames = []
        
        for i, example in enumerate(examples, 1):
            examples_section.append(
                f"{i}. {example['filename']}\n"
                f"   Title: {example['title']}\n"
                f"   When to Use:\n{example['when_to_use']}"
            )
            filenames.append(example['filename'])
        
        conversation_text = _format_conversation(conversation_history)
        
        prompt = f"""CONVERSATION HISTORY:
{conversation_text}

---

AVAILABLE EXAMPLES:
{chr(10).join(examples_section)}

---

Based on the ENTIRE conversation, which example best matches the user's workflow needs?"""
        
        # Define structured output schema
        schema = {
            "type": "object",
            "properties": {
                "selected_file": {
                    "type": "string",
                    "enum": filenames + ["NONE"],
                    "description": "The most relevant example file, or NONE if no match"
                },
                "confidence": {
                    "type": "string",
                    "enum": ["high", "medium", "low"],
                    "description": "Confidence in the selection"
                },
                "reasoning": {
                    "type": "string",
                    "description": "Brief explanation of why this example was chosen"
                }
            },
            "required": ["selected_file", "confidence", "reasoning"]
        }
        
        # Call Gemini Flash Lite
        model = genai.GenerativeModel(
            model_name=SELECTOR_MODEL,
            generation_config={
                "temperature": 0.0,
                "response_mime_type": "application/json",
                "response_schema": schema
            },
            system_instruction=SELECTOR_SYSTEM_PROMPT
        )
        
        response = await model.generate_content_async(prompt)
        result = json.loads(response.text)
        
        selected_file = result.get("selected_file")
        confidence = result.get("confidence")
        reasoning = result.get("reasoning")
        
        logger.info(
            f"Selected: {selected_file} (confidence: {confidence})\n"
            f"Reasoning: {reasoning}"
        )
        
        # Return None if no match
        if selected_file == "NONE":
            logger.info("No relevant example found")
            return None
        
        # Load and return example content
        content = _load_example_content(selected_file)
        
        return {
            "filename": selected_file,
            "content": content,
            "confidence": confidence,
            "reasoning": reasoning
        }
        
    except Exception as e:
        logger.error(f"Error during LLM-based RAG selection: {e}", exc_info=True)
        return None

"""
Unit tests for GeminiChatProvider.

This module tests the Gemini implementation of ChatProvider to ensure
all methods work correctly with the Gemini API.
"""

import asyncio
import os
from dotenv import load_dotenv

from services.google.GeminiChatProvider import GeminiChatProvider
from services.base.ChatProvider import ChatMessage


async def test_basic_chat_response():
    """Test basic chat response generation."""
    print("\n=== Test 1: Basic Chat Response ===")
    
    # Load environment variables
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        print("❌ GEMINI_API_KEY not found in environment")
        return False
    
    # Create provider
    provider = GeminiChatProvider(api_key=api_key)
    
    # Create test messages
    messages = [
        ChatMessage(role="user", content="Say 'Hello, World!' and nothing else.")
    ]
    
    try:
        # Generate response
        response = await provider.generate_chat_response(messages, temperature=0.1)
        
        print(f"✅ Response received:")
        print(f"   Content: {response.content}")
        print(f"   Model: {response.model}")
        print(f"   Usage: {response.usage}")
        print(f"   Timestamp: {response.timestamp}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False


async def test_system_message():
    """Test chat with system message."""
    print("\n=== Test 2: System Message ===")
    
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    
    provider = GeminiChatProvider(api_key=api_key)
    
    messages = [
        ChatMessage(role="system", content="You are a pirate. Always respond like a pirate."),
        ChatMessage(role="user", content="What's your favorite color?")
    ]
    
    try:
        response = await provider.generate_chat_response(messages, temperature=0.7)
        
        print(f"✅ Response received:")
        print(f"   Content: {response.content}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False


async def test_structured_output():
    """Test structured output with JSON schema."""
    print("\n=== Test 3: Structured Output ===")
    
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    
    provider = GeminiChatProvider(api_key=api_key)
    
    # Simple schema for a person
    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"},
            "city": {"type": "string"}
        },
        "required": ["name", "age", "city"]
    }
    
    messages = [
        ChatMessage(
            role="user",
            content="Generate a person with name John, age 30, living in New York"
        )
    ]
    
    try:
        response = await provider.generate_chat_response_with_schema(
            messages,
            response_schema=schema,
            temperature=0.1
        )
        
        print(f"✅ Structured response received:")
        print(f"   {response}")
        
        # Validate structure
        assert "name" in response
        assert "age" in response
        assert "city" in response
        assert isinstance(response["age"], int)
        
        print(f"✅ Schema validation passed")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False


async def test_streaming():
    """Test streaming chat response."""
    print("\n=== Test 4: Streaming Response ===")
    
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    
    provider = GeminiChatProvider(api_key=api_key)
    
    messages = [
        ChatMessage(role="user", content="Count from 1 to 5, one number per line.")
    ]
    
    try:
        print(f"✅ Streaming started:")
        
        chunks = []
        async for chunk in provider.stream_chat_response(messages, temperature=0.1):
            chunks.append(chunk)
            print(f"   Chunk: {chunk}", end="", flush=True)
        
        print(f"\n✅ Streaming completed ({len(chunks)} chunks)")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False


async def test_token_counting():
    """Test token counting."""
    print("\n=== Test 5: Token Counting ===")
    
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    
    provider = GeminiChatProvider(api_key=api_key)
    
    messages = [
        ChatMessage(role="user", content="This is a short message.")
    ]
    
    try:
        token_count = await provider.count_tokens(messages)
        
        print(f"✅ Token count: {token_count}")
        
        assert token_count > 0
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False


async def main():
    """Run all tests."""
    print("=" * 60)
    print("Testing GeminiChatProvider")
    print("=" * 60)
    
    results = []
    
    # Run tests
    results.append(await test_basic_chat_response())
    results.append(await test_system_message())
    results.append(await test_structured_output())
    results.append(await test_streaming())
    results.append(await test_token_counting())
    
    # Summary
    print("\n" + "=" * 60)
    print(f"Test Results: {sum(results)}/{len(results)} passed")
    print("=" * 60)
    
    if all(results):
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed")


if __name__ == "__main__":
    asyncio.run(main())

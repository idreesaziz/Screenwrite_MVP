#!/bin/bash

# Test script for Agent API endpoint
# Tests POST /api/v1/agent/chat
# Requires valid Supabase credentials to generate JWT token

echo "=================================="
echo "Testing Agent API"
echo "=================================="

# Load environment variables
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/../.env"

if [ ! -f "$ENV_FILE" ]; then
  echo "❌ .env file not found at $ENV_FILE"
  exit 1
fi

SUPABASE_URL=$(grep "^SUPABASE_URL=" "$ENV_FILE" | cut -d '=' -f2 | tr -d '"' | tr -d "'" | xargs)
SUPABASE_ANON_KEY=$(grep "^SUPABASE_ANON_KEY=" "$ENV_FILE" | cut -d '=' -f2 | tr -d '"' | tr -d "'" | xargs)

if [ -z "$SUPABASE_URL" ] || [ -z "$SUPABASE_ANON_KEY" ]; then
  echo "❌ SUPABASE_URL or SUPABASE_ANON_KEY not found in .env"
  exit 1
fi

# Prompt for credentials
echo ""
echo "🔐 Authentication Required"
echo "Please enter your Supabase credentials:"
read -p "Email: " EMAIL
read -sp "Password: " PASSWORD
echo ""

# Authenticate with Supabase to get JWT token
echo ""
echo "⏳ Authenticating with Supabase..."
AUTH_RESPONSE=$(curl -s -X POST "${SUPABASE_URL}/auth/v1/token?grant_type=password" \
  -H "Content-Type: application/json" \
  -H "apikey: ${SUPABASE_ANON_KEY}" \
  -d "{\"email\":\"${EMAIL}\",\"password\":\"${PASSWORD}\"}")

# Extract access token
JWT_TOKEN=$(echo "$AUTH_RESPONSE" | jq -r '.access_token')

if [ "$JWT_TOKEN" == "null" ] || [ -z "$JWT_TOKEN" ]; then
  echo "❌ Authentication failed!"
  ERROR_MSG=$(echo "$AUTH_RESPONSE" | jq -r '.error_description // .message // "Unknown error"')
  echo "Error: $ERROR_MSG"
  exit 1
fi

echo "✅ Authentication successful!"
echo "JWT Token: ${JWT_TOKEN:0:50}..."
echo ""

# Test 1: Simple conversational message
echo ""
echo "Test 1: Simple conversational query"
echo "------------------------------------"

curl -X POST http://localhost:8001/api/v1/agent/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -d '{
    "messages": [
      {
        "id": "msg-1",
        "content": "What can you help me with?",
        "isUser": true,
        "timestamp": "2025-10-11T10:30:00Z"
      }
    ],
    "currentComposition": null,
    "mediaLibrary": [],
    "compositionDuration": null
  }' | jq '.'

echo ""
echo "Test 2: Request with composition context"
echo "-----------------------------------------"

curl -X POST http://localhost:8001/api/v1/agent/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -d '{
    "messages": [
      {
        "id": "msg-1",
        "content": "What'\''s currently on my timeline?",
        "isUser": true,
        "timestamp": "2025-10-11T10:32:00Z"
      }
    ],
    "currentComposition": [
      {
        "clips": [
          {
            "id": "clip-1",
            "startTimeInSeconds": 0,
            "endTimeInSeconds": 5,
            "element": {
              "elements": [
                "AbsoluteFill;id:root;parent:null",
                "h1;id:title;parent:root;text:Hello World"
              ]
            }
          }
        ]
      }
    ],
    "mediaLibrary": [
      {
        "name": "background.mp4",
        "type": "video",
        "duration": 10.5
      }
    ],
    "compositionDuration": 5.0
  }' | jq '.'

echo ""
echo "Test 3: Request to add element"
echo "-------------------------------"

curl -X POST http://localhost:8001/api/v1/agent/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -d '{
    "messages": [
      {
        "id": "msg-1",
        "content": "Add a title that says Welcome at the beginning",
        "isUser": true,
        "timestamp": "2025-10-11T10:35:00Z"
      }
    ],
    "currentComposition": [],
    "mediaLibrary": [],
    "compositionDuration": 0
  }' | jq '.'

echo ""
echo "Test 4: Get agent capabilities"
echo "-------------------------------"

curl -X GET http://localhost:8001/api/v1/agent/capabilities | jq '.'

echo ""
echo "=================================="
echo "Tests completed"
echo "=================================="

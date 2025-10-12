#!/bin/bash

# Test script for Composition Generation API
# Tests POST /api/v1/compositions/generate
# Requires valid Supabase credentials to generate JWT token

echo "=================================="
echo "Testing Composition Generation API"
echo "=================================="

# Load environment variables
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/../.env"

if [ ! -f "$ENV_FILE" ]; then
  echo "❌ .env file not found at $ENV_FILE"
  exit 1
fi

SUPABASE_URL=$(grep SUPABASE_URL "$ENV_FILE" | grep -v "^#" | cut -d '=' -f2 | tr -d '"' | tr -d "'" | xargs)
SUPABASE_ANON_KEY=$(grep SUPABASE_ANON_KEY "$ENV_FILE" | grep -v "^#" | cut -d '=' -f2 | tr -d '"' | tr -d "'" | xargs)

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

# Test 1: Simple composition generation
echo ""
echo "Test 1: Simple composition - 'Create a title saying Hello World'"
echo "-------------------------------------------------------------------"

curl -X POST http://localhost:8001/api/v1/compositions/generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -d '{
    "user_request": "Create a title saying Hello World in white text, centered, 48px font",
    "preview_settings": {
      "width": 1920,
      "height": 1080,
      "fps": 30
    },
    "temperature": 0.1
  }' | jq '.'

echo ""
echo "Test 2: With media library"
echo "--------------------------"

curl -X POST http://localhost:8001/api/v1/compositions/generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -d '{
    "user_request": "Add the sunset video to the timeline",
    "preview_settings": {
      "width": 1920,
      "height": 1080,
      "fps": 30
    },
    "media_library": [
      {
        "id": "video-1",
        "name": "sunset.mp4",
        "mediaType": "video",
        "mediaUrlRemote": "https://example.com/sunset.mp4",
        "durationInSeconds": 10.0,
        "media_width": 1920,
        "media_height": 1080
      }
    ],
    "temperature": 0.1
  }' | jq '.'

echo ""
echo "Test 3: Health check"
echo "--------------------"

curl -X GET http://localhost:8001/api/v1/compositions/health | jq '.'

echo ""
echo "=================================="
echo "Tests completed"
echo "=================================="

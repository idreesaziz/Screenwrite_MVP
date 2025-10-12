#!/bin/bash

# Test script for Media Generation API
# Tests POST /api/v1/media/generate and GET /api/v1/media/status/{operation_id}
# Requires valid Supabase credentials to generate JWT token

echo "=================================="
echo "Testing Media Generation API"
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

# Test 1: Generate an image (sync operation)
echo ""
echo "Test 1: Generate an image with Imagen (16:9 landscape)"
echo "-------------------------------------------------------"

curl -X POST http://localhost:8001/api/v1/media/generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -d '{
    "content_type": "image",
    "prompt": "A serene mountain landscape at sunset with golden light",
    "aspect_ratio": "16:9"
  }' | jq '.'

echo ""
echo ""
echo "Test 2: Generate a square image (1:1)"
echo "--------------------------------------"

curl -X POST http://localhost:8001/api/v1/media/generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -d '{
    "content_type": "image",
    "prompt": "Abstract geometric patterns in vibrant colors",
    "aspect_ratio": "1:1"
  }' | jq '.'

echo ""
echo ""
echo "Test 3: Generate a video with Veo (async operation)"
echo "----------------------------------------------------"

GENERATE_RESPONSE=$(curl -s -X POST http://localhost:8001/api/v1/media/generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -d '{
    "content_type": "video",
    "prompt": "A cat playing with a ball of yarn in slow motion",
    "aspect_ratio": "16:9",
    "resolution": "720p",
    "negative_prompt": "blurry, low quality"
  }')

echo "$GENERATE_RESPONSE" | jq '.'

# Extract operation_id if video generation succeeded
OPERATION_ID=$(echo "$GENERATE_RESPONSE" | jq -r '.operation_id')

if [ "$OPERATION_ID" != "null" ] && [ -n "$OPERATION_ID" ]; then
  echo ""
  echo ""
  echo "Test 4: Check video generation status"
  echo "--------------------------------------"
  echo "Operation ID: $OPERATION_ID"
  echo ""
  echo "Checking status (video generation takes ~2-5 minutes)..."
  
  # Check status once
  curl -X GET "http://localhost:8001/api/v1/media/status/${OPERATION_ID}" \
    -H "Authorization: Bearer $JWT_TOKEN" | jq '.'
  
  echo ""
  echo "ℹ️  To continue checking status, run:"
  echo "curl -X GET \"http://localhost:8001/api/v1/media/status/${OPERATION_ID}\" \\"
  echo "  -H \"Authorization: Bearer $JWT_TOKEN\" | jq '.'"
else
  echo ""
  echo "⚠️  Video generation did not start successfully, skipping status check"
fi

echo ""
echo ""
echo "Test 5: Health check"
echo "--------------------"

curl -X GET http://localhost:8001/api/v1/media/health | jq '.'

echo ""
echo "=================================="
echo "Tests completed"
echo "=================================="
echo ""
echo "Note: Video generation is asynchronous and takes 2-5 minutes."
echo "Poll the status endpoint to check when it's complete."

#!/bin/bash

# Test script for Stock Media API
# Tests POST /api/v1/stock/search
# Requires valid Supabase credentials to generate JWT token

echo "=================================="
echo "Testing Stock Media API"
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

# Test 1: Search for videos
echo ""
echo "Test 1: Search for landscape sunset videos"
echo "-------------------------------------------"

curl -X POST http://localhost:8001/api/v1/stock/search \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -d '{
    "query": "beautiful sunset over the ocean",
    "media_type": "video",
    "orientation": "landscape",
    "max_results": 3,
    "per_page": 30
  }' | jq '.'

echo ""
echo ""
echo "Test 2: Search for portrait images"
echo "-----------------------------------"

curl -X POST http://localhost:8001/api/v1/stock/search \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -d '{
    "query": "professional woman in office",
    "media_type": "image",
    "orientation": "portrait",
    "max_results": 4,
    "per_page": 40
  }' | jq '.'

echo ""
echo ""
echo "Test 3: Search for square images (social media)"
echo "------------------------------------------------"

curl -X POST http://localhost:8001/api/v1/stock/search \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -d '{
    "query": "abstract background geometric patterns",
    "media_type": "image",
    "orientation": "square",
    "max_results": 2,
    "per_page": 20
  }' | jq '.'

echo ""
echo ""
echo "Test 4: Search with defaults (no orientation)"
echo "----------------------------------------------"

curl -X POST http://localhost:8001/api/v1/stock/search \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -d '{
    "query": "mountain landscape nature",
    "media_type": "video",
    "max_results": 2
  }' | jq '.'

echo ""
echo ""
echo "Test 5: Health check"
echo "--------------------"

curl -X GET http://localhost:8001/api/v1/stock/health | jq '.'

echo ""
echo "=================================="
echo "Tests completed"
echo "=================================="

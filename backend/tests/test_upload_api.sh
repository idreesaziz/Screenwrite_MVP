#!/bin/bash

# Test script for Media Upload API
# Tests POST /api/v1/upload/upload
# Requires valid Supabase credentials to generate JWT token

echo "=================================="
echo "Testing Media Upload API"
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

# Create test files
echo "Creating test files..."
echo "This is a test text file" > /tmp/test_upload.txt
echo "Test video content (placeholder)" > /tmp/test_video.mp4

# Test 1: Upload a text file
echo ""
echo "Test 1: Upload a text file"
echo "---------------------------"

curl -X POST http://localhost:8001/api/v1/upload/upload \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -F "file=@/tmp/test_upload.txt" | jq '.'

echo ""
echo ""
echo "Test 2: Upload a video file (placeholder)"
echo "------------------------------------------"

curl -X POST http://localhost:8001/api/v1/upload/upload \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -F "file=@/tmp/test_video.mp4" | jq '.'

echo ""
echo ""
echo "Test 3: Health check"
echo "--------------------"

curl -X GET http://localhost:8001/api/v1/upload/health | jq '.'

# Clean up test files
rm -f /tmp/test_upload.txt /tmp/test_video.mp4

echo ""
echo "=================================="
echo "Tests completed"
echo "=================================="

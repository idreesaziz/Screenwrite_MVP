#!/bin/bash

# Test script for Media Analysis API endpoint
# Tests POST /api/v1/analysis/media
# Requires valid Supabase credentials to generate JWT token

echo "=================================="
echo "Testing Media Analysis API"
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

# Test 1: Analyze a video from GCS
echo ""
echo "Test 1: Analyze video from GCS"
echo "--------------------------------"

curl -X POST http://localhost:8001/api/v1/analysis/media \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -d '{
    "file_url": "gs://cloud-samples-data/generative-ai/video/ad_copy_from_video.mp4",
    "question": "What activities are shown in this video?",
    "model_name": "gemini-2.0-flash-exp",
    "temperature": 0.1
  }' | jq '.'

echo ""
echo "Test 2: Analyze with minimal parameters"
echo "----------------------------------------"

curl -X POST http://localhost:8001/api/v1/analysis/media \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -d '{
    "file_url": "gs://cloud-samples-data/generative-ai/video/ad_copy_from_video.mp4",
    "question": "Describe this video briefly."
  }' | jq '.'

echo ""
echo "Test 3: Test error handling (invalid file)"
echo "-------------------------------------------"

curl -X POST http://localhost:8001/api/v1/analysis/media \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -d '{
    "file_url": "gs://non-existent-bucket/fake.mp4",
    "question": "What is this?"
  }' | jq '.'

echo ""
echo "=================================="
echo "Tests completed"
echo "=================================="

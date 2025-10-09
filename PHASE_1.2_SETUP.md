# Phase 1.2: Backend JWT Verification - Setup Instructions

## Step 1: Get Supabase JWT Secret

1. Go to your Supabase dashboard: https://nabgosryybgihawfpkzg.supabase.co
2. Click on **Settings** (gear icon in sidebar)
3. Go to **API** section
4. Find **JWT Settings**
5. Copy the **JWT Secret** value (it's a long string)

## Step 2: Update Backend .env

Add the JWT secret to `backend/.env`:

```bash
SUPABASE_JWT_SECRET=your-actual-jwt-secret-here
```

## Step 3: Test Authentication

1. **Start the backend** (if not already running):
   ```bash
   cd backend
   uv run python main.py
   ```

2. **Get your JWT token from frontend**:
   - Open browser console on your app (`http://localhost:5173`)
   - Run this in console:
     ```javascript
     const { data } = await window.supabase.auth.getSession()
     console.log(data.session.access_token)
     ```
   - Copy the token that appears

3. **Test the auth endpoint**:
   ```bash
   curl -X GET http://localhost:8001/auth/test \
     -H "Authorization: Bearer YOUR_TOKEN_HERE"
   ```

   Should return:
   ```json
   {
     "success": true,
     "message": "Authentication successful!",
     "user": {
       "user_id": "...",
       "email": "your@email.com",
       "role": "authenticated",
       "session_id": "..."
     }
   }
   ```

4. **Test health endpoint** (no auth required):
   ```bash
   curl http://localhost:8001/health
   ```

   Should return:
   ```json
   {
     "status": "healthy",
     "service": "screenwrite-backend"
   }
   ```

## What We Added:

### Backend Files:
- `backend/auth.py` - JWT verification middleware
  - `verify_jwt()` - Verifies Supabase JWT tokens
  - `get_current_user()` - Extracts user info from token
  - `optional_auth()` - Optional auth for public/private endpoints

### Test Endpoints:
- `GET /auth/test` - Protected endpoint (requires auth)
- `GET /health` - Public endpoint (no auth)

### How to Use in Endpoints:

```python
from auth import get_current_user
from fastapi import Depends

@app.post("/my-protected-endpoint")
async def my_endpoint(
    request: MyRequest,
    user: dict = Depends(get_current_user)  # Add this parameter
):
    # Now you have access to:
    # user["user_id"]
    # user["email"]
    # user["session_id"]
    
    print(f"Request from user: {user['email']}")
    # ... your endpoint logic
```

## Next Steps:

Once authentication is verified:
1. ✅ Phase 1.1: Frontend auth - COMPLETE
2. ✅ Phase 1.2: Backend JWT verification - COMPLETE
3. ⏭️ Phase 2: GCS Integration
   - Create GCS helper functions
   - Update upload endpoints with auth
   - Update stock video endpoint with auth
   - Update generated content endpoint with auth

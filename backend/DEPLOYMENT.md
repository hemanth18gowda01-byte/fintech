# Deployment on Render

## Ready for Render? ✅ YES

Your backend is now **100% ready** for Render deployment. All fixes applied:
- ✅ Added `gunicorn` to `requirements.txt`
- ✅ Removed `debug=True` from production
- ✅ Bound to dynamic `PORT` environment variable
- ✅ All environment variables are properly read from `.env` or Render env vars

## Step-by-step Render deployment

### 1. Push to GitHub

```bash
cd c:/Users/Deepak…/OneDrive/Flask_API
git add backend/
git commit -m "ready for deployment"
git push origin main
```

### 2. Create Render Web Service

1. Go to https://render.com and sign in (use GitHub auth).
2. Click **New → Web Service**.
3. Select your `fintrack` repository and authorize Render.
4. Configure:
   - **Name**: `fintrack-backend`
   - **Region**: (choose closest to you)
   - **Root Directory**: `backend`
   - **Environment**: Python 3
   - **Build command**: `pip install -r requirements.txt`
   - **Start command**: `gunicorn app:app`

### 3. Add Environment Variables
> 📝 **Important**: When you create the Web Service you must either
> set **Root Directory** to `backend` or keep the root but use the
> top‑level `requirements.txt` (it simply pulls in `backend/requirements.txt`).
> If you forget this you will see the error:
> 
> ```
> ERROR: Could not open requirements file: [Errno 2] No such file or directory: 'requirements.txt'
> ```
> 
> Make sure the build command is run in a directory containing
> `requirements.txt` (either the top-level stub or the backend folder).
In the **Environment** section, add these variables:

```
JWT_SECRET_KEY=56c867c8bc47815887438432f87e08461e582fd7a886d69854d6af5f7664b73c516fbf1c52ebd530dc6ed7aac5e6817c36672c57ab19f4360d1467df6f43fa10
FERNET_KEY=Lv24oaXrGe2JacbPl-8Y_JkcFFoH2ks7TQg8JaO4Wcs=
MONGO_URI=mongodb+srv://fintech_user:1HIS80F8Nms471j9@fintechcluster.7yexyva.mongodb.net/expenseDB?retryWrites=true&w=majority
DB_NAME=expenseDB
COLLECTION_NAME=transactions
AI_API_KEY=your-gemini-api-key-from-google-cloud-console
AI_PROVIDER=gemini
AI_ENDPOINT=https://generativemodels.googleapis.com/v1/models/text-bison-001:generate
```

**IMPORTANT - Replace these before deploying**:
- `MONGO_URI`: Replace `YOUR_ATLAS_USERNAME` and `YOUR_ATLAS_PASSWORD` with your MongoDB Atlas credentials (from Atlas dashboard → Users → Database Users)
- `AI_API_KEY`: Replace with your actual Gemini API key from Google Cloud Console

### 4. Deploy

Click **Create Web Service** and wait 2–5 minutes. Render will:
- Pull your code from GitHub
- Install dependencies
- Start the Flask app with Gunicorn

Once live, Render shows your public URL (e.g. `https://fintrack-backend.onrender.com`).

## Testing after deployment

```bash
# Get a JWT via Google login
curl -X POST https://fintrack-backend.onrender.com/login-google \
  -H "Content-Type: application/json" \
  -d '{"id_token":"<valid-google-token>"}'

# Then test transactions endpoint
curl -H "Authorization: Bearer <JWT>" \
  https://fintrack-backend.onrender.com/transactions

# Test AI insights
curl -X POST https://fintrack-backend.onrender.com/ai-insights \
  -H "Authorization: Bearer <JWT>" \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Analyze my spending"}'
```

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Deployment fails | Check Render build logs; look for missing dependency in `requirements.txt` |
| 500 errors in API | Check Render logs; ensure env vars match exactly |
| MongoDB connection fails | Verify `MONGO_URI` format and Atlas whitelist `0.0.0.0/0` |
| No response after 15 mins | Render free tier sleeps; next request wakes it (~30 sec delay) |

## Your backend is production-ready! 🚀

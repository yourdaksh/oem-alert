# 🚀 Deployment Guide - Vulnerability Scrapper

This guide covers deploying your Vulnerability Scrapper application to various platforms.

## ⚠️ Important: Vercel Limitations

**Vercel is NOT recommended for Streamlit apps** because:
- Vercel is designed for serverless functions and static sites
- Streamlit requires a persistent Python server
- Vercel has timeout limits (10s for free tier, 60s for pro)
- Database connections may timeout

## ✅ Recommended Deployment Options

### Option 1: Streamlit Cloud (FREE - Best Choice) ⭐

**Why Streamlit Cloud?**
- ✅ Free tier available
- ✅ Designed specifically for Streamlit apps
- ✅ Easy deployment from GitHub
- ✅ Automatic HTTPS
- ✅ No server management needed

**Steps:**

1. **Push your code to GitHub:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/yourusername/vulnerability-scrapper.git
   git push -u origin main
   ```

2. **Create requirements.txt** (already exists):
   - Make sure all dependencies are listed
   - Streamlit Cloud will install them automatically

3. **Create `.streamlit/config.toml`** (optional):
   ```toml
   [server]
   port = 8501
   enableCORS = false
   enableXsrfProtection = false
   ```

4. **Deploy on Streamlit Cloud:**
   - Go to https://share.streamlit.io/
   - Sign in with GitHub
   - Click "New app"
   - Select your repository
   - Set main file path: `app.py`
   - Add your environment variables (see below)
   - Click "Deploy"

5. **Set Environment Variables in Streamlit Cloud:**
   - Go to your app settings
   - Add all variables from your `.env` file:
     ```
     DATABASE_TYPE=supabase
     SUPABASE_URL=your-url
     SUPABASE_KEY=your-key
     SUPABASE_SERVICE_KEY=your-service-key
     SUPABASE_DB_URL=your-db-url
     EMAIL_USERNAME=your-email
     EMAIL_PASSWORD=your-app-password
     SMTP_SERVER=smtp.gmail.com
     SMTP_PORT=587
     SLACK_ENABLED=false
     SLACK_WEBHOOK_URL=
     ```

**Cost:** FREE

---

### Option 2: Railway.app (Recommended for Production)

**Why Railway?**
- ✅ Easy deployment
- ✅ PostgreSQL database included
- ✅ Free tier with $5 credit/month
- ✅ Automatic HTTPS
- ✅ Good for production apps

**Steps:**

1. **Install Railway CLI:**
   ```bash
   npm i -g @railway/cli
   railway login
   ```

2. **Create `Procfile`:**
   ```
   web: streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
   ```

3. **Deploy:**
   ```bash
   railway init
   railway up
   ```

4. **Set Environment Variables:**
   - Use Railway dashboard or CLI
   - Add all variables from `.env`

**Cost:** Free tier with $5 credit/month, then pay-as-you-go

---

### Option 3: Render.com (Good Free Option)

**Why Render?**
- ✅ Free tier available
- ✅ Easy deployment
- ✅ PostgreSQL database available
- ✅ Automatic HTTPS

**Steps:**

1. **Create `render.yaml`:**
   ```yaml
   services:
     - type: web
       name: vulnerability-scrapper
       env: python
       buildCommand: pip install -r requirements.txt
       startCommand: streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
       envVars:
         - key: DATABASE_TYPE
           value: supabase
         # Add other env vars
   ```

2. **Deploy:**
   - Connect GitHub repository
   - Render will auto-detect and deploy
   - Add environment variables in dashboard

**Cost:** Free tier available, then $7/month for web services

---

### Option 4: Heroku (Classic Option)

**Why Heroku?**
- ✅ Well-established platform
- ✅ Easy deployment
- ✅ PostgreSQL addon available

**Steps:**

1. **Create `Procfile`:**
   ```
   web: streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
   ```

2. **Create `runtime.txt`:**
   ```
   python-3.9.18
   ```

3. **Deploy:**
   ```bash
   heroku create vulnerability-scrapper
   heroku config:set DATABASE_TYPE=supabase
   # Add other env vars
   git push heroku main
   ```

**Cost:** Free tier discontinued, starts at $7/month

---

### Option 5: DigitalOcean App Platform

**Why DigitalOcean?**
- ✅ Good performance
- ✅ PostgreSQL database available
- ✅ Simple pricing

**Steps:**

1. **Create `app.yaml`:**
   ```yaml
   name: vulnerability-scrapper
   services:
     - name: web
       source_dir: /
       github:
         repo: yourusername/vulnerability-scrapper
         branch: main
       run_command: streamlit run app.py --server.port=8080 --server.address=0.0.0.0
       environment_slug: python
       instance_count: 1
       instance_size_slug: basic-xxs
       envs:
         - key: DATABASE_TYPE
           value: supabase
   ```

2. **Deploy via DigitalOcean dashboard**

**Cost:** Starts at $5/month

---

## 🔧 Pre-Deployment Checklist

Before deploying, make sure:

- [ ] All environment variables are documented
- [ ] `.env` file is in `.gitignore` (never commit secrets!)
- [ ] Database is set up (Supabase recommended)
- [ ] Email configuration is working
- [ ] All dependencies are in `requirements.txt`
- [ ] Test the app locally first

---

## 📝 Required Files for Deployment

### 1. `Procfile` (for Railway/Heroku)
```
web: streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
```

### 2. `runtime.txt` (optional, for Heroku)
```
python-3.9.18
```

### 3. `.streamlit/config.toml` (optional)
```toml
[server]
port = 8501
enableCORS = false
enableXsrfProtection = false

[browser]
gatherUsageStats = false
```

### 4. `.gitignore` (make sure this exists!)
```
.env
*.db
*.log
__pycache__/
*.pyc
.venv/
venv/
```

---

## 🔐 Environment Variables to Set

Make sure to set these in your deployment platform:

```bash
# Database
DATABASE_TYPE=supabase
SUPABASE_URL=your-supabase-url
SUPABASE_KEY=your-supabase-key
SUPABASE_SERVICE_KEY=your-service-key
SUPABASE_DB_URL=your-database-url

# Email
EMAIL_USERNAME=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
FROM_EMAIL=your-email@gmail.com

# Slack (optional)
SLACK_ENABLED=false
SLACK_WEBHOOK_URL=
SLACK_DEFAULT_CHANNEL=#vulnerability-alerts

# Streamlit (optional)
STREAMLIT_PAGE_TITLE=Vulnerability Scrapper
```

---

## 🚫 If You Still Want to Try Vercel

While not recommended, if you absolutely want to use Vercel:

1. **Create `api/streamlit.py`:**
   ```python
   import subprocess
   import sys
   
   def handler(request):
       # This won't work well - Streamlit needs persistent server
       subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"])
   ```

2. **Create `vercel.json`:**
   ```json
   {
     "version": 2,
     "builds": [
       {
         "src": "api/streamlit.py",
         "use": "@vercel/python"
       }
     ],
     "routes": [
       {
         "src": "/(.*)",
         "dest": "api/streamlit.py"
       }
     ]
   }
   ```

**⚠️ This will NOT work well** - Streamlit needs a persistent server, and Vercel's serverless functions have timeout limits.

---

## 🎯 My Recommendation

**For your use case, I recommend:**

1. **Streamlit Cloud** (if you want free and easy)
2. **Railway.app** (if you want more control and production-ready)
3. **Render.com** (good middle ground)

All three are much better suited for Streamlit than Vercel.

---

## 📚 Additional Resources

- [Streamlit Cloud Documentation](https://docs.streamlit.io/streamlit-community-cloud)
- [Railway Documentation](https://docs.railway.app/)
- [Render Documentation](https://render.com/docs)

---

## ❓ Need Help?

If you need help with deployment:
1. Choose a platform from above
2. Let me know which one
3. I can help you set it up step-by-step!

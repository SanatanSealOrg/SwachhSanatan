# CleanLoop Deployment Guide - Railway & Vercel

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Prerequisites](#prerequisites)
4. [Railway Backend Deployment](#railway-backend-deployment)
5. [Vercel Frontend Deployment](#vercel-frontend-deployment)
6. [Connecting Backend and Frontend](#connecting-backend-and-frontend)
7. [Testing](#testing)
8. [Troubleshooting](#troubleshooting)
9. [Monitoring and Maintenance](#monitoring-and-maintenance)

---

## Overview

This guide walks you through deploying the CleanLoop application on **Railway** (backend) and **Vercel** (frontend). Both platforms offer free tiers suitable for getting started.

### What We'll Deploy
- **Backend**: FastAPI Python application with PostgreSQL, Redis, and AWS S3 integration
- **Frontend**: React + Vite application (TypeScript)
- **Databases**: Managed PostgreSQL and Redis on Railway
- **Storage**: AWS S3 for image uploads

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│ Users' Devices (Mobile/Desktop)                         │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼ HTTPS
        ┌────────────────────────┐
        │  Vercel Frontend       │
        │  (React + Vite)        │
        │  yourdomain.vercel.app │
        └──────────┬─────────────┘
                   │
                   │ API Calls (/api)
                   ▼
        ┌────────────────────────────────┐
        │  Railway Backend API           │
        │  (FastAPI + Uvicorn)           │
        │  your-backend.railway.app      │
        └──────────┬─────────────────────┘
                   │
        ┌──────────┼──────────┬──────────┐
        ▼          ▼          ▼          ▼
    PostgreSQL  Redis      AWS S3    OpenAI API
    (managed)  (managed)  (external) (external)
```

---

## Prerequisites

Before you begin, make sure you have:

1. **GitHub Account** - Both Railway and Vercel connect to GitHub
2. **Railway Account** - https://railway.app (sign up with GitHub)
3. **Vercel Account** - https://vercel.com (sign up with GitHub)
4. **AWS Account** (for S3 file storage) - https://aws.amazon.com
5. **OpenAI API Key** - https://platform.openai.com/api-keys
6. **Git** - With your CleanLoop repository pushed to GitHub

---

## Railway Backend Deployment

### Step 1: Create a Railway Project

1. Go to https://railway.app
2. Click **"Create" → "Empty Project"** (or link from your GitHub if preferred)
3. Name the project: `cleanloop-backend`

### Step 2: Add PostgreSQL Database

1. In your project, click **"+ New → Database → PostgreSQL"**
2. Wait for it to be provisioned (takes ~1 minute)
3. Click on the PostgreSQL service card
4. Note the **DATABASE_URL** shown in the Variables tab (you'll need this)

Example format:
```
postgresql://user:password@host:port/cleanloop_db
```

### Step 3: Add Redis Cache

1. Click **"+ New → Database → Redis"**
2. Wait for provisioning
3. Copy the **REDIS_URL** from the Variables tab

Example format:
```
redis://user:password@host:port
```

### Step 4: Connect Your GitHub Repository

1. Click **"+ New → GitHub Repo"**
2. Authorize Railway to access your GitHub
3. Select your CleanLoop repository
4. Select the branch (usually `main` or `master`)

### Step 5: Configure Environment Variables

In your Railway project, click on the Python/GitHub service:

1. Go to the **Variables** tab
2. Click **"Raw Editor"**
3. Add these environment variables:

```
# Database & Cache (auto-populated from services above, but confirm these exist)
DATABASE_URL=<auto-populated-from-postgres>
REDIS_URL=<auto-populated-from-redis>

# Security (CHANGE THESE!)
SECRET_KEY=<generate-a-strong-random-string-at-least-32-chars>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# OpenAI Integration
OPENAI_API_KEY=<your-openai-api-key>

# AWS S3 Configuration
AWS_ACCESS_KEY_ID=<your-aws-access-key>
AWS_SECRET_ACCESS_KEY=<your-aws-secret-key>
AWS_S3_BUCKET=cleanloop-images
AWS_S3_REGION=us-east-1
AWS_ENDPOINT_URL=https://s3.amazonaws.com

# Email (optional, for notifications)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=<your-email@gmail.com>
SMTP_PASSWORD=<your-app-password>

# CORS Configuration (update after Vercel deployment)
ALLOWED_ORIGINS=https://yourdomain.vercel.app,https://www.yourdomain.vercel.app

# App Configuration
APP_NAME=CleanLoop
APP_ENV=production
DEBUG=False
LOG_LEVEL=INFO

# Timezone
TIMEZONE=Asia/Kolkata
```

### Step 6: Generate SECRET_KEY

Run this in your terminal to generate a secure key:

```bash
# On Windows PowerShell:
[Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes((Get-Random -SetSeed 0 -Count 32 | % { [char](32..126 | Get-Random) }))) -join ''

# Or on macOS/Linux:
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Or simply use:
openssl rand -base64 32
```

### Step 7: Deploy

1. Make sure your `Procfile` exists in the root directory (we created it earlier)
2. Railway auto-detects the Procfile and Python dependencies
3. Watch the **Deployments** tab for build progress
4. Once deployed successfully, you'll see a **Public URL** (e.g., `https://cleanloop-api.up.railway.app`)

### Step 8: Verify Backend is Running

```bash
curl https://your-backend-url.railway.app/health
# Should return: {"status":"ok","service":"cleanloop-api"}
```

**Save this URL** — you'll need it for the frontend deployment!

---

## Vercel Frontend Deployment

### Step 1: Create a Vercel Project

1. Go to https://vercel.com
2. Click **"Add New → Project"**
3. Select your CleanLoop GitHub repository
4. Click **"Import"**

### Step 2: Configure Build Settings

Vercel should auto-detect the settings, but verify:

- **Framework Preset**: Vite
- **Root Directory**: `frontend` (or set explicitly if not auto-detected)
- **Build Command**: `npm run build`
- **Output Directory**: `dist`
- **Install Command**: `npm install`

### Step 3: Set Environment Variables

Before deployment, set the frontend environment variables:

1. In Vercel project settings, go to **Settings → Environment Variables**
2. Add:

```
Name: VITE_API_URL
Value: https://your-backend.railway.app/api
Environments: Production, Preview, Development
```

Replace `your-backend.railway.app` with your actual Railway backend URL.

### Step 4: Deploy

1. Click **"Deploy"**
2. Watch the build progress
3. Once complete, you'll get a **Production URL** (e.g., `https://cleanloop.vercel.app`)

### Step 5: Verify Frontend is Running

1. Open the Vercel URL in your browser
2. You should see the CleanLoop login page
3. Check browser console (F12) for any errors

**Note**: There may be CORS errors if the ALLOWED_ORIGINS on Railway hasn't been updated yet.

---

## Connecting Backend and Frontend

### Step 1: Update Railway CORS Configuration

Now that you have the Vercel frontend URL, update Railway:

1. Go to your Railway project
2. Click on the Python service
3. Go to **Variables** tab
4. Update `ALLOWED_ORIGINS`:

```
ALLOWED_ORIGINS=https://your-frontend.vercel.app,https://www.your-frontend.vercel.app
```

5. Click **"Redeploy"** to apply the change

### Step 2: Verify Connection

1. Open your frontend URL in a browser
2. Go to the **Login** page
3. Try logging in with a test account
4. Check browser Network tab (F12) to see if `/api` calls are succeeding
5. You should see 2xx responses, not 4xx or 5xx errors

---

## Testing

### Test 1: Health Check
```bash
curl https://your-backend.railway.app/health
# Expected: {"status":"ok","service":"cleanloop-api"}
```

### Test 2: API Documentation
Visit: `https://your-backend.railway.app/docs`
You should see Swagger UI with all API endpoints documented.

### Test 3: User Registration & Login
1. Open the frontend URL
2. Register a new account
3. Log in with those credentials
4. Navigate to different pages (Dashboard, Report, etc.)

### Test 4: File Upload (if applicable)
1. Go to "Report" page
2. Try uploading a photo
3. Check that it uploads successfully
4. Verify the file appears in AWS S3

### Test 5: API from Different Device
1. Share your frontend URL with someone else
2. Ask them to access it from their phone/device
3. They should see the same application (no localhost restrictions)

---

## Troubleshooting

### Issue: CORS Errors in Browser Console

**Error**: `Access to XMLHttpRequest has been blocked by CORS policy`

**Solution**:
1. Check that `ALLOWED_ORIGINS` in Railway includes your Vercel frontend URL
2. Ensure no trailing slashes in the ALLOWED_ORIGINS list
3. Railway may need to be redeployed after changing ALLOWED_ORIGINS

### Issue: Frontend Can't Find Backend

**Error**: `Failed to fetch from /api` or `Network Error`

**Solution**:
1. Verify `VITE_API_URL` is set correctly in Vercel environment variables
2. Check that the Railway backend URL is accessible: `curl https://your-backend.railway.app/health`
3. Confirm backend is running (check Railway Deployments tab)

### Issue: Database Connection Error

**Error**: `could not connect to server: Connection refused`

**Solution**:
1. Verify `DATABASE_URL` is set in Railway variables
2. Check that PostgreSQL service is running (green status in Railway)
3. Try redeploying the Python service

### Issue: 502 Bad Gateway from Railway

**Solution**:
1. Check Railway logs (click service → Logs tab)
2. Look for Python errors (import errors, missing packages)
3. Verify `requirements.txt` includes all dependencies
4. Restart the service: Click service → More options → Redeploy

### Issue: Frontend Build Fails on Vercel

**Error**: `Build failed` with TypeScript errors

**Solution**:
1. Check Vercel build logs
2. Run locally: `cd frontend && npm run build` to see the error
3. Fix the TypeScript error
4. Push to GitHub (auto-redeploy)

---

## Monitoring and Maintenance

### Daily Monitoring

1. **Check Railway Deployments**: https://railway.app/project/xxx/deployments
2. **Check Vercel Deployments**: https://vercel.com/dashboard
3. **Monitor API Usage**: Railway shows request metrics

### Weekly Tasks

- Review error logs in Railway (Logs tab)
- Check AWS S3 storage usage (may incur charges)
- Test user flows on production

### Security Reminders

- **Never commit `.env` files** to GitHub
- **Rotate `SECRET_KEY`** periodically (requires Railway redeploy)
- **Keep dependencies updated** (check for security vulnerabilities)
- **Monitor AWS S3 costs** (watch for unexpected charges)

### Scaling (When You Grow)

- **Railway**: Upgrade to paid plan for more resources
- **Vercel**: Auto-scales based on traffic (no changes needed)
- **Database**: Railway PostgreSQL free tier supports ~100K rows
- **S3 Storage**: AWS free tier includes 5GB; costs ~$0.023/GB after

### Logging & Debugging

**View Backend Logs**:
```bash
# In Railway UI:
1. Select Python service
2. Click "Logs" tab
3. Filter by date/service
```

**View Frontend Logs**:
```bash
# In Vercel UI:
1. Go to Deployments tab
2. Click on a deployment
3. Click "Runtime Logs"
```

---

## Rollback Procedures

### Rollback Backend Deployment

1. Go to Railway → Deployments tab
2. Find a previous successful deployment
3. Click the deployment
4. Click "Rollback to this Deployment"

### Rollback Frontend Deployment

1. Go to Vercel → Deployments tab
2. Find a previous working deployment
3. Click "..." menu
4. Select "Promote to Production"

---

## Cost Breakdown (As of 2024)

| Service | Free Tier | Typical Monthly Cost |
|---------|-----------|---------------------|
| Railway Backend | $5 credit/month | $0-$10 |
| PostgreSQL on Railway | Included | $0-$15 (if exceeds free tier) |
| Redis on Railway | Included | $0-$10 (if exceeds free tier) |
| Vercel Frontend | Full free tier | $0 (no charges for simple apps) |
| AWS S3 | 5GB + 20K GET/PUT | $0-$5 (after free tier) |
| OpenAI API | Pay as you use | $0-$50 (depends on usage) |
| **TOTAL** | | **$0-$90/month** |

---

## Support & Next Steps

### Getting Help
- **Railway Issues**: https://railway.app/docs/troubleshooting
- **Vercel Issues**: https://vercel.com/docs
- **FastAPI Issues**: https://fastapi.tiangolo.com
- **React/Vite Issues**: https://vitejs.dev

### Next Steps After Deployment
1. ✅ Share the frontend URL with users
2. ✅ Monitor error logs daily
3. ✅ Set up automated alerts (optional)
4. ✅ Plan for scaling as user base grows
5. ✅ Consider custom domain setup

---

**Last Updated**: 2024
**CleanLoop Version**: 0.1.0

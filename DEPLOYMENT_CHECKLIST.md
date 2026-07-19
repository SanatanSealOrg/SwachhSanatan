# RAILWAY & VERCEL DEPLOYMENT CHECKLIST

## PHASE 1: PREPARE (Already Done ✓)
- [✓] Created Procfile for Railway
- [✓] Created railway.json configuration
- [✓] Created vercel.json configuration
- [✓] Created frontend/.env.production
- [✓] Created frontend/.env.development
- [✓] Updated frontend/src/api.ts for environment variables
- [✓] Updated backend_main.py for better CORS handling
- [✓] Created comprehensive DEPLOYMENT_GUIDE.md

## PHASE 2: COMMIT TO GITHUB
- [ ] Open terminal/PowerShell in project root
- [ ] Run: git add .
- [ ] Run: git commit -m "Add Railway & Vercel deployment configuration"
- [ ] Run: git push origin main (or master)
- [ ] Verify files appear on GitHub

## PHASE 3: RAILWAY BACKEND DEPLOYMENT
- [ ] Create Railway account at https://railway.app
- [ ] Click "Create" → "Empty Project"
- [ ] Name it "cleanloop-backend"
- [ ] Add PostgreSQL database
  - [ ] Wait for provisioning
  - [ ] Copy DATABASE_URL from Variables tab
- [ ] Add Redis database
  - [ ] Wait for provisioning
  - [ ] Copy REDIS_URL from Variables tab
- [ ] Connect GitHub repository
  - [ ] Click "+ New" → "GitHub Repo"
  - [ ] Authorize Railway to access GitHub
  - [ ] Select your CleanLoop repository
  - [ ] Select main/master branch
- [ ] Configure Environment Variables
  - [ ] Go to Python service Variables tab
  - [ ] Add DATABASE_URL (auto-populated)
  - [ ] Add REDIS_URL (auto-populated)
  - [ ] Add SECRET_KEY (generate random 32+ char string)
  - [ ] Add OPENAI_API_KEY
  - [ ] Add AWS_ACCESS_KEY_ID
  - [ ] Add AWS_SECRET_ACCESS_KEY
  - [ ] Add AWS_S3_BUCKET=cleanloop-images
  - [ ] Add AWS_S3_REGION=us-east-1
  - [ ] Add AWS_ENDPOINT_URL=https://s3.amazonaws.com
  - [ ] Add ALLOWED_ORIGINS=http://localhost:3000 (update later)
  - [ ] Add APP_ENV=production
  - [ ] Add DEBUG=False
- [ ] Railway auto-detects Procfile and deploys
- [ ] Wait for successful deployment (watch Deployments tab)
- [ ] Copy your backend URL (e.g., https://cleanloop-api.railway.app)
- [ ] Test: curl https://your-url.railway.app/health
- [ ] Should return: {"status":"ok","service":"cleanloop-api"}

## PHASE 4: VERCEL FRONTEND DEPLOYMENT
- [ ] Create Vercel account at https://vercel.com
- [ ] Click "Add New" → "Project"
- [ ] Select your CleanLoop GitHub repository
- [ ] Click "Import"
- [ ] Verify build settings:
  - [ ] Framework: Vite
  - [ ] Root Directory: frontend
  - [ ] Build Command: npm run build
  - [ ] Output Directory: dist
- [ ] Add Environment Variable:
  - [ ] Name: VITE_API_URL
  - [ ] Value: https://YOUR_RAILWAY_BACKEND_URL/api (replace YOUR_RAILWAY_BACKEND_URL)
  - [ ] Apply to: Production, Preview, Development
- [ ] Click "Deploy"
- [ ] Wait for build to complete
- [ ] Copy your frontend URL (e.g., https://cleanloop.vercel.app)
- [ ] Test: Open URL in browser, should see login page

## PHASE 5: CONNECT SERVICES
- [ ] Go back to Railway dashboard
- [ ] Select Python service
- [ ] Go to Variables tab
- [ ] Update ALLOWED_ORIGINS:
  - [ ] Old: http://localhost:3000
  - [ ] New: https://your-vercel-url.vercel.app,https://www.your-vercel-url.vercel.app
- [ ] Click "Save" and "Redeploy"
- [ ] Wait for backend to redeploy

## PHASE 6: TESTING
- [ ] Test 1: Health check
  - [ ] Run: curl https://your-backend-url/health
  - [ ] Should return OK status
- [ ] Test 2: API Docs
  - [ ] Open: https://your-backend-url/docs
  - [ ] Should see Swagger UI with all endpoints
- [ ] Test 3: Frontend loads
  - [ ] Open frontend URL in browser
  - [ ] Should see CleanLoop login page
  - [ ] No CORS errors in browser console (F12)
- [ ] Test 4: User registration
  - [ ] Register new test account
  - [ ] Login with test credentials
  - [ ] Navigate to different pages
- [ ] Test 5: File upload (if applicable)
  - [ ] Go to Report page
  - [ ] Upload test image
  - [ ] Should upload successfully
- [ ] Test 6: From different device
  - [ ] Share frontend URL with someone
  - [ ] They should access from their phone/device
  - [ ] Should work without localhost restrictions

## PHASE 7: PRODUCTION READY
- [ ] All tests passed
- [ ] No errors in logs
- [ ] Database has initial data (test users, etc.)
- [ ] AWS S3 credentials verified
- [ ] OpenAI API key working
- [ ] Email/SMTP configured (if needed)
- [ ] Backup plan documented

## PHASE 8: LAUNCH
- [ ] Share frontend URL with users
- [ ] Document URL in README or project page
- [ ] Monitor logs daily for errors
- [ ] Set up alerts (optional)
- [ ] Plan for scaling as needed

---

TROUBLESHOOTING QUICK LINKS:
- See DEPLOYMENT_GUIDE.md for detailed troubleshooting
- Railway issues: https://railway.app/docs
- Vercel issues: https://vercel.com/docs
- Common issues:
  * CORS errors → Update ALLOWED_ORIGINS in Railway
  * Backend not found → Check VITE_API_URL in Vercel
  * Database error → Check DATABASE_URL in Railway
  * Build fails → Check build logs in Vercel

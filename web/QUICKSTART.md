# Quick Start Guide - StudyNet Scraper Frontend

## 🚀 Complete Setup (4 steps)

### Step 1: Start the Backend API Server

**Important:** You must start the backend first!

From the project root directory:

```bash
python -m src.main api
```

You should see output like:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
```

The API will be available at `http://localhost:8000`
- API docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

**Keep this terminal window open** - the backend needs to keep running!

### Step 2: Install Frontend Dependencies

Open a **new terminal window** and navigate to the web directory:

```bash
cd web
npm install
```

### Step 3: Start Frontend Development Server

Still in the `web` directory:

```bash
npm run dev
```

You should see:
```
  VITE v5.0.8  ready in 500 ms

  ➜  Local:   http://localhost:3000/
```

### Step 4: Open Browser

Navigate to: **http://localhost:3000**

🎉 You should now see the StudyNet Scraper interface!

## 📋 Quick Checklist

- ✅ Backend running on port 8000 (`python -m src.main api`)
- ✅ Frontend dependencies installed (`npm install`)
- ✅ Frontend dev server running (`npm run dev`)
- ✅ Browser opened to http://localhost:3000

## 🔄 Running Both Servers

You need **two terminal windows**:

**Terminal 1 - Backend:**
```bash
# In project root
python -m src.main api
```

**Terminal 2 - Frontend:**
```bash
# In web directory
cd web
npm run dev
```

## 🆘 Troubleshooting

### "Failed to fetch" or Connection Errors

**Problem:** Backend not running  
**Solution:** Make sure you started the backend with `python -m src.main api` in a separate terminal

### Backend Won't Start

**Problem:** Port 8000 already in use  
**Solution:** 
- Stop the process using port 8000, or
- Use a different port: `python -m src.main api --port 8001`
- Update API_URL in components to match (or use the proxy in vite.config.ts)

### Frontend Can't Connect to Backend

**Check:**
1. Backend is running: Visit http://localhost:8000/health
2. CORS is enabled in backend (should be automatic)
3. API URL is correct (components use `http://localhost:8000`)

### Port 3000 Already in Use (Frontend)

```bash
npm run dev -- --port 3001
```

## 📚 More Information

- **Full Setup Guide**: See [SETUP.md](./SETUP.md)
- **Detailed Documentation**: See [README.md](./README.md)
- **API Documentation**: http://localhost:8000/docs (when backend is running)

## ✨ What You'll See

1. **Infinite Grid Background** - Animated grid that responds to mouse movement
2. **Navigation Header** - Switch between "New Job" and "Dashboard" views
3. **Theme Toggle** - Dark/light mode switcher (top right)
4. **New Job Form** - Submit scraping jobs with configuration options
5. **Dashboard** - View all jobs with real-time status updates (auto-refreshes every 5 seconds)

---

**Need Help?** Check the troubleshooting section or review the main project README.

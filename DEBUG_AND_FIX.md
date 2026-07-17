# 🔧 Complete Debugging & Troubleshooting Guide

> **URGENT FIX GUIDE** - Follow these steps to get the project working immediately

---

## ⚡ QUICK START (3 Minutes)

### **Step 1: Check if Backend is Running**
```bash
# Test backend
curl http://127.0.0.1:8000

# Expected: {"status":"online",...}
```

### **Step 2: Check if Frontend is Running**
```bash
# Open in browser
http://localhost:3000
```

### **Step 3: Test API Connection**
In browser console (Press F12), run:
```javascript
fetch('/api/').then(r => r.json()).then(console.log)
```

---

## 🚨 CRITICAL ISSUES & FIXES

### **❌ Problem: "Cannot GET localhost:3000"**

**Root Causes:**
1. Frontend not running
2. Frontend stuck/crashed
3. Port 3000 already in use

**FIX:**
```bash
# 1. Kill any process on port 3000
# Windows:
netstat -ano | findstr :3000
taskkill /PID <PID> /F

# Mac/Linux:
lsof -ti:3000 | xargs kill -9

# 2. Clear npm cache and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install

# 3. Start fresh
npm run dev
```

**Expected Output:**
```
VITE v8.1.1  ready in 123 ms

➜  Local:   http://localhost:3000/
```

---

### **❌ Problem: "API Error: Backend offline"**

**Root Causes:**
1. Backend not running
2. Backend crashed
3. Port 8000 already in use
4. CORS not configured

**FIX:**

```bash
# 1. Kill process on port 8000
# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Mac/Linux:
lsof -ti:8000 | xargs kill -9

# 2. Install dependencies
cd backend
pip install -r requirements.txt

# 3. Add missing import to main.py (if needed)
# Add this line at top of backend/app/main.py:
# import pandas as pd

# 4. Start backend
python run_backend.py
```

**Expected Output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete
```

---

### **❌ Problem: Frontend Shows Blank/Black Page**

**Root Causes:**
1. JavaScript errors
2. CSS not loading
3. React not mounted

**FIX:**

```bash
# 1. Check browser console for errors (F12)

# 2. Verify HTML file has root div
# Check: frontend/index.html line 13
# Should have: <div id="root"></div>

# 3. Check main.jsx is correct
# frontend/src/main.jsx should have valid React setup

# 4. Rebuild frontend
cd frontend
npm run build
npm run dev
```

**Verify in browser console (F12):**
```javascript
// Should not show errors
document.getElementById('root')  // Should return <div>
```

---

### **❌ Problem: "Cannot POST /api/upload"**

**Root Causes:**
1. Backend routes not defined
2. CORS blocked
3. API proxy not working

**FIX:**

**In frontend/vite.config.js:**
```javascript
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        rewrite: (path) => path  // Important for proper routing
      }
    }
  }
})
```

**In backend/app/main.py:**
Verify CORS middleware is at the top:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Then restart both services.

---

### **❌ Problem: Missing Module - "No module named 'pandas'"**

**FIX:**
```bash
# Reinstall all dependencies
cd backend
pip uninstall -r requirements.txt -y
pip install -r requirements.txt

# Verify pandas installed
python -c "import pandas; print(pandas.__version__)"
```

---

### **❌ Problem: "Ollama not responding" / "No insights generated"**

**Root Causes:**
1. Ollama not running
2. Ollama port (11434) not accessible
3. Llama3 model not downloaded

**FIX:**

```bash
# 1. Start Ollama service (in new terminal)
ollama serve

# 2. In another terminal, download Llama3
ollama pull llama3

# 3. Verify Ollama is accessible
curl http://localhost:11434/api/tags

# Expected response:
# {"models":[{"name":"llama3:latest",...}]}

# 4. Check backend logs for Ollama connection
python run_backend.py
# Should show: "✅ Ollama engine available"
```

**If Ollama still fails:**
```bash
# Fallback will use heuristic engine (still generates insights)
# Check logs - should say: "✅ Using heuristic engine"
```

---

## 🧪 TESTING EACH COMPONENT

### **Test 1: Backend Health**
```bash
# Run from terminal
curl http://127.0.0.1:8000

# Expected response:
# {"status":"online","message":"API running","aws_connected":false}
```

### **Test 2: Frontend Loads**
```bash
# Open in browser
http://localhost:3000

# Check: Page should show dark dashboard with upload button
```

### **Test 3: API Proxy Works**
In browser console (F12):
```javascript
fetch('/api/').then(r => r.json()).then(console.log)

// Should print backend response to console
```

### **Test 4: File Upload**
```bash
# Create sample CSV
cd backend
cat > test_data.csv << 'EOF'
Date,Channel,Spend,Impressions,Clicks,Conversions,Revenue
2026-06-01,Google Ads,500,10000,250,25,1250
2026-06-02,Google Ads,550,11000,275,28,1400
EOF

# Test upload via Python
python << 'EOF'
import requests
import json

with open('test_data.csv', 'rb') as f:
    files = {'file': f}
    res = requests.post('http://127.0.0.1:8000/api/upload', files=files)
    print(json.dumps(res.json(), indent=2))
EOF
```

---

## 🐛 COMMON ERRORS & SOLUTIONS

| Error | Cause | Solution |
|-------|-------|----------|
| `ModuleNotFoundError: No module named 'fastapi'` | Missing dependencies | `pip install -r requirements.txt` |
| `Address already in use` | Port conflict | Kill process: `lsof -ti:8000 \| xargs kill -9` |
| `Cannot connect to Docker daemon` | Docker not running | Start Docker Desktop |
| `uvicorn: command not found` | uvicorn not installed | `pip install uvicorn` |
| `ERR_INVALID_HTTP_RESPONSE` | Backend crashed | Check logs, restart |
| `CORS error in browser console` | CORS not configured | Add CORS middleware to FastAPI |
| `GET http://localhost:3000/api/ 404` | API proxy broken | Fix vite.config.js proxy |
| `Uncaught TypeError: Cannot read property 'map'` | API returns wrong format | Check backend response structure |

---

## 🔍 DEBUGGING STEPS (Use This When Stuck)

### **Step 1: Check All Services Running**
```bash
# Backend
curl http://127.0.0.1:8000

# Frontend (open browser)
http://localhost:3000

# Ollama (optional)
curl http://localhost:11434/api/tags
```

### **Step 2: Check Logs**

**Backend logs:**
```bash
# Terminal where you ran: python run_backend.py
# Should show:
# INFO:     Uvicorn running on http://127.0.0.1:8000
# INFO:     Application startup complete
```

**Frontend logs:**
```bash
# Terminal where you ran: npm run dev
# Should show:
# ➜  Local: http://localhost:3000/
```

**Browser console (F12):**
```
- Should NOT have red errors
- May have yellow warnings (ok)
```

### **Step 3: Test API Response**

```bash
# In backend terminal, make a test request:
python -c "
import requests
import json

try:
    res = requests.get('http://127.0.0.1:8000')
    print('✅ Backend responding')
    print(json.dumps(res.json(), indent=2))
except Exception as e:
    print(f'❌ Backend error: {e}')
"
```

### **Step 4: Check Browser Console**

Press **F12** → Console tab:
```javascript
// Check if fetch works
fetch('/api/').then(r => r.json()).then(d => {
  console.log('✅ API Response:', d)
}).catch(e => console.error('❌ Error:', e))
```

---

## 🚀 FULL RESTART (Nuclear Option)

If everything is broken, do this:

```bash
# 1. Kill all services
# Windows:
taskkill /F /IM python.exe
taskkill /F /IM node.exe
taskkill /F /IM ollama.exe

# Mac/Linux:
pkill -f "python run_backend"
pkill -f "npm run dev"
pkill -f "ollama serve"

# 2. Clean up
cd frontend
rm -rf node_modules package-lock.json dist
cd ../backend
rm -rf __pycache__ .pytest_cache venv

# 3. Fresh install
cd backend
pip install --upgrade pip
pip install -r requirements.txt

cd ../frontend
npm install

# 4. Start fresh (3 different terminals)

# Terminal 1 - Ollama (optional)
ollama serve

# Terminal 2 - Backend
cd backend
python run_backend.py

# Terminal 3 - Frontend
cd frontend
npm run dev

# 5. Test in browser
# http://localhost:3000
```

---

## ✅ SUCCESS CHECKLIST

- [ ] Backend running: `curl http://127.0.0.1:8000` returns JSON
- [ ] Frontend running: `http://localhost:3000` shows dark dashboard
- [ ] API proxy works: Browser console shows no CORS errors
- [ ] Can upload CSV: File upload button works
- [ ] Can generate forecast: Forecast tab shows data
- [ ] Ollama running (optional): `curl http://localhost:11434/api/tags` works
- [ ] Can get insights: "Get Insights" button returns AI text

---

## 📊 EXPECTED BEHAVIOR

### **On Startup:**
```
[Backend] ✅ Uvicorn running on http://127.0.0.1:8000
[Frontend] ✅ Local: http://localhost:3000
[Ollama]   ✅ Ollama engine available (if running)
```

### **In Browser:**
1. Page loads with dark theme
2. Upload tab shows file input
3. No red errors in console
4. API calls succeed (check Network tab)

### **After Upload:**
1. CSV preview shows in dashboard
2. Forecast tab shows charts
3. Insights button works
4. Chat responds to messages

---

## 🆘 STILL STUCK?

**Provide this information:**

1. **Your OS**: Windows/Mac/Linux?
2. **Python version**: `python --version`
3. **Node version**: `node --version`
4. **Backend logs**: Full output from `python run_backend.py`
5. **Frontend logs**: Full output from `npm run dev`
6. **Browser console**: Screenshot of F12 console (any red errors?)
7. **Network tab**: What's the response to `/api/` request?

---

## 📞 QUICK REFERENCE COMMANDS

```bash
# Start Backend
cd backend && python run_backend.py

# Start Frontend
cd frontend && npm run dev

# Start Ollama
ollama serve

# Download Llama3
ollama pull llama3

# Kill port 3000
lsof -ti:3000 | xargs kill -9  # Mac/Linux
netstat -ano | findstr :3000 && taskkill /PID <PID> /F  # Windows

# Kill port 8000
lsof -ti:8000 | xargs kill -9  # Mac/Linux
netstat -ano | findstr :8000 && taskkill /PID <PID> /F  # Windows

# Test backend
curl http://127.0.0.1:8000

# Test Ollama
curl http://localhost:11434/api/tags

# Check what's running
ps aux | grep -E 'python|node|ollama'  # Mac/Linux
tasklist | findstr /I "python node ollama"  # Windows
```

---

**🎯 Goal: Get all 3 services running, then test in browser at http://localhost:3000**

**🚀 You got this! Follow the quick start above first.**

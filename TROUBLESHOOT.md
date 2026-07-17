# 🔧 Troubleshooting Guide - Forecast AI

## ❌ Error: "Connection refused"

**Cause**: Services are not running

**Solution**:
```bash
# Windows
start.bat

# Mac/Linux
bash start.sh
```

---

## ❌ Error: "Docker not found"

**Cause**: Docker is not installed

**Solution**:
1. Download Docker Desktop: https://www.docker.com/products/docker-desktop
2. Install and restart terminal
3. Run `docker --version` to verify

---

## ❌ Error: "Port 3000/8000 already in use"

**Cause**: Another service is using the port

**Solution**:
```bash
# Kill process on port 3000
kill -9 $(lsof -ti:3000)  # Mac/Linux
taskkill /PID $(netstat -ano | findstr :3000 | findstr LISTENING | awk '{print $5}') /F  # Windows

# Then restart
start.bat  # or bash start.sh
```

---

## ❌ Error: "Cannot find module 'pandas'"

**Cause**: Python dependencies not installed

**Solution**: Docker handles this automatically. If issue persists:
```bash
docker-compose down
docker system prune -a
docker-compose up --build
```

---

## ❌ Error: "Ollama not responding"

**Cause**: Ollama container failed to start

**Solution**:
```bash
# Check logs
docker logs forecast-ai-ollama

# Restart only Ollama
docker-compose restart ollama
```

---

## ❌ Error: "npm install fails"

**Cause**: Node dependencies issue

**Solution**:
```bash
# Clean and rebuild
docker-compose down
docker volume prune
docker-compose up --build
```

---

## ✅ Verify Everything is Working

```bash
# Check all services running
docker ps

# Should show 3 containers:
# - forecast-ai-ollama
# - forecast-ai-backend
# - forecast-ai-frontend
```

### Test each endpoint:

```bash
# Test Ollama
curl http://localhost:11434/api/tags

# Test Backend
curl http://127.0.0.1:8000

# Test Frontend (open in browser)
http://localhost:3000
```

---

## 🎯 If Everything Fails

**Nuclear option** (removes all containers & volumes):
```bash
docker-compose down -v
docker system prune -a --volumes
docker-compose up --build
```

Then wait 2-3 minutes for all services to start.

---

## 📞 Common Issues & Fixes

| Issue | Fix |
|-------|-----|
| Services hang on startup | Wait 2-3 minutes, Ollama downloads model on first run |
| Frontend shows blank page | Check browser console (F12), check backend is running |
| Upload CSV fails | Check backend logs: `docker logs forecast-ai-backend` |
| "Get Insights" returns error | Ollama may still be starting, wait 1 minute |
| Port already in use | Close other apps using ports 3000, 8000, 11434 |

---

## 🆘 Still Having Issues?

1. Share output of: `docker ps`
2. Share output of: `docker logs forecast-ai-backend`
3. Share output of: `docker logs forecast-ai-ollama`
4. Let me know your OS (Windows/Mac/Linux)

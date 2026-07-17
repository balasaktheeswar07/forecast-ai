# Forecast AI: Complete AI-Powered Marketing Forecasting Platform

> **AI Forecasting Assistant for Digital Marketing Agencies** - Predict campaign performance, simulate budgets, and generate strategic insights using **100% free local Ollama LLM**

## 🎯 What It Does

Upload your ad campaign data → Get AI-powered forecasts → Receive strategic recommendations → Optimize budget allocation

All with **zero API costs** using local Ollama Llama 3 model running on your machine.

---

## 📊 Complete System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     FORECAST AI DASHBOARD                        │
│  (React + Vite - http://localhost:3000)                         │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │   Upload     │  │  Forecast    │  │  Simulator   │           │
│  │   Campaign   │  │  & Charts    │  │  & Budget    │           │
│  │   CSV Data   │  │              │  │  Optimizer   │           │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘           │
│         │                 │                 │                    │
│  ┌──────────────────────────────────────┐  │                    │
│  │      AI INSIGHTS & CHATBOT            │  │                    │
│  │  (Strategic Recommendations)          │  │                    │
│  │  (AI-Generated Reports)               │  │                    │
│  └──────────────────────────────────────┘  │                    │
└────────────────┬─────────────────────────────┼────────────────────┘
                 │                             │
                 ▼                             ▼
        ┌─────────────────────────────────────────────┐
        │    FastAPI Backend Server (Port 8000)       │
        │    http://127.0.0.1:8000                    │
        │                                             │
        │  ┌─────────────────────────────────────┐   │
        │  │  1. Data Upload & Validation        │   │
        │  │     - CSV parsing                   │   │
        │  │     - Feature engineering           │   │
        │  │     - Data cleaning                 │   │
        │  └─────────────────────────────────────┘   │
        │                    ▼                         │
        │  ┌─────────────────────────────────────┐   │
        │  │  2. ML Forecasting Engine           │   │
        │  │     - Random Forest per channel     │   │
        │  │     - Confidence intervals (95%)    │   │
        │  │     - 30-day horizon forecast       │   │
        │  └─────────────────────────────────────┘   │
        │                    ▼                         │
        │  ┌─────────────────────────────────────┐   │
        │  │  3. Budget Simulation & Optimization│   │
        │  │     - Saturation curve fitting      │   │
        │  │     - Lagrange multiplier optimizer │   │
        │  │     - ROI maximization              │   │
        │  └─────────────────────────────────────┘   │
        │                    ▼                         │
        │  ┌─────────────────────────────────────┐   │
        │  │  4. 🤖 LLM INSIGHT GENERATION 🤖   │   │
        │  │     ┌─────────────────────────────┐ │   │
        │  │     │  LLM Orchestrator           │ │   │
        │  │     │                             │ │   │
        │  │     │ 1️⃣  Try Ollama (LOCAL)     │ │   │
        │  │     │     ✅ FASTEST              │ │   │
        │  │     │     ✅ FREE                 │ │   │
        │  │     │     ✅ OFFLINE              │ │   │
        │  │     │     ✅ NO API KEY           │ │   │
        │  │     │                             │ │   │
        │  │     │ 2️⃣  Fallback: HuggingFace  │ │   │
        │  │     │ 3️⃣  Fallback: Gemini API   │ │   │
        │  │     │ 4️⃣  Fallback: Heuristics   │ │   │
        │  │     └─────────────────────────────┘ │   │
        │  │                                     │   │
        │  │  Generates:                         │   │
        │  │  📈 Executive Summary               │   │
        │  │  🔍 Platform Performance Analysis   │   │
        │  │  ⚠️  Risk & Saturation Assessment  │   │
        │  │  🚀 Strategic Action Plan           │   │
        │  └─────────────────────────────────────┘   │
        │                    ▼                         │
        │  ┌─────────────────────────────────────┐   │
        │  │  5. Report Generation & Export      │   │
        │  │     - PDF reports (ReportLab)       │   │
        │  │     - S3/Local storage              │   │
        │  │     - Download links                │   │
        │  └─────────────────────────────────────┘   │
        └─────────────────────────────────────────────┘
                 ▲                             ▲
                 │                             │
        ┌────────────────────────┬──────────────────────┐
        │                        │                      │
        ▼                        ▼                      ▼
    ┌─────────┐            ┌──────────┐         ┌─────────────┐
    │ Ollama  │            │   S3/    │         │  DynamoDB   │
    │ Llama 3 │            │  Local   │         │  Metadata   │
    │         │            │  Storage │         │  Store      │
    │ Running │            │          │         │  (Optional) │
    │ Locally │            │  CSV &   │         │             │
    │ 🚀      │            │  Reports │         │             │
    └─────────┘            └──────────┘         └─────────────┘
```

---

## 🏗️ Project Structure

```
forecast-ai/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI server & routes
│   │   ├── llm_engine.py           # 🤖 Ollama + LLM orchestrator
│   │   ├── ai_engine.py            # Strategic insights generation
│   │   ├── forecasting.py          # Random Forest forecasting
│   │   ├── simulation.py           # Budget simulation & optimization
│   │   ├── data_processing.py      # CSV validation & cleaning
│   │   ├── reports.py              # PDF report generation
│   │   └── aws_client.py           # S3/DynamoDB integration
│   ├── run_backend.py              # Backend entry point
│   └── requirements.txt            # Python dependencies
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx                 # Main React component
│   │   ├── pages/
│   │   │   ├── Upload.jsx          # Data upload interface
│   │   │   ├── Forecast.jsx        # Forecast visualization
│   │   │   ├── Simulator.jsx       # Budget simulator
│   │   │   ├── Insights.jsx        # 🤖 AI insights display
│   │   │   └── Chat.jsx            # AI chatbot interface
│   │   └── components/
│   │       ├── Charts.jsx          # Recharts visualizations
│   │       └── Dashboard.jsx       # Dashboard layout
│   ├── package.json
│   └── vite.config.js
│
├── OLLAMA_SETUP.md                 # Quick start guide
├── README.md                        # This file
└── sample_data.csv                 # Example campaign data
```

---

## ⚙️ Tech Stack

### **Frontend**
- **React 19** - UI components
- **Vite** - Lightning-fast build tool
- **Tailwind CSS v4** - Styling
- **Recharts** - Interactive forecasting charts
- **Lucide Icons** - Beautiful icons

### **Backend API**
- **FastAPI** - High-performance Python API
- **Uvicorn** - ASGI server
- **Mangum** - AWS Lambda adapter
- **pandas & NumPy** - Data processing
- **scikit-learn** - Random Forest forecasting

### **🤖 AI/ML Engines**
- **Ollama** - Local Llama 3 LLM (PRIMARY)
- **HuggingFace Transformers** - Optional local LLM
- **Google Generative AI** - Optional fallback API
- **Heuristic Engine** - Hardcoded intelligence fallback

### **Cloud Services (Optional)**
- **AWS S3** - File storage
- **AWS DynamoDB** - Metadata store
- **LocalStack** - Local AWS emulation

---

## 🚀 Getting Started

### **Prerequisites**
- Python 3.12+
- Node.js 18+ & npm
- **Ollama** installed from https://ollama.ai

### **1. Setup Ollama (One-time)**
```bash
# Download and install from https://ollama.ai

# Start Ollama service (keep running)
ollama serve

# In new terminal, download Llama 3 model (first time only)
ollama pull llama3
```

### **2. Install Backend**
```bash
cd backend
pip install -r requirements.txt
python run_backend.py
```
✅ Backend runs on http://127.0.0.1:8000

### **3. Install Frontend**
```bash
cd frontend
npm install
npm run dev
```
✅ Dashboard runs on http://localhost:3000

---

## 🎯 Usage Flow

### **Step 1: Upload Campaign Data**
```csv
Date,Channel,Spend,Impressions,Clicks,Conversions,Revenue
2026-06-01,Google Ads,500,10000,250,25,1250
2026-06-01,Meta Ads,300,8000,160,12,840
2026-06-01,LinkedIn Ads,200,3000,60,3,450
...
```

Click **"Upload Data"** → App validates CSV → Stores in database

### **Step 2: Generate AI Forecast**
Click **"Generate Forecast"** → FastAPI:
1. Loads your historical data
2. Trains Random Forest models per channel
3. Forecasts next 30 days with 95% confidence intervals
4. Returns metrics & confidence bands

### **Step 3: View AI-Generated Insights** 🤖
Click **"Get Insights"** → Backend:
1. **Detects Ollama** running on localhost:11434
2. **Sends forecast data** to Ollama Llama 3 model
3. **Llama 3 generates** strategic recommendations
4. **Displays insights** in dashboard:
   ```
   ## 📈 Executive Summary
   The campaign forecast indicates improving trends...
   
   ## 🔍 Platform Insights
   Google Ads (3.2x ROAS): Highly efficient...
   Meta Ads (2.1x ROAS): Moderately efficient...
   
   ## ⚠️ Risk Assessment
   Saturation detected in high-spend channels...
   
   ## 🚀 Strategic Action Plan
   1. Shift 15% budget from Meta to Google
   2. Implement CPA caps on underperformers...
   ```

### **Step 4: Run Budget Simulations**
Adjust channel budgets with sliders → Lagrange multiplier optimization → View projected ROI improvements

### **Step 5: Chat with AI Assistant** 💬
Ask natural questions:
- "How should I allocate my $50,000 budget?"
- "Which channel has best efficiency?"
- "What's next month's ROAS forecast?"

AI responds with data-backed recommendations.

### **Step 6: Generate & Download Reports**
Click **"Generate Report"** → Creates PDF with:
- Forecast charts
- AI insights
- Recommendations
- Budget allocations

---

## 📡 API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/upload` | POST | Upload campaign CSV |
| `/api/forecast` | POST | Generate 30-day forecast |
| `/api/simulate` | POST | Simulate budget changes |
| `/api/optimize` | POST | Optimize budget allocation |
| `/api/insights` | POST | 🤖 Generate AI insights (Ollama) |
| `/api/chat` | POST | Chat with AI assistant |
| `/api/generate-report` | POST | Generate PDF report |

---

## 🤖 How Ollama Integration Works

```python
# In backend/app/ai_engine.py
from .llm_engine import LLMOrchestrator

llm_orchestrator = LLMOrchestrator()

def generate_strategic_insights(forecast_data, simulation_data):
    # Automatically routes to best available LLM
    insights = llm_orchestrator.generate_strategic_insights(
        forecast_data, 
        simulation_data
    )
    return insights
```

**Priority Order:**
1. ✅ **Ollama (Llama 3)** - Local, instant, zero cost
2. 🟡 **HuggingFace** - Local, slower without GPU
3. 🔵 **Gemini API** - Free tier, 60 req/min limit
4. ⚫ **Heuristics** - Always works, data-driven fallback

---

## 💰 Cost Analysis

| Component | Cost | Notes |
|-----------|------|-------|
| **Ollama Llama 3** | **$0** | ✅ Free, local, offline |
| **FastAPI** | **$0** | Open source |
| **React** | **$0** | Open source |
| **AWS (optional)** | $0-50/mo | Only if using cloud storage |
| **Total** | **$0** | 🎉 Completely free! |

---

## 📈 Real Example

**Input CSV (Campaign Data):**
```
Date,Channel,Spend,Conversions,Revenue
2026-06-01,Google Ads,1000,50,3500
2026-06-02,Google Ads,1100,52,3640
2026-06-03,Google Ads,950,45,3325
...
```

**Dashboard Output:**
```
Forecast (Next 30 days):
- Google Ads Projected Spend: $31,500
- Google Ads Projected Revenue: $110,250
- Google Ads Projected ROAS: 3.5x
```

**AI Insights (from Ollama):**
```
## 🚀 Strategic Action Plan

Google Ads (ROAS: 3.5x) is your top performer.
Recommendation: Increase budget by 25% to capture 
additional market share. CPC is stable at $12.50.

Meta Ads (ROAS: 1.8x) is underperforming.
Recommendation: Reduce budget by 10%, focus on 
creative testing to improve CTR from 2.1% to 3%.
```

---

## 🔧 Configuration

### **Change Ollama Model**
Edit `backend/app/llm_engine.py`:
```python
# Use Mistral instead of Llama 3 (faster, lighter)
ollama_engine = OllamaLLMEngine(model="mistral")

# Or Neural Chat
ollama_engine = OllamaLLMEngine(model="neural-chat")
```

### **Adjust Forecast Horizon**
Default is 30 days. In dashboard, change to 14, 60, 90 days.

### **Use Gemini API (Optional)**
```bash
export GEMINI_API_KEY="your-api-key"
python run_backend.py
```

---

## 📚 Learn More

- [Ollama Documentation](https://ollama.ai)
- [FastAPI Docs](https://fastapi.tiangolo.com)
- [React Documentation](https://react.dev)
- [scikit-learn Random Forest](https://scikit-learn.org/stable/modules/ensemble.html#random-forests)

---

## 🎓 Next Steps

- ✅ **Deploy to Production**: Docker + AWS Lambda
- ✅ **Add More Channels**: TikTok, Pinterest, programmatic
- ✅ **Fine-tune Ollama**: Train on your client data
- ✅ **Mobile App**: React Native version
- ✅ **Team Collaboration**: Multi-user support

---

## 📞 Support

For issues:
1. Check `OLLAMA_SETUP.md` for quick troubleshooting
2. Review backend logs: `python run_backend.py`
3. Verify Ollama: `curl http://localhost:11434/api/tags`
4. Check frontend: Open DevTools (F12) → Console

---

**Built with ❤️ for digital marketing agencies**

🚀 **Zero API costs • 100% offline • AI-powered forecasting**

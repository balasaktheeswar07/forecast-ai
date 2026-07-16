# Forecast AI: AI Forecasting Assistant for Digital Marketing Agencies

Forecast AI is a serverless, cloud-native web application built for digital marketing agencies to predict campaign performance, run budget simulations, and receive strategic marketing recommendations driven by AI.

## Project Architecture & Tech Stack

### 1. Frontend:
- **React (Vite)**
- **Tailwind CSS v4** (Utility styling and dark cyberpunk aesthetics)
- **Recharts** (Interactive forecasting charts, confidence bands, allocation doughnut)
- **Lucide Icons**

### 2. Backend API:
- **FastAPI** (Python backend)
- **Mangum** (AWS Lambda wrapper for serverless API Gateway deployment)
- **scikit-learn** (Random Forest regressor with tree-variance uncertainty bounds for forecasting)
- **Lagrange Multipliers** (Closed-form water-filling algorithm to optimize budgets across channels)
- **ReportLab** (Structured corporate PDF report builder)

### 3. Serverless Cloud Services (AWS / LocalStack):
- **Amazon S3**: Stores raw/processed campaign CSVs and generated reports.
- **Amazon DynamoDB**: Key-value metastore for campaign diagnostics and metadata.
- **Fallback Engine**: Automatic local directory JSON/file system fallback if S3/DynamoDB are offline.

---

## Getting Started

### Prerequisites
1. **Python 3.12+**
2. **Node.js 18+ & npm**
3. **AWS CLI** (Optional, for deploying to LocalStack or AWS)

### 1. Running the Backend Server
First, navigate to the backend directory, install python packages, and start the development server:
```bash
cd backend
python -m pip install -r requirements.txt
python run_backend.py
```
The server starts at `http://127.0.0.1:8000`.

### 2. Bootstrapping AWS / LocalStack (Optional)
If Docker and LocalStack are running on your machine on port `4566`, you can bootstrap the cloud environment using the provided PowerShell script:
```powershell
cd backend
powershell -File deploy.ps1
```
This automatically initializes the S3 buckets (`forecast-ai-datasets`, `forecast-ai-reports`) and the DynamoDB table (`forecast-ai-campaigns`). If LocalStack is not active, the backend server will automatically fallback to storing files in the local `backend/data/` folder.

### 3. Running the React Frontend
Navigate to the frontend directory, install npm modules, and start Vite:
```bash
cd frontend
npm install
npm run dev
```
The frontend starts at `http://localhost:3000` (which automatically proxies `/api` calls to the backend on `8000`).

---

## Upload Data Format
Uploaded files must be CSV format and contain the following headers:
- `Date` (Format: `YYYY-MM-DD`)
- `Channel` (e.g. `Google Ads`, `Meta Ads`, `LinkedIn Ads`, `TikTok Ads`)
- `Spend` (in dollars)
- `Impressions`
- `Clicks`
- `Conversions`
- `Revenue` (in dollars)

*Tip: A "Generate Sample CSV" button is provided directly on the Upload page of the dashboard to generate realistic marketing agency data for testing!*

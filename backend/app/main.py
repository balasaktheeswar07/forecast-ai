import os
import uuid
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from mangum import Mangum
import pandas as pd

from .aws_client import (
    init_resources,
    check_aws_connection,
    get_dynamodb_resource,
    CAMPAIGNS_TABLE
)
from .data_processing import (
    validate_and_clean_csv,
    engineer_features,
    save_dataframe_to_s3_or_local,
    load_dataframe_from_s3_or_local
)
from .forecasting import train_and_forecast
from .simulation import (
    fit_saturation_curves,
    simulate_scenario,
    optimize_budget_allocation
)
from .ai_engine import (
    generate_strategic_insights,
    simulated_chatbot_response
)
from .reports import generate_pdf_report, save_report_and_get_url

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("forecast-ai-main")

app = FastAPI(title="AI Forecasting Assistant API")

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mangum Handler for AWS Lambda deployment
handler = Mangum(app)

# Local campaigns metastore path (for local fallback)
LOCAL_CAMPAIGNS_JSON = os.path.join("data", "campaigns.json")

# In-memory session store for current data to avoid S3 calls on every slider move
_session_data_store: Dict[str, Any] = {}

def get_campaign_metadata(campaign_id: str) -> dict:
    """Reads campaign metadata from DynamoDB or local JSON."""
    if check_aws_connection():
        db = get_dynamodb_resource()
        table = db.Table(CAMPAIGNS_TABLE)
        try:
            response = table.get_item(Key={"campaign_id": campaign_id})
            if "Item" in response:
                return response["Item"]
        except Exception as e:
            logger.error(f"Failed to read from DynamoDB: {e}")
            
    # Fallback/Local read
    if os.path.exists(LOCAL_CAMPAIGNS_JSON):
        with open(LOCAL_CAMPAIGNS_JSON, "r", encoding="utf-8") as f:
            campaigns = json.load(f)
            return campaigns.get(campaign_id, {})
    return {}

def save_campaign_metadata(campaign_id: str, metadata: dict):
    """Saves campaign metadata to DynamoDB or local JSON."""
    metadata = {**metadata, "campaign_id": campaign_id, "updated_at": datetime.now().isoformat()}
    
    if check_aws_connection():
        db = get_dynamodb_resource()
        table = db.Table(CAMPAIGNS_TABLE)
        try:
            table.put_item(Item=metadata)
            return
        except Exception as e:
            logger.error(f"Failed to write to DynamoDB: {e}. Saving locally.")
            
    # Fallback/Local write
    os.makedirs("data", exist_ok=True)
    campaigns = {}
    if os.path.exists(LOCAL_CAMPAIGNS_JSON):
        try:
            with open(LOCAL_CAMPAIGNS_JSON, "r", encoding="utf-8") as f:
                campaigns = json.load(f)
        except Exception:
            pass
            
    campaigns[campaign_id] = metadata
    with open(LOCAL_CAMPAIGNS_JSON, "w", encoding="utf-8") as f:
        json.dump(campaigns, f, indent=2)

@app.on_event("startup")
async def startup_event():
    """Run resource bootstrap on startup."""
    init_resources()

@app.get("/")
def read_root():
    return {
        "status": "online",
        "message": "AI Forecasting Assistant Serverless API is running.",
        "aws_connected": check_aws_connection()
    }

@app.post("/api/upload")
async def upload_dataset(file: UploadFile = File(...)):
    """
    Accepts CSV, validates columns, cleans data, performs feature engineering,
    saves the dataset and registers campaign metadata.
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted.")
        
    try:
        content_bytes = await file.read()
        # Clean and validate
        df_clean, cleaning_logs = validate_and_clean_csv(content_bytes)
        
        # Feature engineering
        df_featured = engineer_features(df_clean)
        
        # Save to storage (S3 / Local)
        campaign_id = str(uuid.uuid4())
        filename = f"{campaign_id}.csv"
        saved_path = save_dataframe_to_s3_or_local(df_featured, filename)
        
        # Keep in-memory cache for speed
        _session_data_store[campaign_id] = df_featured
        
        # Calculate high-level summary
        channels = df_featured["Channel"].unique().tolist()
        total_spend = float(df_featured["Spend"].sum())
        total_revenue = float(df_featured["Revenue"].sum())
        total_conversions = float(df_featured["Conversions"].sum())
        overall_roas = total_revenue / total_spend if total_spend > 0 else 0.0
        
        summary = {
            "total_spend": total_spend,
            "total_revenue": total_revenue,
            "total_conversions": total_conversions,
            "overall_roas": overall_roas,
            "channels_count": len(channels)
        }
        
        # Save Metadata
        metadata = {
            "filename": file.filename,
            "storage_path": saved_path,
            "channels": channels,
            "summary": summary
        }
        save_campaign_metadata(campaign_id, metadata)
        
        # Take a 15-row preview to return
        preview_data = df_featured.head(15).to_dict(orient="records")
        # Format dates for JSON response
        for item in preview_data:
            if isinstance(item["Date"], datetime) or hasattr(item["Date"], "strftime"):
                item["Date"] = item["Date"].strftime("%Y-%m-%d")
                
        return {
            "campaign_id": campaign_id,
            "filename": file.filename,
            "summary": summary,
            "channels": channels,
            "cleaning_logs": cleaning_logs,
            "preview": preview_data
        }
        
    except ValueError as val_err:
        logger.error(f"Validation error: {val_err}")
        raise HTTPException(status_code=400, detail=str(val_err))
    except Exception as e:
        logger.error(f"Internal error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

class ForecastRequest(BaseModel):
    campaign_id: str
    horizon_days: Optional[int] = 30
    confidence_level: Optional[float] = 0.95

@app.post("/api/forecast")
def generate_forecast(req: ForecastRequest):
    """
    Fits time-series regression and generates performance forecasts.
    """
    campaign_id = req.campaign_id
    
    # Load DataFrame
    df = _session_data_store.get(campaign_id)
    if df is None:
        meta = get_campaign_metadata(campaign_id)
        if not meta:
            raise HTTPException(status_code=404, detail="Campaign not found.")
        try:
            filename = f"{campaign_id}.csv"
            df = load_dataframe_from_s3_or_local(filename)
            # Ensure Date column is cast to datetime
            df["Date"] = pd.to_datetime(df["Date"])
            _session_data_store[campaign_id] = df
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to load dataset: {e}")
            
    # Run Forecast Engine
    try:
        final_df = train_and_forecast(df, horizon_days=req.horizon_days, confidence_level=req.confidence_level)
        
        # Convert df to JSON list
        records = final_df.to_dict(orient="records")
        for item in records:
            if hasattr(item["Date"], "strftime"):
                item["Date"] = item["Date"].strftime("%Y-%m-%d")
                
        # Calculate projected metrics
        forecast_only = final_df[final_df["IsForecast"] == True]
        proj_spend = float(forecast_only["Spend"].sum())
        proj_revenue = float(forecast_only["Revenue"].sum())
        proj_conversions = float(forecast_only["Conversions"].sum())
        proj_roas = proj_revenue / proj_spend if proj_spend > 0 else 0.0
        
        # Historical stats (last 30 days of actuals)
        actuals_only = final_df[final_df["IsForecast"] == False].sort_values("Date")
        # Grab last 30 distinct dates
        last_30_dates = actuals_only["Date"].unique()[-30:]
        hist_subset = actuals_only[actuals_only["Date"].isin(last_30_dates)]
        hist_spend = float(hist_subset["Spend"].sum())
        hist_revenue = float(hist_subset["Revenue"].sum())
        hist_conversions = float(hist_subset["Conversions"].sum())
        hist_roas = hist_revenue / hist_spend if hist_spend > 0 else 0.0
        
        return {
            "metrics": records,
            "summary": {
                "historical_spend": hist_spend,
                "historical_revenue": hist_revenue,
                "historical_conversions": hist_conversions,
                "historical_roas": hist_roas,
                "projected_spend": proj_spend,
                "projected_revenue": proj_revenue,
                "projected_conversions": proj_conversions,
                "projected_roas": proj_roas
            }
        }
    except Exception as e:
        logger.error(f"Forecasting error: {e}")
        raise HTTPException(status_code=500, detail=f"Forecasting failed: {str(e)}")

class SimulateRequest(BaseModel):
    campaign_id: str
    budgets: Dict[str, float]

@app.post("/api/simulate")
def run_simulation(req: SimulateRequest):
    """
    Recalculates metrics for target channels using diminishing returns curves.
    """
    campaign_id = req.campaign_id
    
    # Load DataFrame
    df = _session_data_store.get(campaign_id)
    if df is None:
        meta = get_campaign_metadata(campaign_id)
        if not meta:
            raise HTTPException(status_code=404, detail="Campaign not found.")
        try:
            df = load_dataframe_from_s3_or_local(f"{campaign_id}.csv")
            df["Date"] = pd.to_datetime(df["Date"])
            _session_data_store[campaign_id] = df
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to load dataset: {e}")
            
    try:
        # Fit curves
        curves = fit_saturation_curves(df)
        
        # Simulate budget changes
        simulation_res = simulate_scenario(curves, req.budgets)
        
        # Calculate baseline (historical daily averages)
        baseline = {}
        for ch, c in curves.items():
            baseline[ch] = {
                "Spend": c["avg_spend"],
                "Conversions": c["avg_conversions"],
                "Revenue": c["avg_revenue"],
                "ROAS": c["avg_revenue"] / c["avg_spend"] if c["avg_spend"] > 0 else 0.0
            }
        
        total_base_spend = sum(c["avg_spend"] for c in curves.values())
        total_base_rev = sum(c["avg_revenue"] for c in curves.values())
        
        return {
            "simulation": simulation_res,
            "baseline": {
                "channels": baseline,
                "summary": {
                    "TotalSpend": total_base_spend,
                    "TotalRevenue": total_base_rev,
                    "TotalROAS": total_base_rev / total_base_spend if total_base_spend > 0 else 0.0
                }
            }
        }
    except Exception as e:
        logger.error(f"Simulation error: {e}")
        raise HTTPException(status_code=500, detail=f"Simulation failed: {str(e)}")

class OptimizeRequest(BaseModel):
    campaign_id: str
    total_daily_budget: float

@app.post("/api/optimize")
def run_optimization(req: OptimizeRequest):
    """
    Optimizes the budget allocation using Lagrange multipliers.
    """
    campaign_id = req.campaign_id
    
    # Load DataFrame
    df = _session_data_store.get(campaign_id)
    if df is None:
        meta = get_campaign_metadata(campaign_id)
        if not meta:
            raise HTTPException(status_code=404, detail="Campaign not found.")
        try:
            df = load_dataframe_from_s3_or_local(f"{campaign_id}.csv")
            df["Date"] = pd.to_datetime(df["Date"])
            _session_data_store[campaign_id] = df
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to load dataset: {e}")
            
    try:
        curves = fit_saturation_curves(df)
        optimal_allocations = optimize_budget_allocation(curves, req.total_daily_budget)
        
        # Run simulator on these optimal allocations
        sim_res = simulate_scenario(curves, optimal_allocations)
        
        return {
            "allocations": optimal_allocations,
            "projected_metrics": sim_res
        }
    except Exception as e:
        logger.error(f"Optimization error: {e}")
        raise HTTPException(status_code=500, detail=f"Optimization failed: {str(e)}")

class InsightRequest(BaseModel):
    campaign_id: str
    forecast_summary: dict
    simulation_summary: Optional[dict] = None
    gemini_key: Optional[str] = None

@app.post("/api/insights")
def get_insights(req: InsightRequest, api_key_header: Optional[str] = Header(None, alias="X-Gemini-Key")):
    """
    Generates dynamic strategic marketing insights.
    """
    # Use headers key or body key
    gemini_key = req.gemini_key or api_key_header
    
    try:
        insights = generate_strategic_insights(
            req.forecast_summary, 
            req.simulation_summary, 
            api_key=gemini_key
        )
        return {"insights": insights}
    except Exception as e:
        logger.error(f"Insights error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate insights: {str(e)}")

class ChatRequest(BaseModel):
    campaign_id: str
    message: str
    campaign_summary: dict

@app.post("/api/chat")
def chatbot_message(req: ChatRequest):
    """
    Generates automated interactive advisory responses.
    """
    try:
        response = simulated_chatbot_response(req.message, req.campaign_summary)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class ReportRequest(BaseModel):
    campaign_id: str
    forecast_summary: dict
    insights: str

@app.post("/api/generate-report")
def generate_report(req: ReportRequest):
    """
    Generates a PDF report, uploads to cloud (S3) or local files, 
    and returns secure download link.
    """
    try:
        # Build PDF stream
        pdf_stream = generate_pdf_report(req.forecast_summary, req.insights)
        
        # Save and return link
        filename = f"forecast_report_{req.campaign_id}_{uuid.uuid4().hex[:6]}.pdf"
        download_url = save_report_and_get_url(pdf_stream, filename)
        
        return {"report_url": download_url}
    except Exception as e:
        logger.error(f"Report generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")

@app.get("/api/download-report/{filename}")
def download_local_report(filename: str):
    """
    Serves generated reports locally in fallback mode.
    """
    local_path = os.path.join("data", "reports", filename)
    if os.path.exists(local_path):
        return FileResponse(
            path=local_path,
            filename=filename,
            media_type="application/pdf"
        )
    raise HTTPException(status_code=404, detail="Report file not found.")

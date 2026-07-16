import requests
import os
import sys

# Configure target server
BASE_URL = "http://127.0.0.1:8000"

print("=============================================")
print("Starting Programmatic Backend API Verification")
print(f"Target API Server: {BASE_URL}")
print("=============================================")

# 1. Check Root Endpoint
try:
    res = requests.get(f"{BASE_URL}/")
    res.raise_for_status()
    print(f"[OK] Root Endpoint response: {res.json()}")
except Exception as e:
    print(f"[ERROR] Could not connect to API server: {e}")
    sys.exit(1)

# Paths
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
csv_path = os.path.join(project_root, "sample_data.csv")

if not os.path.exists(csv_path):
    print(f"[ERROR] Test CSV file not found at {csv_path}")
    sys.exit(1)

# 2. Upload CSV Dataset
print("\n[TEST] Uploading sample CSV dataset...")
campaign_id = None
summary = None
try:
    with open(csv_path, "rb") as f:
        files = {"file": (os.path.basename(csv_path), f, "text/csv")}
        res = requests.post(f"{BASE_URL}/api/upload", files=files)
        res.raise_for_status()
        data = res.json()
        campaign_id = data["campaign_id"]
        summary = data["summary"]
        print(f"[OK] Upload successful! Campaign ID: {campaign_id}")
        print(f"     Metrics Summary: {summary}")
        print(f"     Active Channels: {data['channels']}")
        print(f"     Cleaning Logs Count: {len(data['cleaning_logs'])}")
except Exception as e:
    print(f"[ERROR] Upload endpoint failed: {e}")
    sys.exit(1)

# 3. Generate Forecasts
print("\n[TEST] Generating 30-day forecast projections...")
forecast_summary = None
try:
    payload = {
        "campaign_id": campaign_id,
        "horizon_days": 30,
        "confidence_level": 0.95
    }
    res = requests.post(f"{BASE_URL}/api/forecast", json=payload)
    res.raise_for_status()
    data = res.json()
    forecast_summary = data["summary"]
    print(f"[OK] Forecasting successful!")
    print(f"     Hist vs Proj Revenue: ${forecast_summary['historical_revenue']:,.2f} -> ${forecast_summary['projected_revenue']:,.2f}")
    print(f"     Hist vs Proj ROAS: {forecast_summary['historical_roas']:.2f}x -> {forecast_summary['projected_roas']:.2f}x")
except Exception as e:
    print(f"[ERROR] Forecast endpoint failed: {e}")
    sys.exit(1)

# 4. Scenario Simulation
print("\n[TEST] Simulating custom budget scenario...")
try:
    # Set custom daily budgets
    budgets = {"Google Ads": 200.0, "Meta Ads": 300.0}
    payload = {
        "campaign_id": campaign_id,
        "budgets": budgets
    }
    res = requests.post(f"{BASE_URL}/api/simulate", json=payload)
    res.raise_for_status()
    data = res.json()
    sim_summary = data["simulation"]["summary"]
    print(f"[OK] Simulation successful!")
    print(f"     Simulated Total Spend: ${sim_summary['TotalSpend']:,.2f}")
    print(f"     Simulated Expected Revenue: ${sim_summary['TotalRevenue']:,.2f}")
    print(f"     Simulated Expected ROAS: {sim_summary['TotalROAS']:.2f}x")
except Exception as e:
    print(f"[ERROR] Simulation endpoint failed: {e}")
    sys.exit(1)

# 5. Budget Optimizer
print("\n[TEST] Running Lagrange budget optimizer...")
try:
    payload = {
        "campaign_id": campaign_id,
        "total_daily_budget": 500.0
    }
    res = requests.post(f"{BASE_URL}/api/optimize", json=payload)
    res.raise_for_status()
    data = res.json()
    print(f"[OK] Budget Optimization successful!")
    print(f"     Optimized Allocations: {data['allocations']}")
    print(f"     Projected Optimizer Revenue: ${data['projected_metrics']['summary']['TotalRevenue']:,.2f}")
except Exception as e:
    print(f"[ERROR] Optimization endpoint failed: {e}")
    sys.exit(1)


# 6. Strategic Insights (Heuristics Fallback)
print("\n[TEST] Generating AI Strategic Recommendations (Fallback)...")
insights_text = None
try:
    payload = {
        "campaign_id": campaign_id,
        "forecast_summary": {
            "historical_roas": forecast_summary["historical_roas"],
            "projected_roas": forecast_summary["projected_roas"],
            "historical_revenue": forecast_summary["historical_revenue"],
            "projected_revenue": forecast_summary["projected_revenue"],
            "historical_spend": forecast_summary["historical_spend"],
            "projected_spend": forecast_summary["projected_spend"],
            "channels": {
                "Google Ads": {"roas": 4.0, "spend": 1500, "revenue": 6000, "cpa": 31.25, "cpc": 1.25, "conv_rate": 0.04},
                "Meta Ads": {"roas": 2.75, "spend": 2000, "revenue": 5500, "cpa": 31.75, "cpc": 1.11, "conv_rate": 0.035}
            }
        }
    }
    res = requests.post(f"{BASE_URL}/api/insights", json=payload)
    res.raise_for_status()
    data = res.json()
    insights_text = data["insights"]
    print("[OK] Insights generated successfully!")
    print("----- Insights Preview -----")
    # Encode to ascii replacing unsupported emojis to avoid Windows terminal charmap crashes
    safe_preview = insights_text[:300].encode('ascii', errors='replace').decode('ascii')
    print(safe_preview + "...")
    print("----------------------------")
except Exception as e:
    print(f"[ERROR] Insights endpoint failed: {e}")
    sys.exit(1)


# 7. AI Chat Advisor
print("\n[TEST] Testing AI Chat Assistant query...")
try:
    payload = {
        "campaign_id": campaign_id,
        "message": "Which channel should I invest in?",
        "campaign_summary": {
            "historical_roas": forecast_summary["historical_roas"],
            "projected_roas": forecast_summary["projected_roas"],
            "projected_revenue": forecast_summary["projected_revenue"],
            "channels": {"Google Ads": {"roas": 4.0}, "Meta Ads": {"roas": 2.7}}
        }
    }
    res = requests.post(f"{BASE_URL}/api/chat", json=payload)
    res.raise_for_status()
    data = res.json()
    print(f"[OK] Chat Response: '{data['response']}'")
except Exception as e:
    print(f"[ERROR] Chat endpoint failed: {e}")
    sys.exit(1)

# 8. Report Generator
print("\n[TEST] Testing PDF Report Builder...")
try:
    payload = {
        "campaign_id": campaign_id,
        "forecast_summary": {
            "historical_revenue": forecast_summary["historical_revenue"],
            "projected_revenue": forecast_summary["projected_revenue"],
            "historical_roas": forecast_summary["historical_roas"],
            "projected_roas": forecast_summary["projected_roas"],
            "channels": {
                "Google Ads": {"spend": 1500, "impressions": 30000, "clicks": 1200, "conversions": 48, "revenue": 6000, "roas": 4.0},
                "Meta Ads": {"spend": 2000, "impressions": 50000, "clicks": 1800, "conversions": 63, "revenue": 5500, "roas": 2.75}
            }
        },
        "insights": insights_text
    }
    res = requests.post(f"{BASE_URL}/api/generate-report", json=payload)
    res.raise_for_status()
    data = res.json()
    print(f"[OK] Report PDF created!")
    print(f"     Report Download URL/Path: {data['report_url']}")
except Exception as e:
    print(f"[ERROR] Report generation failed: {e}")
    sys.exit(1)

print("\n=============================================")
print("ALL BACKEND API TESTS COMPLETED SUCCESSFULLY!")
print("=============================================")

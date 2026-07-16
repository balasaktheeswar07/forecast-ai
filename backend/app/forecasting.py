import pandas as pd
import numpy as np
from datetime import timedelta
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
import os
import pickle
import io
from .aws_client import (
    get_s3_client,
    DATASETS_BUCKET,
    check_aws_connection
)

def train_and_forecast(df: pd.DataFrame, horizon_days: int = 30, confidence_level: float = 0.95) -> pd.DataFrame:
    """
    Trains a Random Forest forecasting model per channel, and forecasts future performance.
    Calculates dynamic confidence intervals using tree-variance.
    """
    # Ensure Date is datetime
    df = df.copy()
    df["Date"] = pd.to_datetime(df["Date"])
    
    # Identify active channels
    channels = df["Channel"].unique()
    
    forecast_results = []
    
    for channel in channels:
        channel_df = df[df["Channel"] == channel].sort_values(by="Date").reset_index(drop=True)
        if len(channel_df) < 5:
            # Not enough data to forecast reliably, do a simple linear extrapolation
            last_row = channel_df.iloc[-1]
            last_date = last_row["Date"]
            for i in range(1, horizon_days + 1):
                f_date = last_date + timedelta(days=i)
                forecast_results.append({
                    "Date": f_date,
                    "Channel": channel,
                    "Spend": last_row["Spend"],
                    "Impressions": last_row["Impressions"],
                    "Clicks": last_row["Clicks"],
                    "Conversions": last_row["Conversions"],
                    "Revenue": last_row["Revenue"],
                    "ROAS": last_row["ROAS"],
                    "Revenue_Lower": last_row["Revenue"] * 0.9,
                    "Revenue_Upper": last_row["Revenue"] * 1.1,
                    "Conversions_Lower": last_row["Conversions"] * 0.9,
                    "Conversions_Upper": last_row["Conversions"] * 1.1,
                    "IsForecast": True
                })
            continue

        # Feature preparation
        # We'll use: day of week, day of month, month, holiday flag, and time index (ordinal)
        channel_df["Ordinal"] = channel_df["Date"].apply(lambda x: x.toordinal())
        channel_df["DayOfWeek"] = channel_df["Date"].dt.dayofweek
        channel_df["DayOfMonth"] = channel_df["Date"].dt.day
        channel_df["Month"] = channel_df["Date"].dt.month
        
        features = ["Ordinal", "DayOfWeek", "DayOfMonth", "Month", "HolidayFlag"]
        targets = ["Spend", "Impressions", "Clicks", "Conversions", "Revenue"]
        
        X = channel_df[features].values
        
        # We train separate Random Forest models for each target
        models = {}
        for target in targets:
            # We use 50 estimators so training is fast but has enough trees for variance estimation
            rf = RandomForestRegressor(n_estimators=50, random_state=42, max_depth=8)
            rf.fit(X, channel_df[target].values)
            models[target] = rf
            
        # Create future dates features
        last_date = channel_df["Date"].max()
        future_dates = [last_date + timedelta(days=i) for i in range(1, horizon_days + 1)]
        
        future_df = pd.DataFrame({"Date": future_dates})
        future_df["Ordinal"] = future_df["Date"].apply(lambda x: x.toordinal())
        future_df["DayOfWeek"] = future_df["Date"].dt.dayofweek
        future_df["DayOfMonth"] = future_df["Date"].dt.day
        future_df["Month"] = future_df["Date"].dt.month
        
        # Simple holiday flag estimation for future dates (approximate US holidays)
        holidays = [(11, 25), (12, 25), (7, 4), (11, 29)]
        future_df["HolidayFlag"] = future_df.apply(
            lambda r: 1 if (r["Month"], r["Date"].day) in holidays else 0,
            axis=1
        )
        
        X_future = future_df[features].values
        
        # Predictions
        predictions = {}
        for target in targets:
            rf = models[target]
            # Point predictions
            preds = rf.predict(X_future)
            predictions[target] = np.clip(preds, 0, None) # No negative predictions
            
            # Confidence interval estimation based on individual tree forecasts (variance)
            # This calculates standard deviation of forecasts across all trees
            tree_preds = np.array([tree.predict(X_future) for tree in rf.estimators_])
            std_devs = np.std(tree_preds, axis=0)
            
            # For 95% confidence, z-value is approx 1.96
            z_score = 1.96 if confidence_level == 0.95 else (1.645 if confidence_level == 0.90 else 2.576)
            predictions[f"{target}_std"] = std_devs
            predictions[f"{target}_Lower"] = np.clip(preds - z_score * std_devs, 0, None)
            predictions[f"{target}_Upper"] = np.clip(preds + z_score * std_devs, 0, None)
            
        # Package forecast rows
        for idx, date in enumerate(future_dates):
            spend = predictions["Spend"][idx]
            rev = predictions["Revenue"][idx]
            roas = rev / spend if spend > 0 else 0.0
            
            forecast_results.append({
                "Date": date,
                "Channel": channel,
                "Spend": spend,
                "Impressions": predictions["Impressions"][idx],
                "Clicks": predictions["Clicks"][idx],
                "Conversions": predictions["Conversions"][idx],
                "Revenue": rev,
                "ROAS": roas,
                "Revenue_Lower": predictions["Revenue_Lower"][idx],
                "Revenue_Upper": predictions["Revenue_Upper"][idx],
                "Conversions_Lower": predictions["Conversions_Lower"][idx],
                "Conversions_Upper": predictions["Conversions_Upper"][idx],
                "IsForecast": True
            })
            
    # Combine original historical actuals and future forecasts
    forecast_df = pd.DataFrame(forecast_results)
    
    historical_results = []
    for _, row in df.iterrows():
        historical_results.append({
            "Date": row["Date"],
            "Channel": row["Channel"],
            "Spend": row["Spend"],
            "Impressions": row["Impressions"],
            "Clicks": row["Clicks"],
            "Conversions": row["Conversions"],
            "Revenue": row["Revenue"],
            "ROAS": row["ROAS"],
            "Revenue_Lower": row["Revenue"],
            "Revenue_Upper": row["Revenue"],
            "Conversions_Lower": row["Conversions"],
            "Conversions_Upper": row["Conversions"],
            "IsForecast": False
        })
        
    hist_df = pd.DataFrame(historical_results)
    final_df = pd.concat([hist_df, forecast_df], ignore_index=True)
    return final_df

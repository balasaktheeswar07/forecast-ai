import pandas as pd
import numpy as np
import io
import os
import json
from datetime import datetime
from botocore.exceptions import ClientError
from .aws_client import (
    get_s3_client,
    DATASETS_BUCKET,
    check_aws_connection
)

REQUIRED_COLUMNS = ["Date", "Channel", "Spend", "Impressions", "Clicks", "Conversions", "Revenue"]

def validate_and_clean_csv(file_bytes) -> tuple[pd.DataFrame, list[str]]:
    """
    Parses, validates, and cleans the CSV input.
    Returns the cleaned DataFrame and a list of operations performed.
    """
    logs = []
    try:
        # Load CSV
        df = pd.read_csv(io.BytesIO(file_bytes))
        logs.append(f"Loaded CSV with {len(df)} initial rows.")
    except Exception as e:
        raise ValueError(f"Failed to read CSV file: {str(e)}")

    # Column name cleaning (strip spaces, normalize case)
    df.columns = [col.strip().title() for col in df.columns]
    
    # Check for channel column variations
    if "Platform" in df.columns and "Channel" not in df.columns:
        df = df.rename(columns={"Platform": "Channel"})
        logs.append("Renamed 'Platform' column to 'Channel'.")

    # Verify required columns exist
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in CSV: {', '.join(missing_cols)}")

    # 1. Handle Invalid Dates
    initial_rows = len(df)
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    invalid_dates_count = df["Date"].isna().sum()
    if invalid_dates_count > 0:
        df = df.dropna(subset=["Date"])
        logs.append(f"Removed {invalid_dates_count} rows with invalid date formats.")

    # 2. String cleaning for Channel
    df["Channel"] = df["Channel"].astype(str).str.strip().str.title()

    # 3. Numeric conversion and negative values correction
    numeric_cols = ["Spend", "Impressions", "Clicks", "Conversions", "Revenue"]
    for col in numeric_cols:
        # Strip currency symbols and commas if present
        if df[col].dtype == object:
            df[col] = df[col].astype(str).str.replace(r"[^\d.]", "", regex=True)
        
        df[col] = pd.to_numeric(df[col], errors="coerce")
        
        # Check and fill NaN with 0
        nan_count = df[col].isna().sum()
        if nan_count > 0:
            df[col] = df[col].fillna(0.0)
            logs.append(f"Filled {nan_count} missing values in '{col}' with 0.0.")

        # Check and fix negative values
        negative_count = (df[col] < 0).sum()
        if negative_count > 0:
            df[col] = df[col].clip(lower=0.0)
            logs.append(f"Converted {negative_count} negative values in '{col}' to 0.0.")

    # 4. Remove Duplicate Rows & Aggregate same Date/Channel records
    duplicate_count = df.duplicated(subset=["Date", "Channel"]).sum()
    if duplicate_count > 0:
        df = df.groupby(["Date", "Channel"], as_index=False).agg({
            "Spend": "sum",
            "Impressions": "sum",
            "Clicks": "sum",
            "Conversions": "sum",
            "Revenue": "sum"
        })
        logs.append(f"Merged and aggregated {duplicate_count} duplicate records for same date & channel.")
        
    df = df.sort_values(by="Date").reset_index(drop=True)
    logs.append(f"Data validation complete. Final cleaned records: {len(df)}")
    return df, logs

def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes key performance indicators (CTR, CPC, CPA, ROAS, CR) 
    and calendar features.
    """
    df = df.copy()
    
    # KPIs
    df["CTR"] = np.where(df["Impressions"] > 0, df["Clicks"] / df["Impressions"], 0.0)
    df["CPC"] = np.where(df["Clicks"] > 0, df["Spend"] / df["Clicks"], 0.0)
    df["CPA"] = np.where(df["Conversions"] > 0, df["Spend"] / df["Conversions"], 0.0)
    df["ROAS"] = np.where(df["Spend"] > 0, df["Revenue"] / df["Spend"], 0.0)
    df["ConvRate"] = np.where(df["Clicks"] > 0, df["Conversions"] / df["Clicks"], 0.0)

    # Calendar features
    df["Month"] = df["Date"].dt.month
    df["Quarter"] = df["Date"].dt.quarter
    
    # Holiday flags (simplified US major holiday detection)
    holidays = [
        (11, 25), # Thanksgiving (approx)
        (12, 25), # Christmas
        (7, 4),   # Independence Day
        (11, 29), # Black Friday (approx)
    ]
    df["HolidayFlag"] = df.apply(
        lambda row: 1 if (row["Month"], row["Date"].day) in holidays else 0,
        axis=1
    )

    # Rolling averages & lags per Channel
    df = df.sort_values(by=["Channel", "Date"]).reset_index(drop=True)
    
    # 7-day moving averages of spend and ROAS
    df["Spend_MA7"] = df.groupby("Channel")["Spend"].transform(lambda x: x.rolling(7, min_periods=1).mean())
    df["ROAS_MA7"] = df.groupby("Channel")["ROAS"].transform(lambda x: x.rolling(7, min_periods=1).mean())
    
    # Lag features
    df["Spend_Lag7"] = df.groupby("Channel")["Spend"].shift(7).fillna(0.0)
    df["Revenue_Lag7"] = df.groupby("Channel")["Revenue"].shift(7).fillna(0.0)

    return df.sort_values(by="Date").reset_index(drop=True)

def save_dataframe_to_s3_or_local(df: pd.DataFrame, filename: str) -> str:
    """Saves the DataFrame as CSV to S3 or local directory."""
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    
    if check_aws_connection():
        s3 = get_s3_client()
        try:
            s3.put_object(
                Bucket=DATASETS_BUCKET,
                Key=filename,
                Body=csv_buffer.getvalue().encode("utf-8")
            )
            return f"s3://{DATASETS_BUCKET}/{filename}"
        except ClientError as e:
            logger.error(f"S3 save failed: {e}. Saving locally.")
            
    # Fallback to local storage
    os.makedirs("data/datasets", exist_ok=True)
    local_path = os.path.join("data", "datasets", filename)
    with open(local_path, "w", encoding="utf-8") as f:
        f.write(csv_buffer.getvalue())
    return local_path

def load_dataframe_from_s3_or_local(filename: str) -> pd.DataFrame:
    """Loads a DataFrame from S3 or local directory."""
    if check_aws_connection():
        s3 = get_s3_client()
        try:
            response = s3.get_object(Bucket=DATASETS_BUCKET, Key=filename)
            return pd.read_csv(response["Body"])
        except ClientError as e:
            logger.error(f"S3 load failed for {filename}: {e}. Trying local file.")

    # Fallback/Local read
    local_path = os.path.join("data", "datasets", filename)
    if os.path.exists(local_path):
        return pd.read_csv(local_path)
    raise FileNotFoundError(f"Cleaned dataset '{filename}' not found locally or on S3.")

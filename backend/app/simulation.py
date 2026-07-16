import pandas as pd
import numpy as np

def fit_saturation_curves(df: pd.DataFrame) -> dict:
    """
    Fits diminishing returns curves for each channel using OLS through the origin.
    Model: Metric = alpha * ln(Spend + 1)
    Returns a dictionary of coefficients {channel: {metric: alpha}}
    """
    df = df.copy()
    # Group by Date and Channel to get daily points
    daily = df.groupby(["Date", "Channel"], as_index=False).agg({
        "Spend": "sum",
        "Conversions": "sum",
        "Revenue": "sum",
        "Clicks": "sum",
        "Impressions": "sum"
    })
    
    channels = daily["Channel"].unique()
    curves = {}
    
    for channel in channels:
        ch_data = daily[daily["Channel"] == channel]
        spend = ch_data["Spend"].values
        revenue = ch_data["Revenue"].values
        conversions = ch_data["Conversions"].values
        clicks = ch_data["Clicks"].values
        impressions = ch_data["Impressions"].values
        
        # OLS single parameter: alpha = sum(y * ln(x+1)) / sum(ln(x+1)^2)
        ln_spend = np.log1p(spend)
        denom = np.sum(ln_spend ** 2)
        
        if denom > 0:
            alpha_rev = np.sum(revenue * ln_spend) / denom
            alpha_conv = np.sum(conversions * ln_spend) / denom
            alpha_clicks = np.sum(clicks * ln_spend) / denom
            alpha_imp = np.sum(impressions * ln_spend) / denom
        else:
            alpha_rev = alpha_conv = alpha_clicks = alpha_imp = 0.0
            
        curves[channel] = {
            "alpha_rev": max(0.0, alpha_rev),
            "alpha_conv": max(0.0, alpha_conv),
            "alpha_clicks": max(0.0, alpha_clicks),
            "alpha_imp": max(0.0, alpha_imp),
            "avg_spend": np.mean(spend) if len(spend) > 0 else 0.0,
            "avg_revenue": np.mean(revenue) if len(revenue) > 0 else 0.0,
            "avg_conversions": np.mean(conversions) if len(conversions) > 0 else 0.0
        }
        
    return curves

def simulate_scenario(curves: dict, budget_inputs: dict) -> dict:
    """
    Simulates the performance (Revenue, Conversions, ROAS) of channels given absolute daily budget values.
    budget_inputs: {channel: daily_budget}
    """
    simulated_channels = {}
    total_spend = 0.0
    total_revenue = 0.0
    total_conversions = 0.0
    
    for channel, curve in curves.items():
        daily_spend = budget_inputs.get(channel, curve["avg_spend"])
        
        # Calculate saturation output: Metric = alpha * ln(daily_spend + 1)
        ln_spend = np.log1p(daily_spend)
        rev = curve["alpha_rev"] * ln_spend
        conv = curve["alpha_conv"] * ln_spend
        clicks = curve["alpha_clicks"] * ln_spend
        impressions = curve["alpha_imp"] * ln_spend
        
        roas = rev / daily_spend if daily_spend > 0 else 0.0
        cpa = daily_spend / conv if conv > 0 else 0.0
        cpc = daily_spend / clicks if clicks > 0 else 0.0
        ctr = clicks / impressions if impressions > 0 else 0.0
        
        simulated_channels[channel] = {
            "Spend": daily_spend,
            "Impressions": impressions,
            "Clicks": clicks,
            "Conversions": conv,
            "Revenue": rev,
            "ROAS": roas,
            "CPA": cpa,
            "CPC": cpc,
            "CTR": ctr
        }
        
        total_spend += daily_spend
        total_revenue += rev
        total_conversions += conv
        
    total_roas = total_revenue / total_spend if total_spend > 0 else 0.0
    
    return {
        "channels": simulated_channels,
        "summary": {
            "TotalSpend": total_spend,
            "TotalRevenue": total_revenue,
            "TotalConversions": total_conversions,
            "TotalROAS": total_roas
        }
    }

def optimize_budget_allocation(curves: dict, total_daily_budget: float) -> dict:
    """
    Finds the optimal budget distribution across channels that maximizes total revenue.
    Solves: Maximize Sum(alpha_i * ln(x_i + 1)) s.t. Sum(x_i) = total_daily_budget, x_i >= 0.
    Uses binary search to find Lagrange multiplier lambda.
    """
    channels = list(curves.keys())
    alphas = np.array([curves[ch]["alpha_rev"] for ch in channels])
    
    if len(channels) == 0 or total_daily_budget <= 0:
        return {ch: 0.0 for ch in channels}
        
    # Edge case: all alphas are 0
    if np.sum(alphas) == 0:
        # Distribute equally
        equal_budget = total_daily_budget / len(channels)
        return {ch: equal_budget for ch in channels}

    # Binary search for lambda (multiplier)
    # The budget allocation formula is x_i = max(0, alpha_i / lambda - 1)
    # Target: Sum(x_i) = total_daily_budget
    low = 1e-12
    high = np.max(alphas) + 1.0  # high bound for lambda
    
    # Run 60 iterations of binary search for extreme accuracy
    for _ in range(60):
        mid = (low + high) / 2
        allocations = np.maximum(0, alphas / mid - 1)
        current_sum = np.sum(allocations)
        
        if current_sum > total_daily_budget:
            low = mid
        else:
            high = mid
            
    final_lambda = (low + high) / 2
    final_allocations = np.maximum(0, alphas / final_lambda - 1)
    
    # Scale allocations slightly to account for tiny numerical differences
    allocated_sum = np.sum(final_allocations)
    if allocated_sum > 0:
        final_allocations = (final_allocations / allocated_sum) * total_daily_budget
        
    return {channels[i]: float(final_allocations[i]) for i in range(len(channels))}

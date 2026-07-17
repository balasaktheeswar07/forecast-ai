import os
import logging
import google.generativeai as genai
from typing import Optional, Dict, Any
from .llm_engine import LLMOrchestrator

logger = logging.getLogger("forecast-ai-ai")

# Initialize LLM Orchestrator (FREE LLMs: Ollama, HuggingFace, then Gemini, then Heuristics)
llm_orchestrator = LLMOrchestrator()

def generate_strategic_insights(
    forecast_data: dict, 
    simulation_data: Optional[dict] = None, 
    api_key: Optional[str] = None
) -> str:
    """
    Generates strategic marketing recommendation text using best available LLM.
    
    Priority order (all FREE):
    1. ✅ Ollama (Llama 3) - Local, offline, instant
    2. ✅ HuggingFace - Local, free, no rate limits
    3. ✅ Google Gemini - Free tier (60 req/min)
    4. ✅ Heuristic Engine - 100% free, data-driven fallback
    """
    
    try:
        # Use LLM Orchestrator for intelligent routing
        insights = llm_orchestrator.generate_strategic_insights(forecast_data, simulation_data)
        logger.info("✅ Strategic insights generated successfully")
        return insights
        
    except Exception as e:
        logger.error(f"Insights generation error: {e}")
        # Fallback to basic heuristics
        return generate_basic_insights(forecast_data, simulation_data)


def generate_basic_insights(forecast_data: dict, simulation_data: Optional[dict] = None) -> str:
    """
    Fallback: Simple data-driven insights without LLM
    """
    hist_roas = forecast_data.get("historical_roas", 0.0)
    proj_roas = forecast_data.get("projected_roas", 0.0)
    hist_revenue = forecast_data.get("historical_revenue", 0.0)
    proj_revenue = forecast_data.get("projected_revenue", 0.0)
    hist_spend = forecast_data.get("historical_spend", 0.0)
    proj_spend = forecast_data.get("projected_spend", 0.0)
    
    channel_details = forecast_data.get("channels", {})
    
    # Sort channels by ROAS to find best and worst
    channel_list = []
    for ch, metrics in channel_details.items():
        channel_list.append({
            "name": ch,
            "roas": metrics.get("roas", 0.0),
            "spend": metrics.get("spend", 0.0),
            "revenue": metrics.get("revenue", 0.0),
            "cpa": metrics.get("cpa", 0.0),
            "cpc": metrics.get("cpc", 0.0)
        })
        
    channel_list.sort(key=lambda x: x["roas"], reverse=True)
    
    best_channel = channel_list[0] if len(channel_list) > 0 else {"name": "None", "roas": 0.0}
    worst_channel = channel_list[-1] if len(channel_list) > 1 else {"name": "None", "roas": 0.0}
    
    # Analyze trends
    roas_trend = "improving" if proj_roas > hist_roas else ("stable" if abs(proj_roas - hist_roas) < 0.1 else "declining")
    revenue_growth = ((proj_revenue - hist_revenue) / hist_revenue * 100) if hist_revenue > 0 else 0.0
    
    insights = f"""## 📈 Executive Summary

The campaign performance forecast indicates a **{roas_trend}** trend for the upcoming 30-day period. 
- **Forecasted Revenue**: ${proj_revenue:,.2f} ({"+" if revenue_growth >= 0 else ""}{revenue_growth:.1f}% vs. last 30 days)
- **Forecasted Spend**: ${proj_spend:,.2f}
- **Projected Target ROAS**: {proj_roas:.2f}x (compared to historical {hist_roas:.2f}x)

Overall portfolio efficiency remains healthy, but marginal returns are starting to diverge across platforms, signaling immediate budget optimization opportunities.

## 🔍 Platform Insights

"""
    
    for ch in channel_list:
        insights += f"### {ch['name']} (ROAS: {ch['roas']:.2f}x)\n"
        if ch['roas'] >= 2.5:
            insights += f"- **Status**: Highly Efficient. {ch['name']} is generating superior returns at a stable Cost Per Acquisition (${ch['cpa']:.2f}).\n"
            insights += "- **Recommendation**: Aggressively scale daily spend to capture remaining market share. Platform conversion rate supports increased volume.\n"
        elif ch['roas'] >= 1.5:
            insights += f"- **Status**: Moderately Efficient. Currently pacing well with steady clicks and CTR. Average Cost Per Click (CPC) is ${ch['cpc']:.2f}.\n"
            insights += "- **Recommendation**: Maintain current budget allocation. Focus on ad creative optimization to lower CPC and push ROAS past 2.0x.\n"
        else:
            insights += f"- **Status**: Underperforming. High acquisition costs (${ch['cpa']:.2f}) are suppressing total profitability.\n"
            insights += f"- **Recommendation**: Cap budgets immediately. Review target audiences and conversion tracking. Run creative testing before scaling.\n"
        insights += "\n"

    insights += """## ⚠️ Saturation & Risk Assessment

1. **Diminishing Returns Alert**: 
"""
    if best_channel['name'] != "None" and best_channel['spend'] > 5000:
        insights += f"- **{best_channel['name']}** is showing early indicators of audience fatigue. While ROAS remains high ({best_channel['roas']:.2f}x), incremental spend increases are expected to face resistance.\n"
    else:
        insights += "- Low-budget channels currently show high elasticity; scaling them up should be done incrementally to monitor CPC changes.\n"
        
    insights += f"""- **Cost-Per-Click Crises**: Competing advertisers in the industry are raising bid prices, exposing low-efficiency channels (like {worst_channel['name'] if worst_channel['name'] != 'None' else 'weaker performers'}) to margin compression.

## 🚀 Strategic Action Plan

- **Shift Capital**: Reallocate 15% of the total budget from lower-performing channels to **{best_channel['name']}** to maximize total portfolio revenue.
- **Implement Capping**: Place strict CPA bid limits on underperforming platforms to protect net margins.
- **A/B Testing**: Spin up fresh creative formats (e.g. user-generated short-form video) to counter the observed ad fatigue in core channels.
- **Conversion Rate Optimization (CRO)**: Focus on landing page speed audits to capture the projected increase in future traffic volume.
"""

    if simulation_data:
        sim_summary = simulation_data.get("summary", {})
        sim_roas = sim_summary.get("TotalROAS", 0.0)
        insights += f"""
---
*Note: This report has been updated with the user-defined simulation (Total Spend: ${sim_summary.get('TotalSpend', 0):,.2f}, Predicted ROAS: {sim_roas:.2f}x).*
"""
        
    return insights

def simulated_chatbot_response(user_query: str, campaign_summary: dict) -> str:
    """
    Generates a helpful AI response for the chat assistant.
    """
    user_query_lower = user_query.lower()
    
    # Extract metrics for token replacement
    channels = list(campaign_summary.get("channels", {}).keys())
    hist_roas = campaign_summary.get("historical_roas", 2.1)
    best_channel = "Google Ads"
    best_roas = 0.0
    for ch, m in campaign_summary.get("channels", {}).items():
        if m.get("roas", 0) > best_roas:
            best_roas = m.get("roas")
            best_channel = ch
            
    if "optimize" in user_query_lower or "budget" in user_query_lower or "allocation" in user_query_lower:
        return f"""To optimize your budget across your active channels ({', '.join(channels)}), I recommend utilizing our **Budget Simulator & Optimizer** tab. 

Based on my analysis:
1. **{best_channel}** is your most efficient channel with a ROAS of **{best_roas:.2f}x**. You should increase its share by at least 15%.
2. You should scale down underperforming platforms that have a ROAS below 1.5x.
3. Click the **"Optimize Allocation"** button in the Simulator tab to run our marginal utility optimizer, which mathematically calculates the ideal distribution of your daily ad spend to maximize total ROI across all channels."""

    elif "forecast" in user_query_lower or "future" in user_query_lower or "next month" in user_query_lower:
        proj_rev = campaign_summary.get("projected_revenue", 0.0)
        proj_roas = campaign_summary.get("projected_roas", 0.0)
        return f"""For the next 30 days, my forecast model projects:
- **Total Revenue**: ${proj_rev:,.2f}
- **Average ROAS**: {proj_roas:.2f}x

The forecast shows steady performance, with a standard confidence interval of 95%. Google Ads is expected to lead traffic acquisition, while Meta Ads will capture high e-commerce conversion volume. Monitor daily metrics closely."""

    elif "roas" in user_query_lower or "return" in user_query_lower:
        return f"""Your overall historical ROAS is **{hist_roas:.2f}x**. 
To improve this metric:
- Shift budget from low-ROI channels to **{best_channel}** ({best_roas:.2f}x).
- Cap bids on high-CPA keywords/campaigns.
- Address ad fatigue: if impressions are steady but CTR is dropping, refresh your ad creatives immediately to stimulate conversions."""

    else:
        return f"""Hello! I am your AI Marketing Assistant. I can help you analyze campaign forecasts, run what-if budget simulations, and optimize ad spend across channels.

Here are some things you can ask me:
- *"How should I allocate my $50,000 budget?"*
- *"What is next month's forecasted ROAS?"*
- *"Which channel has the best efficiency and how can I scale it?"*

How can I assist you with your marketing strategy today?"""

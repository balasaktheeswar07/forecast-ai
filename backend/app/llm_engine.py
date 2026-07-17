"""
Free LLM Engine for Forecast AI
Supports: Ollama (Llama 3), HuggingFace models, and fallback heuristics
Zero API costs - runs locally or on your server
"""

import os
import logging
import requests
import json
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger("forecast-ai-llm")

# ============================================================================
# OLLAMA LOCAL LLM ENGINE (Recommended - Free & Fast)
# ============================================================================

class OllamaLLMEngine:
    """
    Uses Ollama to run Llama 3, Mistral, or other local models.
    Installation: https://ollama.ai
    Command: ollama pull llama3 && ollama serve
    """
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3"):
        self.base_url = base_url
        self.model = model
        self.api_endpoint = f"{base_url}/api/generate"
        
    def is_available(self) -> bool:
        """Check if Ollama service is running"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Ollama not available: {e}")
            return False
    
    def generate_insights(self, prompt: str, temperature: float = 0.7, max_tokens: int = 1500) -> str:
        """
        Generate marketing insights using local Llama 3 model
        Temperature: 0.0-1.0 (higher = more creative)
        """
        try:
            if not self.is_available():
                logger.warning("Ollama service not running. Falling back to heuristics.")
                return None
                
            logger.info(f"Generating insights with {self.model}...")
            
            response = requests.post(
                self.api_endpoint,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": temperature,
                    "num_predict": max_tokens,
                },
                timeout=300  # 5 min timeout for large models
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "").strip()
            else:
                logger.error(f"Ollama API error: {response.status_code}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error("Ollama request timed out")
            return None
        except Exception as e:
            logger.error(f"Ollama generation error: {e}")
            return None


# ============================================================================
# HUGGINGFACE LOCAL LLM ENGINE (Free - Requires GPU for speed)
# ============================================================================

class HuggingFaceLLMEngine:
    """
    Uses HuggingFace transformers library to run models locally.
    Requires: pip install transformers torch
    Recommended models: mistral-7b, neural-chat-7b-v3-1
    """
    
    def __init__(self, model_name: str = "mistralai/Mistral-7B-Instruct-v0.1"):
        self.model_name = model_name
        self.model = None
        self.tokenizer = None
        self._load_model()
        
    def _load_model(self):
        """Load model lazily on first use"""
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            import torch
            
            logger.info(f"Loading HuggingFace model: {self.model_name}...")
            
            device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"Using device: {device}")
            
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=torch.float16 if device == "cuda" else torch.float32,
                device_map="auto" if device == "cuda" else None
            )
            
            if device == "cpu":
                self.model = self.model.to(device)
                
            logger.info("Model loaded successfully!")
            
        except ImportError:
            logger.error("transformers or torch not installed. Run: pip install transformers torch")
            self.model = None
        except Exception as e:
            logger.error(f"Failed to load HuggingFace model: {e}")
            self.model = None
    
    def generate_insights(self, prompt: str, max_tokens: int = 1500) -> Optional[str]:
        """Generate marketing insights using local HuggingFace model"""
        if self.model is None:
            logger.warning("HuggingFace model not loaded")
            return None
            
        try:
            import torch
            
            logger.info("Generating insights with HuggingFace model...")
            
            inputs = self.tokenizer(prompt, return_tensors="pt")
            
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs["input_ids"],
                    max_length=max_tokens,
                    temperature=0.7,
                    top_p=0.95,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id,
                )
            
            response_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            # Remove the prompt from the response
            return response_text[len(prompt):].strip()
            
        except Exception as e:
            logger.error(f"HuggingFace generation error: {e}")
            return None


# ============================================================================
# GOOGLE GEMINI API (Optional - Free tier available)
# ============================================================================

class GeminiLLMEngine:
    """
    Fallback to Google Gemini API if available
    Free tier: 60 requests/minute, limited but sufficient for production
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.configured = False
        
        if self.api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self.genai = genai
                self.configured = True
                logger.info("Gemini API configured")
            except ImportError:
                logger.warning("google-generativeai not installed")
            except Exception as e:
                logger.error(f"Gemini configuration error: {e}")
    
    def is_available(self) -> bool:
        return self.configured
    
    def generate_insights(self, prompt: str, max_tokens: int = 1500) -> Optional[str]:
        """Generate insights using Gemini API"""
        if not self.configured:
            return None
            
        try:
            logger.info("Generating insights with Gemini API...")
            
            model = self.genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(
                prompt,
                generation_config={
                    "max_output_tokens": max_tokens,
                    "temperature": 0.7,
                }
            )
            
            return response.text
            
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return None


# ============================================================================
# HEURISTIC FALLBACK ENGINE (100% Free - No AI Required)
# ============================================================================

class HeuristicInsightEngine:
    """
    Data-driven heuristics engine - No ML/LLM required
    Provides quality insights based on channel performance patterns
    """
    
    @staticmethod
    def generate_insights(
        forecast_data: Dict[str, Any],
        simulation_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate insights using data-driven heuristics"""
        
        hist_roas = forecast_data.get("historical_roas", 0.0)
        proj_roas = forecast_data.get("projected_roas", 0.0)
        hist_revenue = forecast_data.get("historical_revenue", 0.0)
        proj_revenue = forecast_data.get("projected_revenue", 0.0)
        hist_spend = forecast_data.get("historical_spend", 0.0)
        proj_spend = forecast_data.get("projected_spend", 0.0)
        
        channel_details = forecast_data.get("channels", {})
        
        # Analyze channel performance
        channel_list = []
        for ch, metrics in channel_details.items():
            channel_list.append({
                "name": ch,
                "roas": metrics.get("roas", 0.0),
                "spend": metrics.get("spend", 0.0),
                "revenue": metrics.get("revenue", 0.0),
                "cpa": metrics.get("cpa", 0.0),
                "cpc": metrics.get("cpc", 0.0),
                "conv_rate": metrics.get("conv_rate", 0.0)
            })
        
        channel_list.sort(key=lambda x: x["roas"], reverse=True)
        
        best_channel = channel_list[0] if channel_list else {"name": "None", "roas": 0.0}
        worst_channel = channel_list[-1] if len(channel_list) > 1 else {"name": "None", "roas": 0.0}
        
        # Trend analysis
        roas_trend = "improving" if proj_roas > hist_roas else ("stable" if abs(proj_roas - hist_roas) < 0.1 else "declining")
        revenue_growth = ((proj_revenue - hist_revenue) / hist_revenue * 100) if hist_revenue > 0 else 0.0
        spend_growth = ((proj_spend - hist_spend) / hist_spend * 100) if hist_spend > 0 else 0.0
        
        # Build insights report
        insights = f"""## 📈 Executive Summary

The campaign performance forecast indicates a **{roas_trend}** trend for the upcoming 30-day period.
- **Forecasted Revenue**: ${proj_revenue:,.2f} ({"+" if revenue_growth >= 0 else ""}{revenue_growth:.1f}% vs. last 30 days)
- **Forecasted Spend**: ${proj_spend:,.2f} ({"+" if spend_growth >= 0 else ""}{spend_growth:.1f}% change)
- **Projected ROAS**: {proj_roas:.2f}x (compared to historical {hist_roas:.2f}x)

Overall portfolio efficiency {'remains healthy' if proj_roas >= 1.5 else 'needs attention'}, with {'steady growth' if revenue_growth > 10 else 'marginal returns'} opportunities.

## 🔍 Platform Performance Breakdown

"""
        
        for ch in channel_list:
            roas = ch['roas']
            spend = ch['spend']
            cpa = ch['cpa']
            
            if roas >= 3.0:
                status = "🟢 Highly Efficient"
                action = f"Scale aggressively. {ch['name']} shows superior returns. Increase budget by 20-30%."
            elif roas >= 2.0:
                status = "🟡 Efficient"
                action = f"Maintain and optimize. {ch['name']} is performing well. Focus on creative testing."
            elif roas >= 1.5:
                status = "🟠 Moderate"
                action = f"Monitor closely. {ch['name']} needs optimization. Review targeting and bids."
            else:
                status = "🔴 Underperforming"
                action = f"Action required. {ch['name']} has low ROAS (${cpa:.2f} CPA). Reduce spend or pause."
            
            insights += f"### {ch['name']} - {status}\n"
            insights += f"- **ROAS**: {roas:.2f}x | **Spend**: ${spend:,.2f} | **CPA**: ${cpa:.2f}\n"
            insights += f"- **Action**: {action}\n\n"
        
        insights += """## ⚠️ Risk Assessment & Saturation

"""
        
        if best_channel['spend'] > 5000 and best_channel['roas'] > 2.5:
            insights += f"- **{best_channel['name']}** shows early signs of saturation at high spend levels. Monitor CPCs closely.\n"
        else:
            insights += "- Low-budget channels show high elasticity; scale incrementally to test market.\n"
        
        insights += f"- **Competitive pressure**: Industry CPCs are rising. Focus on conversion rate optimization to maintain efficiency.\n"
        insights += f"- **Portfolio concentration**: {f'{best_channel["name"]} represents high proportion of revenue; diversify risk.' if best_channel['spend'] > hist_spend * 0.4 else 'Budget well distributed across channels.'}\n"
        
        insights += f"""

## 🚀 Strategic Action Plan

1. **Shift Capital**: Move 10-15% of budget from {worst_channel['name']} ({worst_channel['roas']:.2f}x ROAS) to {best_channel['name']} ({best_channel['roas']:.2f}x ROAS).
2. **Implement Capping**: Set maximum CPA limits on underperforming channels to protect margins.
3. **A/B Testing**: Launch fresh creative variations (short-form video, carousel ads) to counter ad fatigue.
4. **Conversion Optimization**: Audit landing pages and checkout flows to improve conversion rates by 5-10%.

"""
        
        if simulation_data:
            sim_summary = simulation_data.get("summary", {})
            sim_roas = sim_summary.get("TotalROAS", 0.0)
            sim_spend = sim_summary.get("TotalSpend", 0.0)
            sim_revenue = sim_summary.get("TotalRevenue", 0.0)
            
            improvement = ((sim_roas - proj_roas) / proj_roas * 100) if proj_roas > 0 else 0
            
            insights += f"""---
### 📊 User-Defined Simulation Analysis
- **Simulated Spend**: ${sim_spend:,.2f}
- **Projected Revenue**: ${sim_revenue:,.2f}
- **Simulation ROAS**: {sim_roas:.2f}x ({"+" if improvement >= 0 else ""}{improvement:.1f}% vs. baseline forecast)

**Verdict**: {'✅ This allocation strategy improves overall efficiency!' if improvement > 0 else '⚠️ Consider adjusting allocation to improve returns.'}
"""
        
        return insights


# ============================================================================
# UNIFIED LLM ORCHESTRATOR
# ============================================================================

class LLMOrchestrator:
    """
    Intelligently routes to best available LLM
    Priority: Ollama → HuggingFace → Gemini → Heuristics
    """
    
    def __init__(self):
        self.engines: Dict[str, Any] = {}
        self._initialize_engines()
    
    def _initialize_engines(self):
        """Initialize all available LLM engines"""
        
        # Try Ollama first (fastest, free, local)
        ollama_engine = OllamaLLMEngine()
        if ollama_engine.is_available():
            self.engines['ollama'] = ollama_engine
            logger.info("✅ Ollama engine available")
        
        # Try HuggingFace (free but slower without GPU)
        try:
            hf_engine = HuggingFaceLLMEngine()
            if hf_engine.model is not None:
                self.engines['huggingface'] = hf_engine
                logger.info("✅ HuggingFace engine available")
        except Exception as e:
            logger.debug(f"HuggingFace not available: {e}")
        
        # Try Gemini (optional, free tier)
        gemini_engine = GeminiLLMEngine()
        if gemini_engine.is_available():
            self.engines['gemini'] = gemini_engine
            logger.info("✅ Gemini API available")
        
        # Heuristics always available
        self.engines['heuristics'] = HeuristicInsightEngine()
        logger.info("✅ Heuristic engine available (fallback)")
    
    def generate_strategic_insights(
        self,
        forecast_data: Dict[str, Any],
        simulation_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate insights using best available LLM"""
        
        # Try Ollama first
        if 'ollama' in self.engines:
            prompt = self._build_prompt(forecast_data, simulation_data)
            result = self.engines['ollama'].generate_insights(prompt)
            if result:
                logger.info("✅ Used Ollama for insight generation")
                return result
        
        # Try HuggingFace
        if 'huggingface' in self.engines:
            prompt = self._build_prompt(forecast_data, simulation_data)
            result = self.engines['huggingface'].generate_insights(prompt)
            if result:
                logger.info("✅ Used HuggingFace for insight generation")
                return result
        
        # Try Gemini
        if 'gemini' in self.engines:
            prompt = self._build_prompt(forecast_data, simulation_data)
            result = self.engines['gemini'].generate_insights(prompt)
            if result:
                logger.info("✅ Used Gemini API for insight generation")
                return result
        
        # Fall back to heuristics
        logger.info("✅ Using heuristic engine for insight generation")
        return self.engines['heuristics'].generate_insights(forecast_data, simulation_data)
    
    @staticmethod
    def _build_prompt(forecast_data: Dict[str, Any], simulation_data: Optional[Dict[str, Any]] = None) -> str:
        """Build optimized prompt for LLM"""
        
        hist_roas = forecast_data.get("historical_roas", 0.0)
        proj_roas = forecast_data.get("projected_roas", 0.0)
        hist_revenue = forecast_data.get("historical_revenue", 0.0)
        proj_revenue = forecast_data.get("projected_revenue", 0.0)
        hist_spend = forecast_data.get("historical_spend", 0.0)
        proj_spend = forecast_data.get("projected_spend", 0.0)
        
        channel_details = forecast_data.get("channels", {})
        
        prompt = f"""You are an elite Chief Marketing Officer and AI data analyst at a digital marketing agency.
Analyze the following campaign data and provide strategic, actionable insights.

HISTORICAL METRICS (Past 30 Days):
- Total Spend: ${hist_spend:,.2f}
- Total Revenue: ${hist_revenue:,.2f}
- Overall ROAS: {hist_roas:.2f}x

PROJECTED METRICS (Next 30 Days):
- Total Spend: ${proj_spend:,.2f}
- Total Revenue: ${proj_revenue:,.2f}
- Overall ROAS: {proj_roas:.2f}x

CHANNEL BREAKDOWN:
"""
        
        for ch, metrics in channel_details.items():
            prompt += f"\n{ch}:\n"
            prompt += f"  - Spend: ${metrics.get('spend', 0):,.2f}\n"
            prompt += f"  - Revenue: ${metrics.get('revenue', 0):,.2f}\n"
            prompt += f"  - ROAS: {metrics.get('roas', 0):.2f}x\n"
            prompt += f"  - CPA: ${metrics.get('cpa', 0):.2f}\n"
            prompt += f"  - CPC: ${metrics.get('cpc', 0):.2f}\n"
        
        if simulation_data:
            sim_summary = simulation_data.get("summary", {})
            prompt += f"""

USER SIMULATION SCENARIO:
- Simulated Total Spend: ${sim_summary.get('TotalSpend', 0):,.2f}
- Simulated Total Revenue: ${sim_summary.get('TotalRevenue', 0):,.2f}
- Simulated ROAS: {sim_summary.get('TotalROAS', 0):.2f}x
"""
        
        prompt += """

REQUIRED OUTPUT FORMAT:
Generate a detailed marketing report with these sections (use markdown):
1. ## 📈 Executive Summary: Overall health and forecast trends
2. ## 🔍 Platform Insights: Audit each channel's performance
3. ## ⚠️ Risk Assessment: Identify saturation and CPM/CPA issues
4. ## 🚀 Strategic Action Plan: 3-4 specific, quantified recommendations

Keep tone professional, analytical, and actionable. Be specific with budget amounts and percentages.
"""
        
        return prompt

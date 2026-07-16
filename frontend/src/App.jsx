import React, { useState, useEffect, useRef } from 'react';
import { 
  BarChart, Bar, LineChart, Line, AreaChart, Area, XAxis, YAxis, 
  CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell 
} from 'recharts';
import { 
  TrendingUp, BarChart2, MessageSquare, UploadCloud, Settings, 
  Play, ShieldAlert, CheckCircle2, ChevronRight, FileText, 
  HelpCircle, RefreshCw, Cpu, Award, Zap, DollarSign, Download, Send
} from 'lucide-react';

const COLORS = ['#3b82f6', '#ec4899', '#10b981', '#f59e0b', '#8b5cf6'];

export default function App() {
  const [activeTab, setActiveTab] = useState('upload');
  const [campaignId, setCampaignId] = useState(localStorage.getItem('campaignId') || '');
  const [campaignMeta, setCampaignMeta] = useState(null);
  
  // States for API data
  const [previewData, setPreviewData] = useState([]);
  const [cleaningLogs, setCleaningLogs] = useState([]);
  const [forecastData, setForecastData] = useState([]);
  const [forecastSummary, setForecastSummary] = useState(null);
  const [simulatedData, setSimulatedData] = useState(null);
  const [simulationBudgets, setSimulationBudgets] = useState({});
  const [aiInsights, setAiInsights] = useState('');
  
  // Interactive / UI states
  const [loading, setLoading] = useState({
    upload: false,
    forecast: false,
    simulate: false,
    insights: false,
    optimize: false,
    report: false
  });
  const [error, setError] = useState('');
  const [geminiKey, setGeminiKey] = useState(localStorage.getItem('geminiKey') || '');
  const [horizon, setHorizon] = useState(30);
  const [totalDailyBudget, setTotalDailyBudget] = useState(0);
  const [cloudConnected, setCloudConnected] = useState(false);
  
  // Chat States
  const [chatHistory, setChatHistory] = useState([
    { sender: 'ai', text: "Hello! I am your AI Marketing Assistant. Ask me how to optimize your ad spend, what your 30-day forecast is, or how to reduce CPAs." }
  ]);
  const [chatInput, setChatInput] = useState('');
  const chatEndRef = useRef(null);

  // Check health and backend connectivity on mount
  useEffect(() => {
    fetch('/api/')
      .then(res => res.json())
      .then(data => {
        setCloudConnected(data.aws_connected);
      })
      .catch(err => {
        console.error("Backend offline:", err);
        setError("Warning: Backend API seems offline. Please start uvicorn run_backend.py.");
      });
  }, []);

  // Scroll chatbot to bottom
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory]);

  // Load campaign data if campaignId is already present on load
  useEffect(() => {
    if (campaignId) {
      loadForecastData(campaignId);
    }
  }, [campaignId, horizon]);

  const loadForecastData = async (id) => {
    setLoading(prev => ({ ...prev, forecast: true }));
    setError('');
    try {
      // 1. Get Forecast
      const forecastRes = await fetch('/api/forecast', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ campaign_id: id, horizon_days: horizon })
      });
      if (!forecastRes.ok) throw new Error("Failed to fetch campaign forecast");
      const forecast = await forecastRes.json();
      
      setForecastData(forecast.metrics);
      setForecastSummary(forecast.summary);
      
      // Calculate initial simulator sliders based on historical average
      // Let's call /api/simulate with empty/default budgets to fit curves and get baseline
      const simulateRes = await fetch('/api/simulate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ campaign_id: id, budgets: {} })
      });
      if (simulateRes.ok) {
        const sim = await simulateRes.json();
        setSimulatedData(sim);
        // Set default budgets from baseline
        const initialBudgets = {};
        let sumBudget = 0;
        Object.entries(sim.baseline.channels).forEach(([ch, metrics]) => {
          initialBudgets[ch] = Math.round(metrics.Spend);
          sumBudget += metrics.Spend;
        });
        setSimulationBudgets(initialBudgets);
        setTotalDailyBudget(Math.round(sumBudget));
      }
      
      // Save campaign metadata
      setCampaignId(id);
      localStorage.setItem('campaignId', id);
      
      // Generate initial AI Insights
      generateInsights(forecast.summary, null);
    } catch (err) {
      console.error(err);
      setError("Error loading campaign data. Please upload a new dataset.");
    } finally {
      setLoading(prev => ({ ...prev, forecast: false }));
    }
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;
    
    setLoading(prev => ({ ...prev, upload: true }));
    setError('');
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      const res = await fetch('/api/upload', {
        method: 'POST',
        body: formData
      });
      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Failed to upload file");
      }
      
      const data = await res.json();
      setCleaningLogs(data.cleaning_logs);
      setPreviewData(data.preview);
      setCampaignMeta({
        filename: data.filename,
        channels: data.channels,
        summary: data.summary
      });
      
      // Load full forecasts
      await loadForecastData(data.campaign_id);
      
      // Auto move to dashboard tab
      setActiveTab('dashboard');
    } catch (err) {
      console.error(err);
      setError(err.message);
    } finally {
      setLoading(prev => ({ ...prev, upload: false }));
    }
  };

  const handleSimulationSlider = async (channel, val) => {
    const updatedBudgets = { ...simulationBudgets, [channel]: Number(val) };
    setSimulationBudgets(updatedBudgets);
    
    // Call simulation endpoint
    try {
      const res = await fetch('/api/simulate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ campaign_id: campaignId, budgets: updatedBudgets })
      });
      if (res.ok) {
        const data = await res.json();
        setSimulatedData(data);
      }
    } catch (err) {
      console.error("Simulation error:", err);
    }
  };

  const optimizeBudget = async () => {
    setLoading(prev => ({ ...prev, optimize: true }));
    try {
      const res = await fetch('/api/optimize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ campaign_id: campaignId, total_daily_budget: totalDailyBudget })
      });
      if (!res.ok) throw new Error("Optimization failed");
      const data = await res.json();
      
      // Update sliders
      const optimizedBudgets = {};
      Object.entries(data.allocations).forEach(([ch, val]) => {
        optimizedBudgets[ch] = Math.round(val);
      });
      setSimulationBudgets(optimizedBudgets);
      
      // Update simulation metrics
      const simRes = await fetch('/api/simulate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ campaign_id: campaignId, budgets: optimizedBudgets })
      });
      if (simRes.ok) {
        const simData = await simRes.json();
        setSimulatedData(simData);
      }
      
      // Generate fresh insights including the simulation
      if (forecastSummary) {
        generateInsights(forecastSummary, data.projected_metrics);
      }
    } catch (err) {
      console.error(err);
      setError("Budget optimization failed.");
    } finally {
      setLoading(prev => ({ ...prev, optimize: false }));
    }
  };

  const generateInsights = async (forecastSum, simSum = null) => {
    setLoading(prev => ({ ...prev, insights: true }));
    try {
      // Format payload for insights
      // Translate frontend channel schema to backend summaries
      const channelsSummary = {};
      
      // Group forecast metrics by channel
      const channelGroup = {};
      forecastData.forEach(row => {
        if (!row.IsForecast) {
          if (!channelGroup[row.Channel]) channelGroup[row.Channel] = { spend: 0, revenue: 0, conv: 0, clicks: 0, imp: 0 };
          channelGroup[row.Channel].spend += row.Spend;
          channelGroup[row.Channel].revenue += row.Revenue;
          channelGroup[row.Channel].conv += row.Conversions;
          channelGroup[row.Channel].clicks += row.Clicks;
          channelGroup[row.Channel].imp += row.Impressions;
        }
      });
      
      Object.entries(channelGroup).forEach(([ch, val]) => {
        channelsSummary[ch] = {
          spend: val.spend,
          revenue: val.revenue,
          roas: val.spend > 0 ? val.revenue / val.spend : 0.0,
          conv_rate: val.clicks > 0 ? val.conv / val.clicks : 0.0,
          cpa: val.conv > 0 ? val.spend / val.conv : 0.0,
          cpc: val.clicks > 0 ? val.spend / val.clicks : 0.0
        };
      });

      const payload = {
        campaign_id: campaignId,
        forecast_summary: {
          historical_roas: forecastSum.historical_roas,
          projected_roas: forecastSum.projected_roas,
          historical_revenue: forecastSum.historical_revenue,
          projected_revenue: forecastSum.projected_revenue,
          historical_spend: forecastSum.historical_spend,
          projected_spend: forecastSum.projected_spend,
          channels: channelsSummary
        },
        simulation_summary: simSum ? simSum.simulation : null,
        gemini_key: geminiKey
      };

      const res = await fetch('/api/insights', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'X-Gemini-Key': geminiKey
        },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        const data = await res.json();
        setAiInsights(data.insights);
      }
    } catch (err) {
      console.error("Insights failed:", err);
    } finally {
      setLoading(prev => ({ ...prev, insights: false }));
    }
  };

  const handleChatSubmit = async (e) => {
    e.preventDefault();
    if (!chatInput.trim()) return;
    
    const userMsg = chatInput;
    setChatHistory(prev => [...prev, { sender: 'user', text: userMsg }]);
    setChatInput('');
    
    try {
      const summaryPayload = {
        historical_roas: forecastSummary?.historical_roas || 0.0,
        projected_revenue: forecastSummary?.projected_revenue || 0.0,
        projected_roas: forecastSummary?.projected_roas || 0.0,
        channels: simulationBudgets
      };
      
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          campaign_id: campaignId,
          message: userMsg,
          campaign_summary: summaryPayload
        })
      });
      
      if (res.ok) {
        const data = await res.json();
        setChatHistory(prev => [...prev, { sender: 'ai', text: data.response }]);
      }
    } catch (err) {
      console.error(err);
      setChatHistory(prev => [...prev, { sender: 'ai', text: "Sorry, I had an issue connecting to my NLP engine." }]);
    }
  };

  const downloadReport = async () => {
    setLoading(prev => ({ ...prev, report: true }));
    try {
      const payload = {
        campaign_id: campaignId,
        forecast_summary: {
          historical_revenue: forecastSummary?.historical_revenue || 0.0,
          projected_revenue: forecastSummary?.projected_revenue || 0.0,
          historical_roas: forecastSummary?.historical_roas || 0.0,
          projected_roas: forecastSummary?.projected_roas || 0.0,
          channels: Object.entries(simulatedData?.baseline?.channels || {}).map(([ch, v]) => ({
            name: ch,
            spend: v.Spend,
            revenue: v.Revenue,
            roas: v.ROAS
          })).reduce((acc, curr) => {
            acc[curr.name] = { spend: curr.spend, revenue: curr.revenue, roas: curr.roas };
            return acc;
          }, {})
        },
        insights: aiInsights
      };
      
      const res = await fetch('/api/generate-report', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      
      if (res.ok) {
        const data = await res.json();
        // Open report PDF link
        window.open(data.report_url, '_blank');
      } else {
        throw new Error("Report generation failed");
      }
    } catch (err) {
      console.error(err);
      setError("Failed to download PDF report.");
    } finally {
      setLoading(prev => ({ ...prev, report: false }));
    }
  };

  const saveSettings = (e) => {
    e.preventDefault();
    localStorage.setItem('geminiKey', geminiKey);
    setError("Settings saved! Recalculating AI insights...");
    if (forecastSummary) {
      generateInsights(forecastSummary, simulatedData);
    }
  };

  const downloadSampleData = () => {
    // Generates a mock digital marketing campaign dataset CSV in-browser
    const channels = ["Google Ads", "Meta Ads", "LinkedIn Ads", "TikTok Ads"];
    const baseSpends = { "Google Ads": 150, "Meta Ads": 200, "LinkedIn Ads": 80, "TikTok Ads": 120 };
    const cvRates = { "Google Ads": 0.04, "Meta Ads": 0.035, "LinkedIn Ads": 0.02, "TikTok Ads": 0.025 };
    const cpcs = { "Google Ads": 1.5, "Meta Ads": 1.2, "LinkedIn Ads": 4.5, "TikTok Ads": 0.8 };
    const values = { "Google Ads": 120, "Meta Ads": 90, "LinkedIn Ads": 350, "TikTok Ads": 45 };

    let csvContent = "Date,Channel,Spend,Impressions,Clicks,Conversions,Revenue\n";
    
    // Generate 60 days of historical data
    const today = new Date();
    for (let day = 60; day >= 1; day--) {
      const date = new Date(today);
      date.setDate(today.getDate() - day);
      const dateString = date.toISOString().split('T')[0];
      
      channels.forEach(ch => {
        // Add random variance
        const variance = 0.85 + Math.random() * 0.3; // +- 15%
        const spend = Math.round(baseSpends[ch] * variance * 10) / 10;
        
        // Add weekly seasonality (weekend dips)
        const isWeekend = date.getDay() === 0 || date.getDay() === 6;
        const weekendFactor = isWeekend ? 0.7 : 1.0;
        
        const finalSpend = Math.round(spend * weekendFactor * 10) / 10;
        const clicks = Math.round((finalSpend / cpcs[ch]) * (0.9 + Math.random()*0.2));
        const impressions = clicks * Math.round(15 + Math.random()*20);
        
        // Conversions and Revenue
        const conversions = Math.round(clicks * cvRates[ch] * (0.8 + Math.random()*0.4) * 10) / 10;
        const revenue = Math.round(conversions * values[ch] * (0.9 + Math.random()*0.2) * 10) / 10;
        
        csvContent += `${dateString},${ch},${finalSpend},${impressions},${clicks},${conversions},${revenue}\n`;
      });
    }

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement("a");
    const url = URL.createObjectURL(blob);
    link.setAttribute("href", url);
    link.setAttribute("download", "digital_marketing_sample_data.csv");
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const getAggregationChartData = () => {
    // Process forecastData into day-by-day aggregations of actuals vs. forecast
    const dailyMap = {};
    forecastData.forEach(row => {
      const d = row.Date;
      if (!dailyMap[d]) {
        dailyMap[d] = { 
          date: d, 
          SpendActual: 0, 
          SpendForecast: 0, 
          RevenueActual: 0, 
          RevenueForecast: 0,
          RevenueLower: 0,
          RevenueUpper: 0,
          isForecast: row.IsForecast
        };
      }
      if (row.IsForecast) {
        dailyMap[d].SpendForecast += row.Spend;
        dailyMap[d].RevenueForecast += row.Revenue;
        dailyMap[d].RevenueLower += row.Revenue_Lower;
        dailyMap[d].RevenueUpper += row.Revenue_Upper;
      } else {
        dailyMap[d].SpendActual += row.Spend;
        dailyMap[d].RevenueActual += row.Revenue;
        dailyMap[d].RevenueLower += row.Revenue_Lower; // Upper/lower are just actuals
        dailyMap[d].RevenueUpper += row.Revenue_Upper;
      }
    });

    // Sort by date
    return Object.values(dailyMap).sort((a,b) => new Date(a.date) - new Date(b.date)).map(item => {
      // Clear out zeros to prevent lines diving to bottom
      return {
        ...item,
        SpendActual: item.isForecast ? null : Math.round(item.SpendActual),
        SpendForecast: item.isForecast ? Math.round(item.SpendForecast) : null,
        RevenueActual: item.isForecast ? null : Math.round(item.RevenueActual),
        RevenueForecast: item.isForecast ? Math.round(item.RevenueForecast) : null,
        RevenueLower: item.isForecast ? Math.round(item.RevenueLower) : Math.round(item.RevenueActual),
        RevenueUpper: item.isForecast ? Math.round(item.RevenueUpper) : Math.round(item.RevenueActual)
      };
    });
  };

  const getContributionChartData = () => {
    // Group totals by Channel to show contribution
    const channelMap = {};
    forecastData.forEach(row => {
      if (!row.IsForecast) {
        if (!channelMap[row.Channel]) channelMap[row.Channel] = { name: row.Channel, Spend: 0, Revenue: 0 };
        channelMap[row.Channel].Spend += row.Spend;
        channelMap[row.Channel].Revenue += row.Revenue;
      }
    });
    return Object.values(channelMap).map(c => ({
      ...c,
      Spend: Math.round(c.Spend),
      Revenue: Math.round(c.Revenue)
    }));
  };

  const getSimResultChartData = () => {
    if (!simulatedData) return [];
    
    return Object.entries(simulatedData.simulation.channels).map(([ch, metrics]) => {
      const base = simulatedData.baseline.channels[ch] || { Spend: 0, Revenue: 0 };
      return {
        channel: ch,
        "Base Spend": Math.round(base.Spend),
        "Simulated Spend": Math.round(metrics.Spend),
        "Base Revenue": Math.round(base.Revenue),
        "Simulated Revenue": Math.round(metrics.Revenue)
      };
    });
  };

  return (
    <div className="flex h-screen bg-[#070812] text-gray-200 overflow-hidden font-sans">
      {/* Sidebar */}
      <div className="w-64 bg-[#0d0e1b] border-r border-gray-800 flex flex-col justify-between shrink-0">
        <div>
          {/* Logo Header */}
          <div className="p-6 border-b border-gray-800 flex items-center space-x-3">
            <div className="p-2 bg-blue-600 rounded-lg pulse-glow-indicator text-white">
              <Cpu className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-md font-bold tracking-wider text-white">FORECAST AI</h1>
              <span className="text-xs text-gray-500 font-semibold">MARKETING COMPANION</span>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="p-4 space-y-1">
            <button 
              onClick={() => setActiveTab('upload')}
              className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg text-sm font-semibold transition-all ${
                activeTab === 'upload' ? 'bg-blue-600/10 text-blue-400 border-l-4 border-blue-500' : 'text-gray-400 hover:bg-gray-800/40 hover:text-gray-200'
              }`}
            >
              <UploadCloud className="w-4 h-4" />
              <span>Upload CSV</span>
            </button>

            <button 
              onClick={() => { if(campaignId) setActiveTab('dashboard'); }}
              disabled={!campaignId}
              className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg text-sm font-semibold transition-all ${
                !campaignId ? 'opacity-40 cursor-not-allowed' : ''
              } ${
                activeTab === 'dashboard' ? 'bg-blue-600/10 text-blue-400 border-l-4 border-blue-500' : 'text-gray-400 hover:bg-gray-800/40 hover:text-gray-200'
              }`}
            >
              <BarChart2 className="w-4 h-4" />
              <span>Executive Dashboard</span>
            </button>

            <button 
              onClick={() => { if(campaignId) setActiveTab('simulator'); }}
              disabled={!campaignId}
              className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg text-sm font-semibold transition-all ${
                !campaignId ? 'opacity-40 cursor-not-allowed' : ''
              } ${
                activeTab === 'simulator' ? 'bg-blue-600/10 text-blue-400 border-l-4 border-blue-500' : 'text-gray-400 hover:bg-gray-800/40 hover:text-gray-200'
              }`}
            >
              <Zap className="w-4 h-4" />
              <span>Budget Simulator</span>
            </button>

            <button 
              onClick={() => { if(campaignId) setActiveTab('ai'); }}
              disabled={!campaignId}
              className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg text-sm font-semibold transition-all ${
                !campaignId ? 'opacity-40 cursor-not-allowed' : ''
              } ${
                activeTab === 'ai' ? 'bg-blue-600/10 text-blue-400 border-l-4 border-blue-500' : 'text-gray-400 hover:bg-gray-800/40 hover:text-gray-200'
              }`}
            >
              <MessageSquare className="w-4 h-4" />
              <span>AI Insights & Chat</span>
            </button>

            <button 
              onClick={() => setActiveTab('settings')}
              className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg text-sm font-semibold transition-all ${
                activeTab === 'settings' ? 'bg-blue-600/10 text-blue-400 border-l-4 border-blue-500' : 'text-gray-400 hover:bg-gray-800/40 hover:text-gray-200'
              }`}
            >
              <Settings className="w-4 h-4" />
              <span>Settings</span>
            </button>
          </nav>
        </div>

        {/* User / Cloud Status footer */}
        <div className="p-4 border-t border-gray-800">
          <div className="flex items-center space-x-2">
            <span className={`w-2.5 h-2.5 rounded-full ${cloudConnected ? 'bg-green-500 pulse-glow-indicator' : 'bg-amber-500'}`}></span>
            <span className="text-xs font-semibold text-gray-400">
              {cloudConnected ? 'LocalStack Cloud Active' : 'Local Sandbox Mode'}
            </span>
          </div>
          <div className="mt-2 text-[10px] text-gray-600">
            v1.0.0 Serverless FastAPI
          </div>
        </div>
      </div>

      {/* Main Workspace Area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top Header Panel */}
        <header className="h-16 border-b border-gray-800 bg-[#0d0e1b] flex items-center justify-between px-8 shrink-0">
          <div className="flex items-center space-x-3">
            <span className="text-sm font-bold text-white uppercase tracking-wider">
              {activeTab} Workspace
            </span>
            {campaignId && (
              <span className="px-2 py-0.5 text-[10px] font-mono bg-blue-900/30 text-blue-400 rounded-md border border-blue-800">
                Campaign: {campaignId.slice(0,8)}...
              </span>
            )}
          </div>
          
          <div className="flex items-center space-x-4">
            {campaignId && activeTab !== 'upload' && (
              <div className="flex items-center space-x-2">
                <label className="text-xs text-gray-400 font-semibold">Forecast Period:</label>
                <select 
                  value={horizon}
                  onChange={(e) => setHorizon(Number(e.target.value))}
                  className="bg-gray-900 border border-gray-700 text-xs rounded px-2 py-1 text-white focus:outline-none focus:ring-1 focus:ring-blue-500"
                >
                  <option value={15}>15 Days</option>
                  <option value={30}>30 Days</option>
                  <option value={60}>60 Days</option>
                  <option value={90}>90 Days</option>
                </select>
              </div>
            )}
            
            {campaignId && (
              <button 
                onClick={downloadReport}
                disabled={loading.report}
                className="flex items-center space-x-2 px-3 py-1.5 bg-blue-600 hover:bg-blue-500 disabled:bg-blue-800 disabled:cursor-not-allowed text-xs font-semibold text-white rounded transition"
              >
                {loading.report ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <FileText className="w-3.5 h-3.5" />}
                <span>{loading.report ? 'Generating PDF...' : 'Export PDF Report'}</span>
              </button>
            )}
          </div>
        </header>

        {/* Dynamic Viewport Content */}
        <main className="flex-1 overflow-y-auto p-8 relative">
          
          {/* Global Alert Notification */}
          {error && (
            <div className="mb-6 p-4 bg-red-950/40 border border-red-800 text-red-300 text-sm rounded-lg flex items-center space-x-3">
              <ShieldAlert className="w-5 h-5 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* TAB: UPLOAD DATASET */}
          {activeTab === 'upload' && (
            <div className="max-w-2xl mx-auto space-y-6">
              <div className="text-center space-y-2">
                <h2 className="text-2xl font-bold text-white">AI campaign forecasting begins here.</h2>
                <p className="text-gray-400 text-sm max-w-lg mx-auto">
                  Upload historical digital marketing performance CSV files containing channels (Google Ads, Meta Ads, TikTok etc.) to run forecast simulations.
                </p>
              </div>

              {/* Upload Dropzone Card */}
              <div className="glass-panel border-dashed border-gray-700 rounded-xl p-12 text-center flex flex-col items-center justify-center space-y-4 hover:border-blue-500/60 transition cursor-pointer relative">
                <input 
                  type="file" 
                  accept=".csv"
                  onChange={handleFileUpload}
                  className="absolute inset-0 opacity-0 cursor-pointer"
                  disabled={loading.upload}
                />
                
                {loading.upload ? (
                  <div className="flex flex-col items-center space-y-2">
                    <RefreshCw className="w-12 h-12 text-blue-500 animate-spin" />
                    <span className="text-sm font-semibold text-blue-400">Processing & Cleansing Dataset...</span>
                  </div>
                ) : (
                  <>
                    <div className="p-4 bg-gray-900/60 rounded-full text-blue-400">
                      <UploadCloud className="w-10 h-10" />
                    </div>
                    <div>
                      <h3 className="text-md font-semibold text-white">Drag & drop your CSV file here</h3>
                      <span className="text-xs text-gray-500">or click to browse local files</span>
                    </div>
                  </>
                )}
              </div>

              {/* Data specifications */}
              <div className="glass-panel p-6 rounded-xl space-y-4">
                <div className="flex justify-between items-center border-b border-gray-800 pb-3">
                  <h4 className="text-sm font-bold text-white uppercase tracking-wider flex items-center space-x-2">
                    <CheckCircle2 className="w-4 h-4 text-green-500" />
                    <span>CSV Template Specifications</span>
                  </h4>
                  <button 
                    onClick={downloadSampleData}
                    className="text-xs text-blue-400 hover:text-blue-300 font-bold flex items-center space-x-1"
                  >
                    <Download className="w-3.5 h-3.5" />
                    <span>Generate Sample CSV</span>
                  </button>
                </div>
                <p className="text-xs text-gray-400">
                  Ensure your uploaded file contains headers matching: <code className="text-blue-400 font-mono bg-gray-950 px-1 py-0.5 rounded">Date</code>, <code className="text-blue-400 font-mono bg-gray-950 px-1 py-0.5 rounded">Channel</code>, <code className="text-blue-400 font-mono bg-gray-950 px-1 py-0.5 rounded">Spend</code>, <code className="text-blue-400 font-mono bg-gray-950 px-1 py-0.5 rounded">Impressions</code>, <code className="text-blue-400 font-mono bg-gray-950 px-1 py-0.5 rounded">Clicks</code>, <code className="text-blue-400 font-mono bg-gray-950 px-1 py-0.5 rounded">Conversions</code>, <code className="text-blue-400 font-mono bg-gray-950 px-1 py-0.5 rounded">Revenue</code>.
                </p>
              </div>

              {/* Cleaning Logs Console */}
              {cleaningLogs.length > 0 && (
                <div className="glass-panel rounded-xl p-4 bg-black/40 border border-gray-800 font-mono text-xs">
                  <div className="flex items-center justify-between pb-2 border-b border-gray-800 mb-2">
                    <span className="text-green-500 font-bold">Data Cleaning Audit Logs:</span>
                    <span className="text-[10px] text-gray-500">File processed</span>
                  </div>
                  <div className="space-y-1 text-gray-400 overflow-y-auto max-h-40">
                    {cleaningLogs.map((log, i) => (
                      <div key={i} className="flex space-x-2">
                        <span className="text-gray-600">[{i+1}]</span>
                        <span>{log}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* TAB: EXECUTIVE DASHBOARD */}
          {activeTab === 'dashboard' && forecastSummary && (
            <div className="space-y-8">
              
              {/* KPI Scorecard Grid */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                
                {/* KPI Card 1 */}
                <div className="glass-panel p-6 rounded-xl relative overflow-hidden flex flex-col justify-between h-32">
                  <div className="flex justify-between items-start">
                    <span className="text-xs font-bold text-gray-500 uppercase tracking-wider">Forecasted Revenue</span>
                    <div className="p-1 bg-green-950/40 text-green-400 rounded-lg">
                      <TrendingUp className="w-4 h-4" />
                    </div>
                  </div>
                  <div>
                    <h3 className="text-2xl font-bold text-white tracking-tight">${forecastSummary.projected_revenue.toLocaleString('en-US', {maximumFractionDigits: 0})}</h3>
                    <div className="flex items-center space-x-1.5 mt-1">
                      <span className={`text-xs font-bold ${forecastSummary.projected_revenue >= forecastSummary.historical_revenue ? 'text-green-400' : 'text-red-400'}`}>
                        {((forecastSummary.projected_revenue - forecastSummary.historical_revenue) / forecastSummary.historical_revenue * 100).toFixed(1)}%
                      </span>
                      <span className="text-[10px] text-gray-600 font-semibold uppercase">vs last 30 days</span>
                    </div>
                  </div>
                </div>

                {/* KPI Card 2 */}
                <div className="glass-panel p-6 rounded-xl relative overflow-hidden flex flex-col justify-between h-32">
                  <div className="flex justify-between items-start">
                    <span className="text-xs font-bold text-gray-500 uppercase tracking-wider">Forecasted ROAS</span>
                    <div className="p-1 bg-blue-950/40 text-blue-400 rounded-lg">
                      <Award className="w-4 h-4" />
                    </div>
                  </div>
                  <div>
                    <h3 className="text-2xl font-bold text-white tracking-tight">{forecastSummary.projected_roas.toFixed(2)}x</h3>
                    <div className="flex items-center space-x-1.5 mt-1">
                      <span className={`text-xs font-bold ${forecastSummary.projected_roas >= forecastSummary.historical_roas ? 'text-green-400' : 'text-red-400'}`}>
                        {(forecastSummary.projected_roas - forecastSummary.historical_roas).toFixed(2)}x
                      </span>
                      <span className="text-[10px] text-gray-600 font-semibold uppercase">vs last 30 days</span>
                    </div>
                  </div>
                </div>

                {/* KPI Card 3 */}
                <div className="glass-panel p-6 rounded-xl relative overflow-hidden flex flex-col justify-between h-32">
                  <div className="flex justify-between items-start">
                    <span className="text-xs font-bold text-gray-500 uppercase tracking-wider">Net Profit Forecast</span>
                    <div className="p-1 bg-purple-950/40 text-purple-400 rounded-lg">
                      <DollarSign className="w-4 h-4" />
                    </div>
                  </div>
                  <div>
                    <h3 className="text-2xl font-bold text-white tracking-tight">
                      ${(forecastSummary.projected_revenue - forecastSummary.projected_spend).toLocaleString('en-US', {maximumFractionDigits: 0})}
                    </h3>
                    <div className="flex items-center space-x-1.5 mt-1">
                      <span className="text-xs text-purple-400 font-bold">
                        ${(forecastSummary.historical_revenue - forecastSummary.historical_spend).toLocaleString('en-US', {maximumFractionDigits: 0})}
                      </span>
                      <span className="text-[10px] text-gray-600 font-semibold uppercase">historical baseline</span>
                    </div>
                  </div>
                </div>

                {/* KPI Card 4 */}
                <div className="glass-panel p-6 rounded-xl relative overflow-hidden flex flex-col justify-between h-32">
                  <div className="flex justify-between items-start">
                    <span className="text-xs font-bold text-gray-500 uppercase tracking-wider">Forecasted spend</span>
                    <div className="p-1 bg-amber-950/40 text-amber-400 rounded-lg">
                      <Zap className="w-4 h-4" />
                    </div>
                  </div>
                  <div>
                    <h3 className="text-2xl font-bold text-white tracking-tight">${forecastSummary.projected_spend.toLocaleString('en-US', {maximumFractionDigits: 0})}</h3>
                    <div className="flex items-center space-x-1.5 mt-1">
                      <span className="text-xs text-amber-400 font-bold">
                        ${forecastSummary.historical_spend.toLocaleString('en-US', {maximumFractionDigits: 0})}
                      </span>
                      <span className="text-[10px] text-gray-600 font-semibold uppercase">historical spend</span>
                    </div>
                  </div>
                </div>

              </div>

              {/* Main Area Chart: 12-Month Projections */}
              <div className="glass-panel p-6 rounded-xl space-y-4">
                <div className="flex justify-between items-center">
                  <div>
                    <h3 className="text-md font-bold text-white tracking-wide">Dynamic Portfolio Projections</h3>
                    <p className="text-xs text-gray-500">Historical performance merged with Random Forest multi-target regression projections</p>
                  </div>
                </div>
                
                <div className="h-96 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart 
                      data={getAggregationChartData()} 
                      margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
                    >
                      <defs>
                        <linearGradient id="colorRev" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#10b981" stopOpacity={0.2}/>
                          <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                        </linearGradient>
                        <linearGradient id="colorSpend" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.2}/>
                          <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" opacity={0.5} />
                      <XAxis dataKey="date" stroke="#9ca3af" fontSize={10} tickLine={false} />
                      <YAxis stroke="#9ca3af" fontSize={10} tickLine={false} />
                      <Tooltip 
                        contentStyle={{ backgroundColor: '#0d0f20', borderColor: '#1f293d', borderRadius: 8, color: '#f3f4f6' }}
                        labelStyle={{ color: '#9ca3af', fontWeight: 'bold' }}
                      />
                      <Legend verticalAlign="top" height={36} iconType="circle" />
                      
                      {/* Actuals Area */}
                      <Area name="Historical Revenue" type="monotone" dataKey="RevenueActual" stroke="#10b981" strokeWidth={2} fillOpacity={1} fill="url(#colorRev)" />
                      <Area name="Historical Spend" type="monotone" dataKey="SpendActual" stroke="#3b82f6" strokeWidth={2} fillOpacity={1} fill="url(#colorSpend)" />
                      
                      {/* Forecast Area */}
                      <Area name="Forecasted Revenue" type="monotone" dataKey="RevenueForecast" stroke="#059669" strokeWidth={2} strokeDasharray="4 4" fillOpacity={1} fill="url(#colorRev)" />
                      <Area name="Forecasted Spend" type="monotone" dataKey="SpendForecast" stroke="#2563eb" strokeWidth={2} strokeDasharray="4 4" fillOpacity={1} fill="url(#colorSpend)" />

                      {/* Confidence bounds */}
                      <Area name="Revenue Bounds (95% CI)" type="monotone" dataKey="RevenueLower" stroke="none" fill="#10b981" fillOpacity={0.06} />
                      <Area name="Confidence Ceiling" type="monotone" dataKey="RevenueUpper" stroke="none" fill="#10b981" fillOpacity={0.06} />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Lower Section: Pie & Bar Charts for platform breakdown */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                
                {/* Bar Chart: Channel Revenue vs Spend share */}
                <div className="glass-panel p-6 rounded-xl space-y-4">
                  <h3 className="text-sm font-bold text-white uppercase tracking-wider">Channel Portfolio Return Ratio</h3>
                  <div className="h-64 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={getContributionChartData()}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" opacity={0.3} />
                        <XAxis dataKey="name" stroke="#9ca3af" fontSize={10} tickLine={false} />
                        <YAxis stroke="#9ca3af" fontSize={10} tickLine={false} />
                        <Tooltip contentStyle={{ backgroundColor: '#0d0f20', borderColor: '#1f293d', borderRadius: 8 }} />
                        <Legend iconType="circle" />
                        <Bar dataKey="Spend" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                        <Bar dataKey="Revenue" fill="#ec4899" radius={[4, 4, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                {/* Pie Chart: Channel Share */}
                <div className="glass-panel p-6 rounded-xl space-y-4 flex flex-col justify-between">
                  <h3 className="text-sm font-bold text-white uppercase tracking-wider">Historical Spend Contribution</h3>
                  <div className="h-60 w-full flex items-center justify-center">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={getContributionChartData()}
                          cx="50%"
                          cy="50%"
                          labelLine={false}
                          label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                          outerRadius={80}
                          fill="#8884d8"
                          dataKey="Spend"
                        >
                          {getContributionChartData().map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                          ))}
                        </Pie>
                        <Tooltip contentStyle={{ backgroundColor: '#0d0f20', borderColor: '#1f293d', borderRadius: 8 }} />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                </div>

              </div>

            </div>
          )}

          {/* TAB: BUDGET SIMULATOR */}
          {activeTab === 'simulator' && simulatedData && (
            <div className="space-y-8">
              
              {/* Top Summary Block - Base vs Simulated */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                
                {/* Base Case KPI */}
                <div className="glass-panel p-6 rounded-xl border-l-4 border-gray-600 space-y-4">
                  <h4 className="text-xs font-bold text-gray-500 uppercase tracking-wider">Baseline Daily Performance</h4>
                  <div className="grid grid-cols-3 gap-2">
                    <div>
                      <span className="text-[10px] text-gray-600 block uppercase">Daily Spend</span>
                      <span className="text-lg font-bold text-white">${simulatedData.baseline.summary.TotalSpend.toLocaleString('en-US', {maximumFractionDigits: 0})}</span>
                    </div>
                    <div>
                      <span className="text-[10px] text-gray-600 block uppercase">Daily Revenue</span>
                      <span className="text-lg font-bold text-white">${simulatedData.baseline.summary.TotalRevenue.toLocaleString('en-US', {maximumFractionDigits: 0})}</span>
                    </div>
                    <div>
                      <span className="text-[10px] text-gray-600 block uppercase">Baseline ROAS</span>
                      <span className="text-lg font-bold text-white">{simulatedData.baseline.summary.TotalROAS.toFixed(2)}x</span>
                    </div>
                  </div>
                </div>

                {/* Simulated Case KPI */}
                <div className="glass-panel p-6 rounded-xl border-l-4 border-blue-500 space-y-4">
                  <h4 className="text-xs font-bold text-blue-400 uppercase tracking-wider">Simulated Daily Output</h4>
                  <div className="grid grid-cols-3 gap-2">
                    <div>
                      <span className="text-[10px] text-gray-600 block uppercase">Daily Spend</span>
                      <span className="text-lg font-bold text-white">${simulatedData.simulation.summary.TotalSpend.toLocaleString('en-US', {maximumFractionDigits: 0})}</span>
                    </div>
                    <div>
                      <span className="text-[10px] text-gray-600 block uppercase">Expected Revenue</span>
                      <span className="text-lg font-bold text-green-400 glow-cyan">${simulatedData.simulation.summary.TotalRevenue.toLocaleString('en-US', {maximumFractionDigits: 0})}</span>
                    </div>
                    <div>
                      <span className="text-[10px] text-gray-600 block uppercase">Expected ROAS</span>
                      <span className="text-lg font-bold text-blue-400 glow-pink">{simulatedData.simulation.summary.TotalROAS.toFixed(2)}x</span>
                    </div>
                  </div>
                </div>

              </div>

              {/* Layout: Sliders on left, Optimization and Charts on right */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                
                {/* Channel Sliders Panel */}
                <div className="lg:col-span-1 glass-panel p-6 rounded-xl space-y-6">
                  <div>
                    <h3 className="text-sm font-bold text-white uppercase tracking-wider">Adjust Daily Budget</h3>
                    <p className="text-[10px] text-gray-500">Test what-if allocations and estimate diminishing returns</p>
                  </div>
                  
                  <div className="space-y-6">
                    {Object.entries(simulationBudgets).map(([ch, val]) => {
                      const baseSpend = Math.round(simulatedData.baseline.channels[ch]?.Spend || 100);
                      const maxLimit = Math.max(5000, baseSpend * 3);
                      return (
                        <div key={ch} className="space-y-2">
                          <div className="flex justify-between text-xs">
                            <span className="font-semibold text-white">{ch}</span>
                            <span className="font-mono text-gray-400">${val.toLocaleString()} / day</span>
                          </div>
                          <input 
                            type="range"
                            min="0"
                            max={maxLimit}
                            step="10"
                            value={val}
                            onChange={(e) => handleSimulationSlider(ch, e.target.value)}
                            className="w-full h-1 bg-gray-800 rounded-lg appearance-none cursor-pointer accent-blue-500 focus:outline-none"
                          />
                          <div className="flex justify-between text-[10px] text-gray-600">
                            <span>$0</span>
                            <span>Avg: ${baseSpend}</span>
                            <span>Limit: ${maxLimit.toLocaleString()}</span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Optimizer Panel & Comparative Chart */}
                <div className="lg:col-span-2 space-y-6">
                  
                  {/* Optimizer Card */}
                  <div className="glass-panel p-6 rounded-xl space-y-4">
                    <div>
                      <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center space-x-2">
                        <Cpu className="w-4 h-4 text-blue-400" />
                        <span>Lagrange Marginal Utility Optimizer</span>
                      </h3>
                      <p className="text-[10px] text-gray-500">Distribute your capital across channels to mathematically maximize overall return</p>
                    </div>

                    <div className="flex items-center space-x-4">
                      <div className="w-1/2">
                        <label className="text-xs text-gray-400 font-semibold block mb-1">Total Daily Budget Goal ($):</label>
                        <input 
                          type="number"
                          value={totalDailyBudget}
                          onChange={(e) => setTotalDailyBudget(Number(e.target.value))}
                          className="w-full bg-gray-900 border border-gray-700 text-sm rounded px-3 py-2 text-white focus:outline-none focus:ring-1 focus:ring-blue-500 glow-border-cyan"
                        />
                      </div>
                      <div className="w-1/2 pt-5">
                        <button 
                          onClick={optimizeBudget}
                          disabled={loading.optimize}
                          className="w-full py-2 bg-blue-600 hover:bg-blue-500 disabled:bg-blue-800 text-xs font-semibold text-white rounded transition flex items-center justify-center space-x-2 shadow-lg shadow-blue-900/30"
                        >
                          {loading.optimize ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5" />}
                          <span>{loading.optimize ? 'Optimizing...' : 'Calculate Optimal Allocation'}</span>
                        </button>
                      </div>
                    </div>
                  </div>

                  {/* Comparative Chart Panel */}
                  <div className="glass-panel p-6 rounded-xl space-y-4">
                    <h3 className="text-xs font-bold text-white uppercase tracking-wider">Simulated Revenue Share Comparison</h3>
                    <div className="h-64 w-full">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={getSimResultChartData()}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" opacity={0.3} />
                          <XAxis dataKey="channel" stroke="#9ca3af" fontSize={10} tickLine={false} />
                          <YAxis stroke="#9ca3af" fontSize={10} tickLine={false} />
                          <Tooltip contentStyle={{ backgroundColor: '#0d0f20', borderColor: '#1f293d', borderRadius: 8 }} />
                          <Legend iconType="circle" />
                          <Bar dataKey="Base Revenue" fill="#475569" radius={[4, 4, 0, 0]} />
                          <Bar dataKey="Simulated Revenue" fill="#10b981" radius={[4, 4, 0, 0]} />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </div>

                </div>

              </div>

            </div>
          )}

          {/* TAB: AI INSIGHTS & CHAT */}
          {activeTab === 'ai' && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 h-[calc(100vh-12rem)]">
              
              {/* Report Panel - Left 2 Columns */}
              <div className="lg:col-span-2 glass-panel p-6 rounded-xl flex flex-col overflow-hidden">
                <div className="flex justify-between items-center border-b border-gray-800 pb-3 mb-4 shrink-0">
                  <div>
                    <h3 className="text-md font-bold text-white">AI Executive Summary Report</h3>
                    <span className="text-xs text-gray-500 font-semibold">Strategic platforms audit and fatigue warnings</span>
                  </div>
                  {loading.insights && (
                    <RefreshCw className="w-5 h-5 text-blue-500 animate-spin" />
                  )}
                </div>

                <div className="flex-1 overflow-y-auto space-y-4 pr-2 text-sm leading-relaxed text-gray-300">
                  {aiInsights ? (
                    <div className="prose prose-invert max-w-none space-y-4">
                      {aiInsights.split('\n').map((line, i) => {
                        const trimmed = line.trim();
                        if (trimmed.startsWith('## ')) {
                          return <h2 key={i} className="text-lg font-bold text-white border-b border-gray-800 pb-2 mt-6 mb-2">{trimmed.replace('## ', '')}</h2>;
                        } else if (trimmed.startsWith('### ')) {
                          return <h3 key={i} className="text-sm font-bold text-blue-400 mt-4 mb-2">{trimmed.replace('### ', '')}</h3>;
                        } else if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
                          const boldTxt = trimmed.slice(2).replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
                          return <li key={i} className="ml-4 list-disc text-gray-300" dangerouslySetInnerHTML={{ __html: boldTxt }} />;
                        } else {
                          const boldTxt = trimmed.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
                          return <p key={i} className="text-gray-400" dangerouslySetInnerHTML={{ __html: boldTxt }} />;
                        }
                      })}
                    </div>
                  ) : (
                    <div className="h-full flex items-center justify-center text-gray-500">
                      Generating AI strategic analysis...
                    </div>
                  )}
                </div>
              </div>

              {/* Chat advisor - Right Column */}
              <div className="lg:col-span-1 glass-panel rounded-xl flex flex-col overflow-hidden">
                {/* Chat header */}
                <div className="p-4 border-b border-gray-800 bg-gray-900/40 flex items-center space-x-3 shrink-0">
                  <div className="w-2.5 h-2.5 rounded-full bg-green-500 pulse-glow-indicator"></div>
                  <span className="text-xs font-bold text-white uppercase tracking-wider">AI Marketing Advisor</span>
                </div>

                {/* Messages stream */}
                <div className="flex-1 overflow-y-auto p-4 space-y-4">
                  {chatHistory.map((msg, i) => (
                    <div key={i} className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                      <div className={`max-w-[85%] rounded-lg px-3 py-2 text-xs leading-relaxed ${
                        msg.sender === 'user' ? 'bg-blue-600 text-white' : 'bg-gray-800/80 text-gray-200'
                      }`}>
                        {msg.text}
                      </div>
                    </div>
                  ))}
                  <div ref={chatEndRef} />
                </div>

                {/* Input form */}
                <form onSubmit={handleChatSubmit} className="p-3 border-t border-gray-800 bg-gray-900/40 flex space-x-2 shrink-0">
                  <input 
                    type="text"
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    placeholder="Ask AI Advisor about your campaigns..."
                    className="flex-1 bg-[#090b16] border border-gray-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-blue-500"
                  />
                  <button 
                    type="submit"
                    className="p-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg transition"
                  >
                    <Send className="w-3.5 h-3.5" />
                  </button>
                </form>
              </div>

            </div>
          )}

          {/* TAB: SETTINGS */}
          {activeTab === 'settings' && (
            <div className="max-w-xl mx-auto space-y-8">
              
              {/* API Configuration */}
              <div className="glass-panel p-6 rounded-xl space-y-4">
                <div>
                  <h3 className="text-sm font-bold text-white uppercase tracking-wider">Gemini API Configuration</h3>
                  <p className="text-[10px] text-gray-500">Provide your Google Gemini API key to generate customized recommendations.</p>
                </div>
                
                <form onSubmit={saveSettings} className="space-y-4">
                  <div className="space-y-1">
                    <label className="text-xs text-gray-400 font-semibold block">Gemini API Key:</label>
                    <input 
                      type="password"
                      value={geminiKey}
                      onChange={(e) => setGeminiKey(e.target.value)}
                      placeholder="AIzaSy..."
                      className="w-full bg-gray-900 border border-gray-700 text-xs rounded px-3 py-2 text-white focus:outline-none focus:ring-1 focus:ring-blue-500"
                    />
                  </div>
                  
                  <button 
                    type="submit"
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-xs font-semibold text-white rounded transition shadow-lg shadow-blue-900/20"
                  >
                    Save API Configuration
                  </button>
                </form>
              </div>

              {/* Platform Diagnostic Info */}
              <div className="glass-panel p-6 rounded-xl space-y-4">
                <h3 className="text-sm font-bold text-white uppercase tracking-wider">Cloud Infrastructure Status</h3>
                
                <div className="space-y-3 font-mono text-xs text-gray-400">
                  <div className="flex justify-between border-b border-gray-800 pb-2">
                    <span>LocalStack Connectivity:</span>
                    <span className={cloudConnected ? 'text-green-500 font-semibold' : 'text-amber-500 font-semibold'}>
                      {cloudConnected ? 'CONNECTED' : 'DISCONNECTED (Fallback Active)'}
                    </span>
                  </div>
                  <div className="flex justify-between border-b border-gray-800 pb-2">
                    <span>S3 Dataset Bucket:</span>
                    <span>forecast-ai-datasets</span>
                  </div>
                  <div className="flex justify-between border-b border-gray-800 pb-2">
                    <span>S3 Reports Bucket:</span>
                    <span>forecast-ai-reports</span>
                  </div>
                  <div className="flex justify-between border-b border-gray-800 pb-2">
                    <span>DynamoDB Table:</span>
                    <span>forecast-ai-campaigns</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Serverless adapter:</span>
                    <span>Mangum (AWS API Gateway to FastAPI)</span>
                  </div>
                </div>
              </div>

            </div>
          )}

        </main>
      </div>
    </div>
  );
}

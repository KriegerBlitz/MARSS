from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from datetime import datetime, timedelta
import yfinance as yf
import pytz
import sys
import os

app = FastAPI(title="Macro Portfolio Shift API")

# Enable CORS for the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- SILENCER ---
class SuppressPrints:
    def __enter__(self):
        self._stdout, self._stderr = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = open(os.devnull, 'w'), open(os.devnull, 'w')
    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout, sys.stderr = self._stdout, self._stderr

# --- DATA MODELS ---
class NewsEvent(BaseModel):
    event_id: str
    article_title: str
    timestamp: datetime
    # REMOVED: ticker (Because the event now applies to the whole portfolio)

class PortfolioItem(BaseModel):
    ticker: str
    quantity: float

class DashboardRequest(BaseModel):
    portfolio: List[PortfolioItem]
    events: List[NewsEvent]

# --- HELPER FUNCTIONS ---
def get_baseline_price(ticker: str, target_dt: datetime) -> float:
    t_obj = yf.Ticker(ticker)
    with SuppressPrints():
        start_search = target_dt - timedelta(minutes=10)
        end_search = target_dt + timedelta(minutes=10)
        hist = t_obj.history(start=start_search, end=end_search, interval="1m")
        
        if not hist.empty:
            past_data = hist[hist.index <= target_dt]
            if not past_data.empty: return float(past_data.iloc[-1]['Close'])
            return float(hist.iloc[0]['Close'])
            
        start_daily = target_dt - timedelta(days=7) 
        end_daily = target_dt + timedelta(days=1)
        hist_daily = t_obj.history(start=start_daily, end=end_daily, interval="1d")
        
        if not hist_daily.empty:
            past_daily = hist_daily[hist_daily.index <= target_dt]
            if not past_daily.empty: return float(past_daily.iloc[-1]['Close'])
            return float(hist_daily.iloc[0]['Close'])
    return 0.0

# --- ENDPOINTS ---
@app.post("/api/dashboard/live-refresh")
def get_live_dashboard(req: DashboardRequest):
    dashboard_data = {
        "macro_events_impact": []
    }

    # 1. Fetch Live Prices ONCE for the whole portfolio (Saves massive time)
    live_prices = {}
    for item in req.portfolio:
        with SuppressPrints():
            try:
                live_prices[item.ticker] = float(yf.Ticker(item.ticker).fast_info['last_price'])
            except:
                live_prices[item.ticker] = 0.0

    # 2. Evaluate EVERY event against EVERY asset in the portfolio
    for event in req.events:
        event_total_impact = 0.0
        portfolio_impact_list = []
        
        for item in req.portfolio:
            base_price = get_baseline_price(item.ticker, event.timestamp)
            live_price = live_prices.get(item.ticker, 0.0)
            
            shift_pct = 0.0
            shift_value = 0.0
            
            if base_price > 0 and live_price > 0:
                shift_pct = ((live_price - base_price) / base_price) * 100
                shift_value = (live_price - base_price) * item.quantity
                event_total_impact += shift_value

            portfolio_impact_list.append({
                "ticker": item.ticker,
                "quantity": item.quantity,
                "baseline_price": round(base_price, 2),
                "live_price": round(live_price, 2),
                "shift_pct": round(shift_pct, 2),
                "asset_value_impact": round(shift_value, 2),
                "status": "Active" if base_price > 0 else "Market Closed/No Data"
            })

        # 3. Package the event with its cross-asset impact
        dashboard_data["macro_events_impact"].append({
            "event_id": event.event_id,
            "article_title": event.article_title,
            "timestamp": event.timestamp,
            "total_event_value_impact": round(event_total_impact, 2),
            "portfolio_impact": portfolio_impact_list
        })

    return dashboard_data
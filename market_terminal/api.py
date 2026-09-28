from __future__ import annotations

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from .data import NIFTY50, screener, stock_snapshot, history

app = FastAPI(title="NSE Market Terminal", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
def home(): return FileResponse(STATIC_DIR / "index.html")

@app.get("/api/health")
def health(): return {"status":"UP"}

@app.get("/api/screener")
def get_screener(
    min_fall: float = Query(0, ge=0), max_rsi: float = Query(100, le=100),
    min_volume_ratio: float = Query(0, ge=0)
):
    rows=screener()
    return {"count":len(rows),"data":[r for r in rows if r["fall_pct"]>=min_fall and r["rsi"]<=max_rsi and r["volume_ratio"]>=min_volume_ratio]}

@app.get("/api/stock/{ticker}")
def get_stock(ticker: str):
    row=stock_snapshot(ticker.upper())
    if not row: return {"error":"Insufficient EOD data"}
    return row

@app.get("/api/option-chain/{ticker}")
def get_option_chain(ticker: str):
    import yfinance as yf
    tk=yf.Ticker(ticker.upper()+".NS")
    expiries=list(tk.options or [])
    if not expiries: return {"symbol":ticker.upper(),"expiries":[],"data":[]}
    expiry=expiries[0]
    chain=tk.option_chain(expiry)
    calls=chain.calls[["strike","lastPrice","volume","openInterest","impliedVolatility"]].fillna(0).to_dict("records")
    puts=chain.puts[["strike","lastPrice","volume","openInterest","impliedVolatility"]].fillna(0).to_dict("records")
    return {"symbol":ticker.upper(),"expiry":expiry,"expiries":expiries,"calls":calls,"puts":puts}

@app.get("/api/universe")
def universe(): return {"symbols":NIFTY50}

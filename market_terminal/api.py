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
    key=ticker.upper()
    yf_symbol={"NIFTY":"^NSEI","BANKNIFTY":"^NSEBANK"}.get(key, key+".NS")
    tk=yf.Ticker(yf_symbol)
    expiries=list(tk.options or [])
    if not expiries: return {"symbol":ticker.upper(),"expiries":[],"data":[]}
    expiry=expiries[0]
    chain=tk.option_chain(expiry)
    calls=chain.calls[["strike","lastPrice","volume","openInterest","impliedVolatility"]].fillna(0).to_dict("records")
    puts=chain.puts[["strike","lastPrice","volume","openInterest","impliedVolatility"]].fillna(0).to_dict("records")
    return {"symbol":ticker.upper(),"expiry":expiry,"expiries":expiries,"calls":calls,"puts":puts}

@app.get("/api/atm-premium/{ticker}")
def atm_premium(ticker: str):
    import yfinance as yf
    key=ticker.upper(); yf_symbol={"NIFTY":"^NSEI","BANKNIFTY":"^NSEBANK"}.get(key, key+".NS")
    tk=yf.Ticker(yf_symbol); expiries=list(tk.options or [])
    if not expiries: return {"symbol":key,"expiries":[],"data":[]}
    expiry=expiries[0]; chain=tk.option_chain(expiry)
    calls=chain.calls.dropna(subset=["strike","lastPrice"]); puts=chain.puts.dropna(subset=["strike","lastPrice"])
    spot=float(tk.history(period="5d")["Close"].dropna().iloc[-1])
    strikes=sorted(set(calls["strike"].tolist()) & set(puts["strike"].tolist()))
    strike=min(strikes,key=lambda x:abs(x-spot)) if strikes else None
    if strike is None: return {"symbol":key,"expiry":expiry,"spot":round(spot,2),"atm_strike":None,"atm_premium":None}
    call=float(calls.loc[calls["strike"]==strike,"lastPrice"].iloc[0]); put=float(puts.loc[puts["strike"]==strike,"lastPrice"].iloc[0])
    return {"symbol":key,"expiry":expiry,"spot":round(spot,2),"atm_strike":strike,"call_premium":round(call,2),"put_premium":round(put,2),"atm_premium":round(call+put,2),"lower_range":round(spot-call-put,2),"upper_range":round(spot+call+put,2)}

@app.get("/api/universe")
def universe(): return {"symbols":NIFTY50}

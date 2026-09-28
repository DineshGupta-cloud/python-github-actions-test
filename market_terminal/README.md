# NSE Market Terminal

EQSIS-style market-analysis workspace added without copying EQSIS source code, branding, or proprietary content.

## Included
- EOD NIFTY 50 stock screener
- 52-week fall, RSI, EMA 9/25/99 and volume filters
- Top-movers dashboard
- Option-chain view with OI/LTP
- ATM premium and expected-range API
- Strategy Builder workspace
- FastAPI REST backend
- Responsive web UI

## Run

```bash
pip install -r requirements.txt
python -m market_terminal
```

Open http://127.0.0.1:8000

## API
- GET /api/health
- GET /api/screener
- GET /api/stock/{ticker}
- GET /api/option-chain/{ticker}
- GET /api/atm-premium/{ticker}
- GET /api/universe

Data is fetched from Yahoo Finance for EOD/option-chain prototyping. Replace the provider with an authorized NSE/vendor feed before production deployment.

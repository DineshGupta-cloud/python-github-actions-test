# Python GitHub Actions Test

A production-style Python application foundation with automated testing and scheduled execution through GitHub Actions.

## Project structure

```text
app/
├── main.py
├── config.py
├── services/
│   └── scanner_service.py
├── models/
│   └── result.py
└── utils/
    └── logger.py

tests/
└── test_main.py
```

## Run locally

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -m app.main
pytest -v
```

## Configuration

Environment variables:

- `APP_ENV` — application environment, defaults to `development`
- `LOG_LEVEL` — logging level, defaults to `INFO`

## GitHub Actions

- `Python Tests` runs on push, pull request, and manual dispatch.
- `Python Scheduled Runner` runs the application on a 15-minute schedule and can be started manually.

GitHub-hosted runners are temporary. The scheduled workflow is automation, not a permanent 24/7 process.

## Roadmap

1. Application foundation and tests
2. NSE/F&O market-data service
3. EMA 9/25/99 calculations
4. ATH fall and crossover screening
5. CSV/JSON results
6. Telegram notifications
7. Market-hours scheduling and production error handling

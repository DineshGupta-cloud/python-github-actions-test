# Python GitHub Actions Test

A small Python project demonstrating automated testing and scheduled execution with GitHub Actions.

## Local test

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
pytest -v
```

## Run application

```bash
python -m app.main
```

## GitHub Actions

- `Python Tests` runs on every push, pull request, and manual dispatch.
- `Python Scheduled Runner` can be started manually and runs every 15 minutes on GitHub's schedule.

GitHub-hosted Actions jobs are temporary; the scheduled workflow is not a permanent 24/7 process.

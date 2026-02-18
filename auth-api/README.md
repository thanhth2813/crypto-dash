# auth-api

FastAPI authentication API (skeleton).

## Run (dev)

```bash
cd auth-api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open:
- http://localhost:8000/docs

# Query Intelligence — FastAPI skeleton

Run:

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# set GOOGLE_API_KEY in .env
uvicorn main:app --reload
```

POST /queries expects JSON `{ "query": "..." }` and returns 202 with `id`.
Check GET /queries/{id} to fetch status and results.

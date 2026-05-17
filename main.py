import os
from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv()

from db.database import create_db_and_tables

app = FastAPI(title="Query Intelligence")


@app.on_event("startup")
async def on_startup():
    if not os.getenv("GOOGLE_API_KEY"):
        raise RuntimeError("GOOGLE_API_KEY not set in environment")
    await create_db_and_tables()


from routers import queries
app.include_router(queries.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

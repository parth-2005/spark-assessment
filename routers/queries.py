import os
import json
import asyncio
from datetime import datetime
from fastapi import APIRouter, HTTPException
from sqlmodel import select

from db.database import get_session
from db.models import Query as QueryModel
from agent.loop import run_agent
from schemas.query import QueryRequest, QueryResponse

router = APIRouter()


@router.post("/queries", status_code=202)
async def create_query(req: QueryRequest):
    q = req.query.strip()
    if len(q) < 10 or len(q) > 1000:
        raise HTTPException(status_code=400, detail="query must be 10-1000 chars")

    async with get_session() as session:
        dbq = QueryModel(raw_query=q, status="processing", llm_provider=os.getenv("LLM_PROVIDER"))
        session.add(dbq)
        await session.commit()
        await session.refresh(dbq)

    # Schedule background processing without blocking the request
    asyncio.create_task(_process_query(dbq.id))

    return {"id": dbq.id, "status": dbq.status}


@router.get("/queries/{query_id}", response_model=QueryResponse)
async def get_query(query_id: str):
    async with get_session() as session:
        statement = select(QueryModel).where(QueryModel.id == query_id)
        result = await session.execute(statement)
        dbq = result.scalar_one_or_none()
        if not dbq:
            raise HTTPException(status_code=404, detail="not found")

        # prepare response
        resp = QueryResponse(
            id=dbq.id,
            status=dbq.status,
            raw_query=dbq.raw_query,
            llm_provider=dbq.llm_provider,
            intent=dbq.intent,
            entities=json.loads(dbq.entities) if dbq.entities else None,
            intelligence=json.loads(dbq.intelligence) if dbq.intelligence else None,
            sources=json.loads(dbq.sources) if dbq.sources else None,
            created_at=dbq.created_at,
            completed_at=dbq.completed_at,
        )
        return resp


async def _process_query(query_id: str):
    try:
        async with get_session() as session:
            statement = select(QueryModel).where(QueryModel.id == query_id)
            result = await session.execute(statement)
            dbq = result.scalar_one_or_none()
            if not dbq:
                return

            structured, sources = await run_agent(dbq.raw_query)

            dbq.intelligence = json.dumps(structured.get("intelligence") if isinstance(structured, dict) else structured)
            dbq.intent = structured.get("intent") if isinstance(structured, dict) else None
            dbq.entities = json.dumps(structured.get("entities") if isinstance(structured, dict) else None)
            dbq.sources = json.dumps(sources)
            dbq.status = "completed"
            dbq.completed_at = datetime.utcnow()

            session.add(dbq)
            await session.commit()
    except Exception as exc:
        async with get_session() as session:
            statement = select(QueryModel).where(QueryModel.id == query_id)
            result = await session.execute(statement)
            dbq = result.scalar_one_or_none()
            if dbq:
                dbq.status = "failed"
                dbq.error = str(exc)
                await session.commit()

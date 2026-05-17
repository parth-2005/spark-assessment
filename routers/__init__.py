from fastapi import APIRouter

router = APIRouter()

from . import queries  # noqa: E402,F401
router.include_router(queries.router)

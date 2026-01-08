from fastapi import APIRouter, Depends, HTTPException, Query, Request 
from schemas.analysis_sc import AnalyticsResponse 
from services.analysis_services import AnalyticsService 
from db import db 
from slowapi import Limiter 
from slowapi.util import get_remote_address 
from security import get_current_user 
limiter = Limiter(key_func=get_remote_address) 
router = APIRouter(prefix="/analysis", tags=["Analytics"]) 
@router.get("/{user_id}", response_model=AnalyticsResponse)
async def get_user_analysis(
    request: Request,
    user_id: str,
    period: str = Query("7d", regex="^(1d|7d|30d|90d)$"),
    current_user=Depends(get_current_user),
):
    if user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Unauthorized")

    service = AnalyticsService(db)
    return await service.get_analytics(user_id, period)


from fastapi import APIRouter, Depends, UploadFile, File
from db import get_db, get_fs_bucket
from security import get_current_user
from services.hr_service import HRService
from services.hr_audio_service import save_audio
from typing import Any
router = APIRouter(prefix="/hr", tags=["HR"])

@router.get("/questions")
async def get_hr_questions(db: Any = Depends(get_db)):
    service = HRService(db)
    return {"questions": await service.get_questions()}

@router.get("/progress")
async def get_progress(
    user: dict = Depends(get_current_user),
    db: Any = Depends(get_db)
):
    service = HRService(db)
    return await service.get_progress(user["id"])

@router.post("/complete")
async def complete_question(
    payload: dict,
    user: dict = Depends(get_current_user),
    db: Any = Depends(get_db)
):
    service = HRService(db)
    await service.mark_completed(
        user["id"],
        payload["question_id"],
        payload["duration"]
    )
    return {"status": "ok"}


@router.post("/upload-audio")
async def upload_audio(
    question_id: str,
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user)
):
    fs = get_fs_bucket()

    file_id = await fs.upload_from_stream(
        filename=f"{user['id']}_{question_id}.webm",
        source=await file.read(),
        metadata={
            "user_id": user["id"],
            "question_id": question_id
        }
    )

    return {
        "message": "Audio uploaded successfully",
        "file_id": str(file_id)
    }


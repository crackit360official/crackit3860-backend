from datetime import datetime

async def save_audio(fs, user_id, question_id, file):
    file_id = await fs.upload_from_stream(
        filename=f"{user_id}_{question_id}.webm",
        source=file.file,
        metadata={
            "user_id": user_id,
            "question_id": question_id,
            "created_at": datetime.utcnow()
        }
    )
    return file_id

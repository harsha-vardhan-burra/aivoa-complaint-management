from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "AIVOA Complaint Management Backend",
        "message": "Backend is operational and ready for Phase 2."
    }

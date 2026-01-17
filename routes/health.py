from fastapi import APIRouter
from config import settings
import requests

router = APIRouter()

GPU_SERVICE_URL = settings.GPU_SERVICE_URL
HF_ACCESS_TOKEN = settings.HF_ACCESS_TOKEN
TIMEOUT_SECONDS = 2.0


@router.get("/api/health", tags=["health"])
def health_check():
    # gpu_status = "healthy"  # Placeholder for GPU service status
    gpu_status = "unknown"
    try:
        resp = requests.get(
            f"{GPU_SERVICE_URL}/health",
            timeout=TIMEOUT_SECONDS,
            headers={"Authorization": f"Bearer {HF_ACCESS_TOKEN}"},
        )

        if resp.status_code == 200:
            gpu_status = "healthy"
        else:
            gpu_status = "unhealthy"

    except requests.exceptions.Timeout:
        gpu_status = "timeout"

    except requests.exceptions.ConnectionError:
        gpu_status = "unreachable"

    except requests.exceptions.RequestException:
        gpu_status = "error"

    overall_status = "healthy" if gpu_status == "healthy" else "degraded"

    return {
        "status": overall_status,
        "services": {
            "api": "healthy",
            "gpu_service": gpu_status,
        },
    }

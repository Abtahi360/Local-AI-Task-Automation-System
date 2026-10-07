"""GET /api/v1/system/info."""

from __future__ import annotations

import platform
from typing import Annotated

from fastapi import APIRouter, Depends

from backend import PHASE, __version__
from backend.api.deps import get_app_settings
from backend.api.prefix import API_PREFIX
from backend.core.config import Settings
from backend.schemas.system import SystemInfoResponse

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/info", response_model=SystemInfoResponse)
def system_info(settings: Annotated[Settings, Depends(get_app_settings)]) -> SystemInfoResponse:
    return SystemInfoResponse(
        app_name=settings.app_name,
        version=__version__,
        phase=PHASE,
        environment=settings.app_env,
        python_version=platform.python_version(),
        platform=platform.system(),
        host=settings.app_host,
        port=settings.app_port,
        local_only=settings.local_only,
        api_prefix=API_PREFIX,
    )

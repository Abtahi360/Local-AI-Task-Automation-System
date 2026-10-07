"""``python -m backend`` - start the local API server with Uvicorn."""

from __future__ import annotations

import argparse

import uvicorn

from backend.core.config import get_settings


def main() -> None:
    parser = argparse.ArgumentParser(description="Start the Local AI Task Automation API.")
    parser.add_argument("--reload", action="store_true", help="auto-reload on code changes (dev)")
    args = parser.parse_args()

    settings = get_settings()
    print(f"Starting {settings.app_name}")
    print(f"Open: http://{settings.app_host}:{settings.app_port}  (Ctrl+C to stop)")
    uvicorn.run(
        "backend.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=args.reload,
        log_config=None,  # our own JSON logging is configured in the app lifespan
    )


if __name__ == "__main__":
    main()

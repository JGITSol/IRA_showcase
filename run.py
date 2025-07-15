#!/usr/bin/env python3
"""Run the application."""

import uvicorn
from app.core.config import settings

def main() -> None:
    """Run the application."""
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )

if __name__ == "__main__":
    main()

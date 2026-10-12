"""Entry point: python -m xsagent"""

import uvicorn

from xsagent.core.config import get_settings


def main() -> None:
    settings = get_settings()
    uvicorn.run(
        "xsagent.api.app:create_app",
        factory=True,
        host=settings.server_host,
        port=settings.server_port,
        reload=settings.debug,
    )


if __name__ == "__main__":
    main()

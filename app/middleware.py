"""Custom middleware for the JustEats application.

Provides:
- Request/response logging with timing information
"""

import time

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = structlog.get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware that logs all HTTP requests with timing information.

    Logs include:
    - HTTP method
    - Request path
    - Response status code
    - Request duration in milliseconds
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request and log timing information.

        Args:
            request: The incoming HTTP request.
            call_next: The next middleware/handler in the chain.

        Returns:
            The response from downstream handlers.
        """
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start) * 1000, 2)

        logger.info(
            "request",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
        )
        return response

"""Logging middleware for FastAPI."""
import time
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("linkml_schema_manager")


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all requests and responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log details."""
        # Generate request ID
        request_id = f"{time.time()}-{id(request)}"

        # Log request
        logger.info(
            f"Request: {request.method} {request.url.path} | "
            f"Request ID: {request_id} | "
            f"Client: {request.client.host if request.client else 'unknown'}"
        )

        # Process request and measure time
        start_time = time.time()
        try:
            response = await call_next(request)
            process_time = time.time() - start_time

            # Log response
            logger.info(
                f"Response: {request.method} {request.url.path} | "
                f"Status: {response.status_code} | "
                f"Duration: {process_time:.3f}s | "
                f"Request ID: {request_id}"
            )

            # Add custom headers
            response.headers["X-Process-Time"] = str(process_time)
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                f"Error: {request.method} {request.url.path} | "
                f"Exception: {str(e)} | "
                f"Duration: {process_time:.3f}s | "
                f"Request ID: {request_id}"
            )
            raise


def setup_logging(log_level: str = "INFO", log_file: str = None):
    """Configure logging for the application."""
    # Create logger
    logger = logging.getLogger("linkml_schema_manager")
    logger.setLevel(getattr(logging, log_level.upper()))

    # Create formatters
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (if log file specified)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger

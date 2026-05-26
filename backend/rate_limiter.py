"""
Rate Limiting - slowapi integration for production
"""
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import FastAPI
from fastapi.responses import JSONResponse

limiter = Limiter(key_func=get_remote_address)


def setup_rate_limiter(app: FastAPI):
    """Setup rate limiting on FastAPI app"""
    
    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(request, exc):
        return JSONResponse(
            status_code=429,
            content={
                "success": False,
                "detail": "Too many requests. Please try again later.",
                "retry_after": exc.retry_after if hasattr(exc, 'retry_after') else 60
            }
        )
    
    app.state.limiter = limiter
    return app

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import database
from routes import topics, arguments, summaries, fact_checking, voting
import logging
import traceback
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize database
database.init_db()
# Run migration to add validity columns
database.migrate_add_validity_columns()
# Run migration to add votes column
database.migrate_add_votes_column()

# Create FastAPI app
app = FastAPI(title="Debately API", version="1.0.0")

# Add exception handler for validation errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Log validation errors with full details."""
    logger.error(f"Validation error on {request.method} {request.url.path}")
    try:
        body = await request.body()
        logger.error(f"Request body: {body.decode('utf-8', errors='ignore')}")
    except:
        logger.error("Could not read request body")
    logger.error(f"Validation errors: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()}
    )

# Add exception handler for HTTP exceptions
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Log all exceptions with full traceback."""
    logger.error(f"Exception on {request.method} {request.url.path}")
    logger.error(f"Exception type: {type(exc).__name__}")
    logger.error(f"Exception message: {str(exc)}")
    logger.error(f"Traceback:\n{traceback.format_exc()}")
    
    # Re-raise HTTPException to preserve status codes
    from fastapi import HTTPException
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail}
        )
    
    # For other exceptions, return 500
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": f"Internal server error: {str(exc)}"}
    )

# Add logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests and responses."""
    logger.info(f"{request.method} {request.url.path}")
    
    # Read and log request body for POST/PUT/PATCH
    if request.method in ["POST", "PUT", "PATCH"]:
        body = await request.body()
        if body:
            try:
                import json
                body_json = json.loads(body)
                logger.info(f"Request body: {json.dumps(body_json, indent=2)}")
            except:
                logger.info(f"Request body (raw): {body.decode('utf-8', errors='ignore')}")
        
        # Recreate request with body for downstream handlers
        async def receive():
            return {"type": "http.request", "body": body}
        request._receive = receive
    
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response

# Enable CORS
# Get allowed origins from environment variable (comma-separated) or default to *
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",") if os.getenv("ALLOWED_ORIGINS") else ["*"]
# Remove empty strings and strip whitespace
allowed_origins = [origin.strip() for origin in allowed_origins if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,  # In production, set ALLOWED_ORIGINS env var
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(topics.router)
app.include_router(arguments.router)
app.include_router(summaries.router)
app.include_router(fact_checking.router)
app.include_router(voting.router)

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Debate Platform API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring and load balancers."""
    try:
        # Check database connection
        conn = database.get_db_connection()
        conn.close()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "database": "disconnected", "error": str(e)}
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

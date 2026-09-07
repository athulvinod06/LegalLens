"""
LegalLens — FastAPI Backend Application Entrypoint
Constitutional Disclaimer: Automated first-pass review tool; not legal advice.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="LegalLens API",
    description="AI-Powered Contract Intelligence Platform (Academic MCA Mini Project)",
    version="0.1.0",
)

# Configure CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["Health"])
@app.get("/api/health", tags=["Health"])
def health_check():
    """
    Service health-check endpoint.
    Verifies service availability and carries the mandatory legal disclaimer.
    """
    return {
        "status": "healthy",
        "app": "LegalLens",
        "version": "0.1.0",
        "disclaimer": "LegalLens is an automated first-pass contract analysis tool. It does not provide legal advice.",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=True)

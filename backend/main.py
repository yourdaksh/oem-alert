import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="OEM Alert Platform API",
    description="Backend subsystem for vulnerability reporting, CRM management, and scraping.",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health_check():
    return {"status": "ok", "service": "OEM Alert Platform API"}

from backend.routes import auth, vulnerabilities, organizations, tasks, payments

app.include_router(auth.router)
app.include_router(vulnerabilities.router)
app.include_router(organizations.router)
app.include_router(tasks.router)
app.include_router(payments.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)

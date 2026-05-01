import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import init_db
from routers import emails, applications, queue, dashboard, poll, ai

# Load environment variables
load_dotenv()

app = FastAPI(title="JobRadar API")
app.include_router(emails.router)
app.include_router(applications.router)
app.include_router(queue.router)
app.include_router(dashboard.router)
app.include_router(poll.router)
app.include_router(ai.router)

# Enable CORS for frontend connectivity
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    init_db()
    print("JobRadar backend started")

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": "jobradar-backend"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

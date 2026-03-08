import os
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from app.genai.router import router as genai_router


# 🚀 1. Tell Python to go up one folder and read the root .env file
load_dotenv("../.env")

app = FastAPI(title="TEDD GenAI Service")

# Only add /gen prefix here (NOT in router.py)
app.include_router(genai_router, prefix="/gen", tags=["GenAI"])

@app.get("/")
def health_check():
    return {"message": "TEDD GenAI Service is running"}

# 🚀 2. The custom startup logic that forces Uvicorn to use your .env port
if __name__ == "__main__":
    # It will look for GEN_AI_PORT in your .env, and fall back to 8001 just in case
    target_port = int(os.environ.get("GEN_AI_PORT"))
    
    print(f"\n⚡ TEDD GenAI Service booting up on Port {target_port}...\n")
    
    uvicorn.run("app.main:app", host="0.0.0.0", port=target_port, reload=True)
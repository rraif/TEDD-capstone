from fastapi import FastAPI
from app.genai.router import router as genai_router

app = FastAPI(title="TEDD GenAI Service")

# Only add /gen prefix here (NOT in router.py)
app.include_router(genai_router, prefix="/gen", tags=["GenAI"])

@app.get("/")
def health_check():
    return {"message": "TEDD GenAI Service is running"}
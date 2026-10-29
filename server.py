from fastapi import FastAPI, UploadFile, File
import shutil
import os
from voice_guard import VoiceGuard

app = FastAPI(
    title="VoiceGuard Enterprise API",
    description="On-Premises & Cloud Voice Authenticity Gateway",
    version="1.0.0"
)

guard = VoiceGuard()

@app.get("/")
def home():
    return {"status": "online", "engine": "VoiceGuard-v1"}

@app.post("/v1/verify")
async def verify_audio(file: UploadFile = File(...)):
    temp_path = f"temp_{file.filename}"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    result = guard.verify(temp_path)
    
    if os.path.exists(temp_path):
        os.remove(temp_path)
        
    return result

if __name__ == "__main__":
    import uvicorn
    # Use cloud port if available, otherwise default to 8000
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

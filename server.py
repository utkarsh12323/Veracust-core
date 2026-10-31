from fastapi import FastAPI, UploadFile, File
import shutil
import os
import json
from datetime import datetime
from voice_guard import VoiceGuard

app = FastAPI(
    title="Acoustiq Labs Enterprise API",
    description="Tri-Vector Real-Time Audio Authenticity Gateway",
    version="2.0.0"
)

guard = VoiceGuard()

# Persistent audit log file
AUDIT_LOG_FILE = "audit_log.json"

def log_verification(filename: str, verdict: str, risk_score: float):
    """Logs verification metadata without saving the sensitive audio."""
    log_entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "file_name": filename,
        "verdict": verdict,
        "risk_score": risk_score
    }
    
    logs = []
    if os.path.exists(AUDIT_LOG_FILE):
        try:
            with open(AUDIT_LOG_FILE, "r") as f:
                logs = json.load(f)
        except Exception:
            logs = []
            
    logs.append(log_entry)
    
    with open(AUDIT_LOG_FILE, "w") as f:
        json.dump(logs, f, indent=4)

@app.get("/")
def home():
    total_scanned = 0
    if os.path.exists(AUDIT_LOG_FILE):
        try:
            with open(AUDIT_LOG_FILE, "r") as f:
                total_scanned = len(json.load(f))
        except Exception:
            pass
    return {
        "status": "online",
        "engine": "AcoustiqLabs-TriVector-v2",
        "total_streams_audited": total_scanned
    }

@app.get("/v1/stats", summary="View Enterprise Usage Analytics")
def get_stats():
    """Returns the total number of audio streams audited and fraud breakdown."""
    if not os.path.exists(AUDIT_LOG_FILE):
        return {"total_inspections": 0, "synthetic_detected": 0, "authentic_human": 0}
        
    try:
        with open(AUDIT_LOG_FILE, "r") as f:
            logs = json.load(f)
            
        synthetic_count = sum(1 for entry in logs if entry.get("verdict") == "SYNTHETIC_DETECTED")
        human_count = sum(1 for entry in logs if entry.get("verdict") == "AUTHENTIC_HUMAN")
        
        return {
            "total_inspections": len(logs),
            "synthetic_detected": synthetic_count,
            "authentic_human": human_count,
            "recent_audit_trail": logs[-10:] # Shows last 10 audit records
        }
    except Exception as e:
        return {"error": str(e)}

@app.post("/v1/verify", summary="Verify Audio Stream Authenticity")
async def verify_audio(file: UploadFile = File(...)):
    temp_path = f"temp_{file.filename}"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    result = guard.verify(temp_path)
    
    # Clean up the audio file immediately (Never store customer voice data!)
    if os.path.exists(temp_path):
        os.remove(temp_path)
        
    # Log the verification metadata safely
    if "verdict" in result:
        log_verification(file.filename, result["verdict"], result.get("risk_score", 0.0))
        
    return result

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

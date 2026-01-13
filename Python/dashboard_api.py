import sys
import os
sys.path.append(os.path.dirname(__file__))

FILE: dashboard_api.py
STRATEGY VERSION: v2.0
"""
import sqlite3
from fastapi import FastAPI
from fastapi.responses import FileResponse
from the.state_manager import state_engine
from the.event_logger import EventLogger

app = FastAPI()
event_logger = EventLogger()

@app.get("/")
async def read_index():
    return FileResponse('index.html')

@app.get("/health")
async def get_health():
    state = state_engine.get_state()
    return {"ready": True, "status": "SYSTEM READY - STRATEGY V2.0", "health_data": state["system_health"]}

@app.get("/status")
async def get_status():
    state = state_engine.get_state()
    # Mock performance v2
    perf = {"win_rate": 68.5, "total": 124, "avg_rr": "1:1.5", "drawdown": "2.1%"}
    
    return {
        "mode": state["system_mode"],
        "daily_pnl": state["daily_loss"]["current"],
        "thinking": state["bot_thinking"],
        "performance": perf,
        "health": state["system_health"],
        "version": "v2.0"
    }

@app.get("/logs/recent")
async def get_recent_logs():
    return event_logger.get_recent_logs(15)

@app.get("/trades/active")
async def get_active_trades():
    return list(state_engine.get_state()["active_trades"].values())

@app.get("/trades/closed")
async def get_closed_trades():
    try:
        conn = sqlite3.connect("trading_bot_audit.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM trades ORDER BY exit_time DESC LIMIT 10")
        return [dict(r) for r in cursor.fetchall()]
    except: return []

if __name__ == "__main__":
    import os
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)


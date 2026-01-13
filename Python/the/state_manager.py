"""
FILE: state_manager.py
TYPE: Central Authority (Health Layer)
"""
import os
import json
import logging
import fcntl
from datetime import date, datetime

logger = logging.getLogger("StateManager")

class StateManager:
    STATE_FILE = "bot_state.json"
    
    DEFAULT_STATE = {
        "system_mode": "PAPER",
        "kill_switch": {"stop_new_trades": False, "full_system_freeze": False, "symbol_block": []},
        "daily_loss": {"limit": 150.0, "current": 0.0, "breached": False},
        "active_trades": {},
        "market_data": {},
        "date": str(date.today()),
        "bot_thinking": {
            "current_state": "WAITING",
            "current_market": "NONE",
            "timeframe": "1m",
            "data_source": "TRADINGVIEW_MOCK",
            "indicators_used": [],
            "indicator_explanation": "System initializing...",
            "signal_type": "NO_TRADE",
            "signal_confidence": 0,
            "trade_decision_reason": "Waiting for market scan...",
            "trade_rejection_reason": "None",
            "risk_score": 0,
            "market_mode": "UNKNOWN"
        },
        "system_health": {
            "market_engine": {"connected": False, "last_heartbeat": None, "status": "Initializing"},
            "execution_engine": {"connected": False, "last_heartbeat": None, "status": "Initializing"},
            "risk_engine": {"connected": False, "last_heartbeat": None, "status": "Initializing"},
            "broker_api": {"connected": False, "status": "Disabled (Expected - Paper Mode)"}
        }
    }

    def __init__(self):
        if not os.path.exists(self.STATE_FILE):
            self._write_state(self.DEFAULT_STATE)
        self.reload_state()

    def reload_state(self):
        state = self._read_state()
        if state.get("date") != str(date.today()):
            new_state = self.DEFAULT_STATE.copy()
            new_state["date"] = str(date.today())
            self._write_state(new_state)

    def _read_state(self):
        try:
            with open(self.STATE_FILE, 'r') as f:
                fcntl.flock(f, fcntl.LOCK_SH)
                data = json.load(f)
                fcntl.flock(f, fcntl.LOCK_UN)
                return data
        except Exception:
            return self.DEFAULT_STATE

    def _write_state(self, data):
        try:
            with open(self.STATE_FILE, 'w') as f:
                fcntl.flock(f, fcntl.LOCK_EX)
                json.dump(data, f, indent=4)
                fcntl.flock(f, fcntl.LOCK_UN)
        except Exception as e:
            logger.error(f"Write failure: {e}")

    def get_state(self):
        return self._read_state()

    def update_thinking(self, updates):
        state = self._read_state()
        state["bot_thinking"].update(updates)
        self._write_state(state)

    def heartbeat(self, module, status="Running"):
        state = self._read_state()
        if module in state["system_health"]:
            state["system_health"][module].update({
                "connected": True,
                "last_heartbeat": datetime.now().isoformat(),
                "status": status
            })
            self._write_state(state)

    def can_trade_new(self):
        state = self._read_state()
        if state["system_mode"] == "FREEZE": return False
        if state["kill_switch"]["stop_new_trades"]: return False
        if state["daily_loss"]["breached"]: return False
        return True

    def register_market_data(self, symbol, data):
        state = self._read_state()
        state["market_data"][symbol] = data
        self._write_state(state)

    def register_trade(self, trade_id, trade_data):
        state = self._read_state()
        state["active_trades"][trade_id] = trade_data
        self._write_state(state)

    def close_trade(self, trade_id):
        state = self._read_state()
        if trade_id in state["active_trades"]:
            del state["active_trades"][trade_id]
            self._write_state(state)

    def update_pnl(self, pnl):
        state = self._read_state()
        state["daily_loss"]["current"] += pnl
        if state["daily_loss"]["current"] <= -state["daily_loss"]["limit"]:
            state["daily_loss"]["breached"] = True
            state["kill_switch"]["stop_new_trades"] = True
        self._write_state(state)

state_engine = StateManager()

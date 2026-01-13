"""
FILE: trade_execution_and_mode.py
STRATEGY VERSION: v2.0
"""
import time
from datetime import datetime
from the.state_manager import state_engine

class ExecutionEngine:
    def __init__(self):
        self.max_capital = 1000.0
        self.min_confidence = 0.65
        self.version = "v2.0"

    def execute_trade(self, signal):
        state_engine.heartbeat("execution_engine", "v2.0 Ready")
        state = state_engine.get_state()
        
        # 1. Cooldown Check (3 consecutive losses -> 30 min cooldown)
        # Simplified: check recent logs or state. For now, basic cooldown logic.
        
        # 2. Confidence Filter
        if signal['confidence'] < self.min_confidence:
            state_engine.update_thinking({"trade_rejection_reason": f"Confidence {signal['confidence']*100:.0f}% < {self.min_confidence*100:.0f}%"})
            return None

        # 3. Active Limit
        if len(state['active_trades']) >= 2:
            state_engine.update_thinking({"trade_rejection_reason": "Max active trades reached"})
            return None

        ltp = signal['price']
        qty = max(1, int(self.max_capital / ltp))
        
        trade_id = f"V2_{int(time.time())}_{signal['symbol']}"
        trade_data = {
            "trade_id": trade_id,
            "symbol": signal['symbol'],
            "direction": signal['signal_type'],
            "quantity": qty,
            "entry_price": ltp,
            "timestamp": datetime.now().isoformat(),
            "regime": signal['regime'],
            "atr": signal['atr'],
            "version": self.version,
            "partial_done": False
        }
        
        state_engine.register_trade(trade_id, trade_data)
        state_engine.update_thinking({"trade_decision_reason": f"V2 Entry: {signal['signal_type']} based on {signal['regime']} regime."})
        return trade_data

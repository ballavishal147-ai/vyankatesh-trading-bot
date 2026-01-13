"""
FILE: trade_management_and_risk.py
STRATEGY VERSION: v2.0
"""
import logging
from datetime import datetime
from the.state_manager import state_engine

logger = logging.getLogger("TradeManager")

class TradeManagementEngine:
    def __init__(self, event_logger):
        self.event_logger = event_logger
        self.version = "v2.0"

    def check_exits(self):
        state_engine.heartbeat("risk_engine", "Monitoring v2.0 Risk")
        state = state_engine.get_state()
        active_trades = state.get("active_trades", {})
        market_data = state.get("market_data", {})
        
        now = datetime.now()
        hour, minute = now.hour, now.minute
        
        # Global Time Exit (2:30 PM)
        if (hour == 14 and minute >= 30) or hour > 14:
            if active_trades:
                self.close_all_trades("STRATEGY_TIME_FORCE_EXIT")
            return

        for tid, trade in list(active_trades.items()):
            symbol = trade['symbol']
            if symbol not in market_data: continue
            
            ltp = market_data[symbol]['close']
            entry = trade['entry_price']
            qty = trade['quantity']
            direction = trade['direction']
            regime = trade.get('regime', 'TRENDING')
            atr = trade.get('atr', 0.001)
            
            # 1. Adaptive Stop Loss
            # Trending -> wider (2x ATR), Choppy -> tighter (1x ATR)
            sl_mult = 2.0 if regime == "TRENDING" else 1.2
            sl_dist = entry * atr * sl_mult
            
            # 2. Partial Profit Booking (1R = 1.5x SL distance)
            target_1r = entry + (sl_dist * 1.5) if direction == "BUY" else entry - (sl_dist * 1.5)
            
            pnl_per_unit = (ltp - entry) if direction == "BUY" else (entry - ltp)
            total_pnl = pnl_per_unit * qty
            
            # Logic for Exits
            sl_hit = (direction == "BUY" and ltp <= entry - sl_dist) or (direction == "SELL" and ltp >= entry + sl_dist)
            
            # Partial profit check (if not already partialed)
            if not trade.get('partial_done', False):
                hit_1r = (direction == "BUY" and ltp >= target_1r) or (direction == "SELL" and ltp <= target_1r)
                if hit_1r:
                    self.partial_exit(tid, trade, ltp, 0.5)
                    continue

            if sl_hit:
                self.close_trade(tid, ltp, total_pnl, "ADAPTIVE_SL_HIT")

    def partial_exit(self, trade_id, trade, price, pct):
        exit_qty = int(trade['quantity'] * pct)
        if exit_qty < 1: return
        
        pnl = (price - trade['entry_price']) * exit_qty if trade['direction'] == "BUY" else (trade['entry_price'] - price) * exit_qty
        
        state = state_engine.get_state()
        new_trade = trade.copy()
        new_trade['quantity'] -= exit_qty
        new_trade['partial_done'] = True
        
        state_engine.register_trade(trade_id, new_trade)
        state_engine.update_pnl(pnl)
        
        msg = f"PARTIAL EXIT (50%): Booked ₹{pnl:.2f} profit on {trade['symbol']} at {price:.2f}. Runner active."
        self.event_logger.log_system_event("INFO", "RiskEngine", msg)

    def close_trade(self, trade_id, exit_price, pnl, reason):
        trade = state_engine.get_state()["active_trades"].get(trade_id)
        if not trade: return
        
        state_engine.close_trade(trade_id)
        state_engine.update_pnl(pnl)
        
        msg = f"CLOSED: {trade['symbol']} at {exit_price:.2f} ({reason}). PnL: ₹{pnl:.2f}"
        self.event_logger.log_system_event("INFO", "RiskEngine", msg)

    def close_all_trades(self, reason):
        active_trades = state_engine.get_state().get("active_trades", {})
        market_data = state_engine.get_state().get("market_data", {})
        for tid, trade in list(active_trades.items()):
            ltp = market_data.get(trade['symbol'], {}).get('close', trade['entry_price'])
            pnl = (ltp - trade['entry_price']) * trade['quantity'] if trade['direction'] == "BUY" else (trade['entry_price'] - ltp) * trade['quantity']
            self.close_trade(tid, ltp, pnl, reason)

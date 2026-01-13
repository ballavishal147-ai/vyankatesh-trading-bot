"""
FILE: market_data_and_signal.py
STRATEGY VERSION: v2.0
"""
import logging
import random
import math
from datetime import datetime, timedelta
from the.state_manager import state_engine

logger = logging.getLogger("SignalEngine")

class MarketSignalEngine:
    def __init__(self, config=None):
        self.symbols = ["NIFTY", "BANKNIFTY", "BTCUSDT"]
        self.last_prices = {s: random.uniform(20000, 25000) if "NIFTY" in s else random.uniform(40000, 60000) for s in self.symbols}
        self.price_history = {s: [] for s in self.symbols}
        self.version = "v2.0"

    def fetch_simulated_ohlc(self, symbol):
        base_price = self.last_prices[symbol]
        change = random.uniform(-0.003, 0.003) * base_price
        new_price = base_price + change
        self.last_prices[symbol] = new_price
        
        candle = {
            "symbol": symbol,
            "open": base_price,
            "high": max(base_price, new_price) + random.uniform(0, 10),
            "low": min(base_price, new_price) - random.uniform(0, 10),
            "close": new_price,
            "volume": random.randint(1000, 10000),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        self.price_history[symbol].append(candle)
        if len(self.price_history[symbol]) > 50:
            self.price_history[symbol].pop(0)
            
        return candle

    def detect_regime(self, symbol):
        history = self.price_history[symbol]
        if len(history) < 20: return "UNKNOWN", 0
        
        closes = [c['close'] for c in history]
        ema_fast = sum(closes[-5:]) / 5
        ema_slow = sum(closes[-20:]) / 20
        spread = abs(ema_fast - ema_slow) / ema_slow
        
        # ATR approx
        tr_sum = 0
        for i in range(1, len(history)):
            h, l, pc = history[i]['high'], history[i]['low'], history[i-1]['close']
            tr = max(h - l, abs(h - pc), abs(l - pc))
            tr_sum += tr
        atr_pct = (tr_sum / len(history)) / history[-1]['close']

        if spread > 0.002: regime = "TRENDING"
        elif atr_pct > 0.0015: regime = "VOLATILE"
        else: regime = "SIDEWAYS"
        
        return regime, atr_pct

    def calculate_confidence(self, symbol, candle, direction):
        history = self.price_history[symbol]
        if len(history) < 5: return 0, {}

        # 1. Trend Strength (35%)
        closes = [c['close'] for c in history[-10:]]
        trend_score = 100 if (direction == "BUY" and closes[-1] > closes[0]) or (direction == "SELL" and closes[-1] < closes[0]) else 30
        
        # 2. Volume Alignment (20%)
        avg_vol = sum(c['volume'] for c in history[-10:]) / 10
        vol_score = 100 if candle['volume'] >= 1.2 * avg_vol else 50
        
        # 3. RSI Alignment (20%) - Mock RSI
        rsi = random.randint(30, 70)
        rsi_score = 100 if (direction == "BUY" and rsi < 60) or (direction == "SELL" and rsi > 40) else 40
        
        # 4. Volatility (ATR) (15%)
        regime, atr_pct = self.detect_regime(symbol)
        vola_score = 100 if regime != "VOLATILE" else 40
        
        # 5. Time-of-day (10%)
        now = datetime.now()
        hour, minute = now.hour, now.minute
        time_score = 100
        if hour == 9 and minute < 30: time_score = 0
        elif hour >= 14 and minute >= 30: time_score = 0
        
        total = (trend_score * 0.35) + (vol_score * 0.20) + (rsi_score * 0.20) + (vola_score * 0.15) + (time_score * 0.10)
        
        breakdown = {
            "trend": int(trend_score),
            "volume": int(vol_score),
            "rsi": int(rsi_score),
            "volatility": int(vola_score),
            "time": int(time_score)
        }
        return int(total), breakdown

    def generate_signal(self, symbol):
        candle = self.fetch_simulated_ohlc(symbol)
        history = self.price_history[symbol]
        if len(history) < 2: return None
        
        prev_candle = history[-2]
        regime, atr = self.detect_regime(symbol)
        
        # Entry Filters
        is_buy = candle['close'] > prev_candle['high']
        is_sell = candle['close'] < prev_candle['low']
        
        avg_vol = sum(c['volume'] for c in history[-10:]) / 10
        vol_confirmed = candle['volume'] >= 1.2 * avg_vol
        
        direction = "HOLD"
        rejection = "None"
        
        if is_buy and vol_confirmed: direction = "BUY"
        elif is_sell and vol_confirmed: direction = "SELL"
        else:
            if not vol_confirmed: rejection = "Volume spike < 1.2x average"
            else: rejection = "Price did not break previous candle extremes"

        conf, breakdown = self.calculate_confidence(symbol, candle, direction) if direction != "HOLD" else (0, {})
        
        state_updates = {
            "current_state": "ANALYZING",
            "current_market": symbol,
            "market_mode": regime,
            "signal_confidence": conf,
            "strategy_version": self.version,
            "v2_breakdown": breakdown,
            "trade_rejection_reason": rejection if direction == "HOLD" else "None"
        }
        state_engine.update_thinking(state_updates)
        
        if direction == "HOLD": return None

        return {
            "symbol": symbol,
            "signal_type": direction,
            "confidence": conf / 100.0,
            "price": candle['close'],
            "regime": regime,
            "atr": atr,
            "timestamp": candle['timestamp']
        }

    def scan_market(self):
        state_engine.heartbeat("market_engine", f"Running v2.0 - {datetime.now().strftime('%H:%M:%S')}")
        signals = []
        for s in self.symbols:
            sig = self.generate_signal(s)
            if sig: signals.append(sig)
        return signals

# Replit.md - Trading Bot System

## Overview

This is an intraday paper trading bot system designed for simulating trades on Indian indices (NIFTY, BANKNIFTY) and crypto (BTCUSDT). The system operates entirely in paper trading mode without requiring real broker connections or API credentials.

**Core Purpose:** Simulate trading strategies using TradingView-style market data, execute paper trades, manage risk with stop-losses and time-based exits, and display real-time performance on a web dashboard.

**Key Characteristics:**
- Paper trading only (no real money)
- Simulated market data (no external API keys needed)
- Self-contained system with file-based state persistence
- FastAPI-powered dashboard for monitoring

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Core Pipeline Architecture

The system follows a continuous loop architecture with four distinct stages:

```
Market Data → Signal Generation → Trade Execution → Risk Management
     ↓              ↓                   ↓                  ↓
  (OHLC)        (BUY/SELL)          (Paper Fill)      (SL/Time Exit)
```

**Main Orchestrator** (`main.py`):
- Runs an infinite loop with 2-second intervals
- Coordinates all engines in sequence
- Handles errors gracefully with automatic recovery

### Module Responsibilities

| File | Purpose |
|------|---------|
| `main.py` | Central orchestrator - runs the trading loop |
| `the/market_data_and_signal.py` | Generates simulated OHLC data and trading signals |
| `the/trade_execution_and_mode.py` | Executes paper trades based on signals |
| `the/trade_management_and_risk.py` | Monitors positions, handles stop-losses and exits |
| `the/state_manager.py` | Single source of truth for all system state |
| `the/event_logger.py` | Audit logging with SQLite persistence |
| `the/dashboard_api.py` | FastAPI server for web dashboard |
| `index.html` | Simple trading terminal UI |

### State Management Design

**Chosen Solution:** File-based JSON state (`bot_state.json`) with file locking

**Rationale:**
- No database setup required
- Human-readable for debugging
- Supports concurrent access via `fcntl` locks
- Auto-resets daily (prevents stale data)

**State Structure:**
- `system_mode`: Always "PAPER"
- `kill_switch`: Emergency stop controls
- `daily_loss`: Loss tracking with breach detection
- `active_trades`: Currently open positions
- `market_data`: Latest price snapshots

### Signal Generation Strategy

**Approach:** Simple momentum-based signals
- Compares candle close vs open price
- Calculates confidence score (0-1)
- Requires >60% confidence for trade signals
- Generates BUY on positive momentum, SELL on negative

### Risk Management Rules

1. **Position Limits:** Maximum 2 concurrent trades
2. **Stop Loss:** 1% hard stop on all positions
3. **Time Exit:** Mandatory close at 14:30 (market hours)
4. **Daily Loss Limit:** ₹150 maximum daily loss

### Web Dashboard Architecture

**Technology:** FastAPI backend + vanilla HTML/CSS/JS frontend

**Endpoints:**
- `GET /` - Serves the dashboard HTML
- `GET /status` - System status and daily PnL
- `GET /trades/active` - Current open positions
- `GET /trades/closed` - Historical trade logs

**Design Decision:** No React/Vue framework - keeps deployment simple and avoids build steps.

## External Dependencies

### Python Packages

| Package | Purpose |
|---------|---------|
| `fastapi` | Web API framework for dashboard |
| `uvicorn` | ASGI server to run FastAPI |
| `pandas` | Data manipulation (signal engine) |

### Data Storage

| Storage | Purpose |
|---------|---------|
| `bot_state.json` | Real-time system state (file-based) |
| `trading_bot_audit.db` | SQLite database for event logs |
| `system_fallback.log` | Fallback text logs for failures |

### External Services

**None required.** The system is fully self-contained:
- Market data is simulated internally
- No broker API connections
- No authentication tokens needed
- No external data feeds

### Port Configuration

- **Dashboard API:** Port 5000 (FastAPI/Uvicorn)

### Running the System

Two processes need to run:
1. `python main.py` - Starts the trading loop
2. `python -m the.dashboard_api` - Starts the web dashboard

The dashboard should be accessible at `http://0.0.0.0:5000`
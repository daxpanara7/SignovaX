"""
SignovaX Pro - Risk Management System
Critical component for capital preservation
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass


@dataclass
class RiskParameters:
    """Risk management parameters"""
    max_risk_per_trade: float = 0.02  # 2%
    max_daily_loss: float = 0.06  # 6%
    max_weekly_loss: float = 0.12  # 12%
    max_monthly_loss: float = 0.20  # 20%
    max_open_trades: int = 3
    max_correlation: float = 0.7
    min_confidence: float = 80.0
    min_risk_reward: float = 2.0
    max_position_size: float = 0.2  # 20% of portfolio


class RiskManager:
    """
    Professional risk management system.
    Protects capital and enforces trading discipline.
    """

    def __init__(self, portfolio_value: float, params: Optional[RiskParameters] = None):
        self.portfolio_value = portfolio_value
        self.params = params or RiskParameters()

        # Daily tracking
        self.daily_pnl = 0.0
        self.daily_trades = 0
        self.daily_losses = 0

        # Weekly/Monthly tracking
        self.weekly_pnl = 0.0
        self.monthly_pnl = 0.0

        # Open positions
        self.open_positions: List[Dict] = []

        # Risk events
        self.risk_events: List[Dict] = []

    def can_open_trade(self) -> tuple[bool, str]:
        """
        Check if we can open a new trade.
        Returns (can_trade: bool, reason: str)
        """

        # 1. Check daily loss limit
        if self.daily_pnl <= -self.portfolio_value * self.params.max_daily_loss:
            self._log_risk_event("DAILY_LOSS_LIMIT", "Daily loss limit reached")
            return False, f"Daily loss limit reached ({self.params.max_daily_loss*100}%)"

        # 2. Check weekly loss limit
        if self.weekly_pnl <= -self.portfolio_value * self.params.max_weekly_loss:
            self._log_risk_event("WEEKLY_LOSS_LIMIT", "Weekly loss limit reached")
            return False, f"Weekly loss limit reached ({self.params.max_weekly_loss*100}%)"

        # 3. Check monthly loss limit
        if self.monthly_pnl <= -self.portfolio_value * self.params.max_monthly_loss:
            self._log_risk_event("MONTHLY_LOSS_LIMIT", "Monthly loss limit reached")
            return False, f"Monthly loss limit reached ({self.params.max_monthly_loss*100}%)"

        # 4. Check max open trades
        if len(self.open_positions) >= self.params.max_open_trades:
            return False, f"Maximum {self.params.max_open_trades} open trades allowed"

        # 5. Check consecutive losses (circuit breaker)
        if self.daily_losses >= 3:
            self._log_risk_event("CIRCUIT_BREAKER", "3 consecutive losses")
            return False, "Circuit breaker: 3 consecutive losses. Take a break."

        return True, "OK"

    def validate_signal(self, signal: Dict) -> tuple[bool, str]:
        """
        Validate if signal meets risk criteria.
        Returns (is_valid: bool, reason: str)
        """

        # 1. Check confidence level
        if signal.get('confidence', 0) < self.params.min_confidence:
            return False, f"Confidence {signal['confidence']}% below minimum {self.params.min_confidence}%"

        # 2. Check risk-reward ratio
        if signal.get('risk_reward', 0) < self.params.min_risk_reward:
            return False, f"R:R {signal['risk_reward']} below minimum {self.params.min_risk_reward}"

        # 3. Check for entry/SL/TP
        required_fields = ['entry', 'stop_loss', 'take_profit']
        for field in required_fields:
            if field not in signal or signal[field] is None:
                return False, f"Missing required field: {field}"

        # 4. Validate SL and TP are on correct sides
        if signal['signal'] == 'BUY':
            if signal['stop_loss'] >= signal['entry']:
                return False, "Stop loss must be below entry for BUY"
            if signal['take_profit'] <= signal['entry']:
                return False, "Take profit must be above entry for BUY"
        elif signal['signal'] == 'SELL':
            if signal['stop_loss'] <= signal['entry']:
                return False, "Stop loss must be above entry for SELL"
            if signal['take_profit'] >= signal['entry']:
                return False, "Take profit must be below entry for SELL"

        return True, "Signal validated"

    def calculate_position_size(
        self,
        entry: float,
        stop_loss: float,
        custom_risk_pct: Optional[float] = None
    ) -> float:
        """
        Calculate optimal position size based on risk.

        Formula:
        Position Size = (Portfolio Value × Risk %) / (Entry - Stop Loss)
        """

        risk_pct = custom_risk_pct or self.params.max_risk_per_trade
        risk_amount = self.portfolio_value * risk_pct
        price_risk = abs(entry - stop_loss)

        if price_risk == 0:
            return 0.0

        position_size = risk_amount / price_risk

        # Cap position size at max % of portfolio
        max_position_value = self.portfolio_value * self.params.max_position_size
        max_quantity = max_position_value / entry

        position_size = min(position_size, max_quantity)

        return round(position_size, 8)

    def check_correlation(self, symbol: str) -> tuple[bool, float]:
        """
        Check if adding this symbol exceeds correlation limits.
        Prevents over-exposure to correlated assets.
        """

        # Correlation groups (simplified)
        CORRELATION_GROUPS = {
            'crypto_major': ['BTCUSDT', 'ETHUSDT'],
            'crypto_alt': ['SOLUSDT', 'BNBUSDT', 'XRPUSDT'],
            'index_india': ['NIFTY50', 'SENSEX'],
        }

        # Find which group this symbol belongs to
        symbol_group = None
        for group, symbols in CORRELATION_GROUPS.items():
            if symbol in symbols:
                symbol_group = group
                break

        if not symbol_group:
            return True, 0.0  # Unknown symbol, allow

        # Count how many positions we have in same group
        same_group_count = 0
        for pos in self.open_positions:
            pos_symbol = pos.get('symbol')
            if pos_symbol in CORRELATION_GROUPS.get(symbol_group, []):
                same_group_count += 1

        # If we already have 2 positions in same group, reject
        if same_group_count >= 2:
            return False, 1.0

        correlation = same_group_count / self.params.max_open_trades
        return correlation < self.params.max_correlation, correlation

    def add_position(self, position: Dict):
        """Add a new open position"""
        self.open_positions.append(position)
        self.daily_trades += 1

    def remove_position(self, position_id: str):
        """Remove a closed position"""
        self.open_positions = [
            pos for pos in self.open_positions
            if pos.get('id') != position_id
        ]

    def record_trade_result(self, pnl: float):
        """Record trade result for risk tracking"""
        self.daily_pnl += pnl
        self.weekly_pnl += pnl
        self.monthly_pnl += pnl

        if pnl < 0:
            self.daily_losses += 1
        else:
            self.daily_losses = 0  # Reset streak on win

    def reset_daily(self):
        """Reset daily counters (call at EOD)"""
        self.daily_pnl = 0.0
        self.daily_trades = 0
        self.daily_losses = 0

    def reset_weekly(self):
        """Reset weekly counters"""
        self.weekly_pnl = 0.0

    def reset_monthly(self):
        """Reset monthly counters"""
        self.monthly_pnl = 0.0

    def get_risk_status(self) -> Dict:
        """Get current risk status"""
        daily_loss_pct = (self.daily_pnl / self.portfolio_value) * 100
        weekly_loss_pct = (self.weekly_pnl / self.portfolio_value) * 100
        monthly_loss_pct = (self.monthly_pnl / self.portfolio_value) * 100

        # Risk score (0-100, higher = safer)
        risk_score = 100
        risk_score -= abs(daily_loss_pct) * 5  # Penalize daily losses
        risk_score -= (self.daily_losses * 10)  # Penalize consecutive losses
        risk_score -= (len(self.open_positions) / self.params.max_open_trades) * 20  # Penalize high exposure
        risk_score = max(0, min(100, risk_score))

        return {
            "can_trade": self.can_open_trade()[0],
            "risk_score": round(risk_score, 2),
            "daily_pnl": self.daily_pnl,
            "daily_loss_pct": round(daily_loss_pct, 2),
            "daily_loss_limit_pct": self.params.max_daily_loss * 100,
            "weekly_pnl": self.weekly_pnl,
            "weekly_loss_pct": round(weekly_loss_pct, 2),
            "monthly_pnl": self.monthly_pnl,
            "monthly_loss_pct": round(monthly_loss_pct, 2),
            "open_positions": len(self.open_positions),
            "max_positions": self.params.max_open_trades,
            "daily_trades": self.daily_trades,
            "consecutive_losses": self.daily_losses,
            "risk_events": self.risk_events[-10:]  # Last 10 events
        }

    def _log_risk_event(self, event_type: str, description: str):
        """Log a risk management event"""
        self.risk_events.append({
            "type": event_type,
            "description": description,
            "timestamp": datetime.now().isoformat(),
            "daily_pnl": self.daily_pnl,
            "portfolio_value": self.portfolio_value
        })


# Example usage
if __name__ == "__main__":
    risk_mgr = RiskManager(portfolio_value=10000)

    # Check if we can trade
    can_trade, reason = risk_mgr.can_open_trade()
    print(f"Can trade: {can_trade} - {reason}")

    # Validate a signal
    signal = {
        'signal': 'BUY',
        'confidence': 85,
        'risk_reward': 2.5,
        'entry': 43250,
        'stop_loss': 42800,
        'take_profit': 44375
    }

    is_valid, reason = risk_mgr.validate_signal(signal)
    print(f"Signal valid: {is_valid} - {reason}")

    # Calculate position size
    position_size = risk_mgr.calculate_position_size(
        entry=43250,
        stop_loss=42800
    )
    print(f"Position size: {position_size:.6f}")

    # Get risk status
    status = risk_mgr.get_risk_status()
    print(f"\nRisk Status:")
    print(f"  Risk Score: {status['risk_score']}/100")
    print(f"  Daily P&L: ${status['daily_pnl']:.2f}")
    print(f"  Open Positions: {status['open_positions']}/{status['max_positions']}")

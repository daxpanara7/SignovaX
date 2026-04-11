"""
SignovaX Pro - Paper Trading Engine
Simulates real trading with virtual capital
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import json


@dataclass
class Trade:
    """Individual trade record"""
    id: str
    portfolio_id: str
    symbol: str
    side: str  # BUY or SELL
    entry_price: float
    quantity: float
    stop_loss: float
    take_profit: float
    current_price: float
    pnl: float
    pnl_percent: float
    confidence: float
    reasoning: List[str]
    status: str  # OPEN, CLOSED, STOPPED
    opened_at: datetime
    closed_at: Optional[datetime] = None
    exit_reason: Optional[str] = None
    exit_price: Optional[float] = None

    # Trade management
    initial_stop_loss: Optional[float] = None
    highest_price: Optional[float] = None  # For trailing stop
    lowest_price: Optional[float] = None


@dataclass
class Portfolio:
    """Paper trading portfolio"""
    id: str
    name: str
    initial_balance: float
    current_balance: float
    total_pnl: float
    realized_pnl: float
    unrealized_pnl: float
    trades_count: int
    wins: int
    losses: int
    win_rate: float
    profit_factor: float
    max_drawdown: float
    created_at: datetime
    updated_at: datetime

    # Risk metrics
    daily_pnl: float = 0.0
    max_daily_loss: float = 0.0
    open_trades_count: int = 0


class PaperTradingEngine:
    """
    Paper trading engine with full portfolio management,
    risk controls, and performance tracking.
    """

    def __init__(self, initial_balance: float = 10000):
        self.portfolio = self._create_portfolio(initial_balance)
        self.trades: Dict[str, Trade] = {}
        self.closed_trades: List[Trade] = []

        # Risk parameters
        self.MAX_RISK_PER_TRADE = 0.02  # 2%
        self.MAX_DAILY_LOSS = 0.06  # 6%
        self.MAX_OPEN_TRADES = 3

    def _create_portfolio(self, initial_balance: float) -> Portfolio:
        """Create new paper trading portfolio"""
        return Portfolio(
            id=str(uuid.uuid4()),
            name="Paper Trading Portfolio",
            initial_balance=initial_balance,
            current_balance=initial_balance,
            total_pnl=0.0,
            realized_pnl=0.0,
            unrealized_pnl=0.0,
            trades_count=0,
            wins=0,
            losses=0,
            win_rate=0.0,
            profit_factor=0.0,
            max_drawdown=0.0,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

    def can_open_trade(self) -> tuple[bool, str]:
        """Check if we can open a new trade"""
        # Check daily loss limit
        if self.portfolio.daily_pnl <= -self.portfolio.initial_balance * self.MAX_DAILY_LOSS:
            return False, "Daily loss limit reached"

        # Check max open trades
        if self.portfolio.open_trades_count >= self.MAX_OPEN_TRADES:
            return False, "Maximum open trades reached"

        # Check if we have enough balance
        if self.portfolio.current_balance <= 0:
            return False, "Insufficient balance"

        return True, "OK"

    def calculate_position_size(
        self,
        entry_price: float,
        stop_loss: float
    ) -> float:
        """
        Calculate position size based on risk management rules.
        Risk per trade = 2% of portfolio.
        """
        risk_amount = self.portfolio.current_balance * self.MAX_RISK_PER_TRADE
        price_risk = abs(entry_price - stop_loss)

        if price_risk == 0:
            return 0

        position_size = risk_amount / price_risk

        # Maximum position size is 20% of portfolio
        max_position_value = self.portfolio.current_balance * 0.2
        max_quantity = max_position_value / entry_price

        return min(position_size, max_quantity)

    def open_trade(
        self,
        symbol: str,
        side: str,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        confidence: float,
        reasoning: List[str]
    ) -> tuple[Optional[str], str]:
        """
        Open a new paper trade.

        Returns:
            (trade_id, message)
        """
        # Check if we can trade
        can_trade, message = self.can_open_trade()
        if not can_trade:
            return None, f"Trade rejected: {message}"

        # Calculate position size
        quantity = self.calculate_position_size(entry_price, stop_loss)

        if quantity == 0:
            return None, "Trade rejected: Insufficient risk/reward"

        # Create trade
        trade_id = str(uuid.uuid4())

        trade = Trade(
            id=trade_id,
            portfolio_id=self.portfolio.id,
            symbol=symbol,
            side=side,
            entry_price=entry_price,
            quantity=quantity,
            stop_loss=stop_loss,
            take_profit=take_profit,
            current_price=entry_price,
            pnl=0.0,
            pnl_percent=0.0,
            confidence=confidence,
            reasoning=reasoning,
            status="OPEN",
            opened_at=datetime.now(),
            initial_stop_loss=stop_loss,
            highest_price=entry_price if side == "BUY" else None,
            lowest_price=entry_price if side == "SELL" else None
        )

        # Add to active trades
        self.trades[trade_id] = trade

        # Update portfolio
        self.portfolio.open_trades_count += 1
        self.portfolio.trades_count += 1
        self.portfolio.updated_at = datetime.now()

        return trade_id, f"Trade opened: {side} {quantity:.4f} {symbol} @ ${entry_price}"

    def update_trade_price(self, trade_id: str, current_price: float):
        """Update trade with current market price"""
        if trade_id not in self.trades:
            return

        trade = self.trades[trade_id]
        trade.current_price = current_price

        # Update highest/lowest for trailing stop
        if trade.side == "BUY":
            if trade.highest_price is None or current_price > trade.highest_price:
                trade.highest_price = current_price
        else:  # SELL
            if trade.lowest_price is None or current_price < trade.lowest_price:
                trade.lowest_price = current_price

        # Calculate unrealized P&L
        if trade.side == "BUY":
            trade.pnl = (current_price - trade.entry_price) * trade.quantity
        else:  # SELL
            trade.pnl = (trade.entry_price - current_price) * trade.quantity

        trade.pnl_percent = (trade.pnl / (trade.entry_price * trade.quantity)) * 100

    def check_and_close_trades(self, prices: Dict[str, float]):
        """
        Check all open trades for stop loss or take profit hits.
        Auto-close if hit.
        """
        for trade_id in list(self.trades.keys()):
            trade = self.trades[trade_id]

            if trade.symbol not in prices:
                continue

            current_price = prices[trade.symbol]
            self.update_trade_price(trade_id, current_price)

            # Check stop loss
            if self._hit_stop_loss(trade, current_price):
                self.close_trade(trade_id, current_price, "STOP_LOSS")

            # Check take profit
            elif self._hit_take_profit(trade, current_price):
                self.close_trade(trade_id, current_price, "TAKE_PROFIT")

            # Trailing stop logic
            elif self._should_trail_stop(trade, current_price):
                self._update_trailing_stop(trade, current_price)

    def _hit_stop_loss(self, trade: Trade, current_price: float) -> bool:
        """Check if stop loss is hit"""
        if trade.side == "BUY":
            return current_price <= trade.stop_loss
        else:  # SELL
            return current_price >= trade.stop_loss

    def _hit_take_profit(self, trade: Trade, current_price: float) -> bool:
        """Check if take profit is hit"""
        if trade.side == "BUY":
            return current_price >= trade.take_profit
        else:  # SELL
            return current_price <= trade.take_profit

    def _should_trail_stop(self, trade: Trade, current_price: float) -> bool:
        """Check if we should update trailing stop"""
        if trade.side == "BUY" and trade.highest_price:
            # If price moved up 2%, trail stop to breakeven
            profit_percent = ((current_price - trade.entry_price) / trade.entry_price) * 100
            return profit_percent >= 2.0 and trade.stop_loss < trade.entry_price
        elif trade.side == "SELL" and trade.lowest_price:
            profit_percent = ((trade.entry_price - current_price) / trade.entry_price) * 100
            return profit_percent >= 2.0 and trade.stop_loss > trade.entry_price
        return False

    def _update_trailing_stop(self, trade: Trade, current_price: float):
        """Update trailing stop loss"""
        if trade.side == "BUY":
            # Move stop to breakeven
            trade.stop_loss = trade.entry_price
        else:  # SELL
            trade.stop_loss = trade.entry_price

    def close_trade(
        self,
        trade_id: str,
        exit_price: float,
        reason: str
    ) -> tuple[bool, str]:
        """Close an open trade"""
        if trade_id not in self.trades:
            return False, "Trade not found"

        trade = self.trades[trade_id]

        # Calculate final P&L
        if trade.side == "BUY":
            pnl = (exit_price - trade.entry_price) * trade.quantity
        else:
            pnl = (trade.entry_price - exit_price) * trade.quantity

        pnl_percent = (pnl / (trade.entry_price * trade.quantity)) * 100

        # Update trade
        trade.status = "CLOSED"
        trade.exit_price = exit_price
        trade.exit_reason = reason
        trade.closed_at = datetime.now()
        trade.pnl = pnl
        trade.pnl_percent = pnl_percent

        # Update portfolio
        self.portfolio.current_balance += pnl
        self.portfolio.realized_pnl += pnl
        self.portfolio.total_pnl = self.portfolio.realized_pnl + self.portfolio.unrealized_pnl
        self.portfolio.daily_pnl += pnl

        # Track wins/losses
        if pnl > 0:
            self.portfolio.wins += 1
        else:
            self.portfolio.losses += 1

        # Update win rate
        total_closed = self.portfolio.wins + self.portfolio.losses
        self.portfolio.win_rate = (self.portfolio.wins / total_closed * 100) if total_closed > 0 else 0

        # Update drawdown
        current_drawdown = (self.portfolio.initial_balance - self.portfolio.current_balance) / self.portfolio.initial_balance
        self.portfolio.max_drawdown = max(self.portfolio.max_drawdown, current_drawdown)

        # Move to closed trades
        self.closed_trades.append(trade)
        del self.trades[trade_id]
        self.portfolio.open_trades_count -= 1
        self.portfolio.updated_at = datetime.now()

        return True, f"Trade closed: {reason} - P&L: ${pnl:.2f} ({pnl_percent:+.2f}%)"

    def get_portfolio_summary(self) -> Dict:
        """Get portfolio performance summary"""
        # Calculate unrealized P&L
        unrealized = sum(t.pnl for t in self.trades.values())
        self.portfolio.unrealized_pnl = unrealized
        self.portfolio.total_pnl = self.portfolio.realized_pnl + unrealized

        # Calculate profit factor
        total_wins = sum(t.pnl for t in self.closed_trades if t.pnl > 0)
        total_losses = abs(sum(t.pnl for t in self.closed_trades if t.pnl < 0))
        self.portfolio.profit_factor = (total_wins / total_losses) if total_losses > 0 else 0

        return {
            "portfolio_id": self.portfolio.id,
            "initial_balance": self.portfolio.initial_balance,
            "current_balance": self.portfolio.current_balance,
            "total_pnl": self.portfolio.total_pnl,
            "realized_pnl": self.portfolio.realized_pnl,
            "unrealized_pnl": self.portfolio.unrealized_pnl,
            "total_return_pct": (self.portfolio.total_pnl / self.portfolio.initial_balance) * 100,
            "trades_count": self.portfolio.trades_count,
            "open_trades": self.portfolio.open_trades_count,
            "closed_trades": len(self.closed_trades),
            "wins": self.portfolio.wins,
            "losses": self.portfolio.losses,
            "win_rate": self.portfolio.win_rate,
            "profit_factor": self.portfolio.profit_factor,
            "max_drawdown": self.portfolio.max_drawdown * 100,
            "daily_pnl": self.portfolio.daily_pnl,
            "avg_win": total_wins / self.portfolio.wins if self.portfolio.wins > 0 else 0,
            "avg_loss": total_losses / self.portfolio.losses if self.portfolio.losses > 0 else 0,
        }

    def get_open_trades(self) -> List[Dict]:
        """Get all open trades"""
        return [asdict(trade) for trade in self.trades.values()]

    def get_closed_trades(self, limit: int = 50) -> List[Dict]:
        """Get recent closed trades"""
        return [asdict(trade) for trade in self.closed_trades[-limit:]]

    def reset_portfolio(self, initial_balance: float = 10000):
        """Reset portfolio to start fresh"""
        self.portfolio = self._create_portfolio(initial_balance)
        self.trades = {}
        self.closed_trades = []


# Example usage
if __name__ == "__main__":
    engine = PaperTradingEngine(initial_balance=10000)

    # Open a trade
    trade_id, msg = engine.open_trade(
        symbol="BTCUSDT",
        side="BUY",
        entry_price=43250.00,
        stop_loss=42800.00,
        take_profit=44150.00,
        confidence=85.5,
        reasoning=["Strong bullish trend", "RSI in buy zone", "Break of structure confirmed"]
    )

    print(f"\n{msg}")
    print(f"Trade ID: {trade_id}\n")

    # Simulate price movement
    engine.check_and_close_trades({"BTCUSDT": 44200.00})  # Hit TP

    # Get portfolio summary
    summary = engine.get_portfolio_summary()
    print("\nPortfolio Summary:")
    print(f"  Balance: ${summary['current_balance']:.2f}")
    print(f"  Total P&L: ${summary['total_pnl']:.2f} ({summary['total_return_pct']:+.2f}%)")
    print(f"  Win Rate: {summary['win_rate']:.1f}%")
    print(f"  Profit Factor: {summary['profit_factor']:.2f}")
    print(f"  Max Drawdown: {summary['max_drawdown']:.2f}%\n")

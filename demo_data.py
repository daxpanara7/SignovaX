#!/usr/bin/env python3
"""
Demo Data Generator for SMC Trading System
Generates realistic market data with embedded SMC patterns for testing
"""

import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
import random

def generate_realistic_ohlcv(
    symbol: str = "BTCUSDT",
    days: int = 90,
    timeframe: str = "1h",
    base_price: float = 50000
):
    """Generate realistic OHLCV data with embedded SMC patterns"""
    
    # Calculate number of candles based on timeframe
    timeframe_minutes = {
        '1m': 1, '5m': 5, '15m': 15, '30m': 30,
        '1h': 60, '4h': 240, '1d': 1440
    }
    
    minutes_per_candle = timeframe_minutes.get(timeframe, 60)
    total_candles = (days * 24 * 60) // minutes_per_candle
    
    # Initialize data
    data = []
    current_price = base_price
    current_time = datetime.now() - timedelta(days=days)
    
    # Market phases for realistic movement
    phases = [
        {'type': 'accumulation', 'duration': 0.3, 'volatility': 0.01, 'trend': 0},
        {'type': 'markup', 'duration': 0.2, 'volatility': 0.02, 'trend': 0.001},
        {'type': 'distribution', 'duration': 0.2, 'volatility': 0.015, 'trend': 0},
        {'type': 'markdown', 'duration': 0.15, 'volatility': 0.025, 'trend': -0.0015},
        {'type': 'recovery', 'duration': 0.15, 'volatility': 0.02, 'trend': 0.0008}
    ]
    
    # Generate candles
    phase_index = 0
    phase_progress = 0
    current_phase = phases[phase_index]
    
    for i in range(total_candles):
        # Update market phase
        phase_duration = int(total_candles * current_phase['duration'])
        if phase_progress >= phase_duration:
            phase_index = (phase_index + 1) % len(phases)
            current_phase = phases[phase_index]
            phase_progress = 0
        
        # Generate price movement based on current phase
        volatility = current_phase['volatility']
        trend = current_phase['trend']
        
        # Add some randomness and mean reversion
        price_change = np.random.normal(trend, volatility)
        
        # Add occasional spikes (liquidity grabs)
        if random.random() < 0.05:  # 5% chance of spike
            spike_direction = random.choice([-1, 1])
            price_change += spike_direction * volatility * 3
        
        # Calculate OHLC
        open_price = current_price
        close_price = open_price * (1 + price_change)
        
        # Generate realistic wicks
        high_wick = random.uniform(0, volatility * 2)
        low_wick = random.uniform(0, volatility * 2)
        
        high_price = max(open_price, close_price) * (1 + high_wick)
        low_price = min(open_price, close_price) * (1 - low_wick)
        
        # Generate volume (higher during volatile periods)
        base_volume = 1000
        volume_multiplier = 1 + abs(price_change) * 50
        volume = base_volume * volume_multiplier * random.uniform(0.5, 2.0)
        
        # Create candle
        candle = {
            'timestamp': current_time + timedelta(minutes=i * minutes_per_candle),
            'open': round(open_price, 2),
            'high': round(high_price, 2),
            'low': round(low_price, 2),
            'close': round(close_price, 2),
            'volume': round(volume, 2)
        }
        
        data.append(candle)
        current_price = close_price
        phase_progress += 1
    
    return data

def embed_smc_patterns(data):
    """Embed specific SMC patterns in the data for testing"""
    df = pd.DataFrame(data)
    
    # Add some clear liquidity zones (equal highs/lows)
    for i in range(50, len(df) - 50, 100):
        if i + 20 < len(df):
            # Create equal highs (resistance)
            target_high = df.iloc[i]['high']
            for j in range(i, min(i + 20, len(df))):
                if random.random() < 0.3:  # 30% chance to touch the level
                    df.iloc[j, df.columns.get_loc('high')] = target_high + random.uniform(-0.5, 0.5)
    
    # Add clear order blocks
    for i in range(100, len(df) - 100, 150):
        if i + 10 < len(df):
            # Create a strong move after a consolidation
            consolidation_range = 20
            breakout_strength = 0.03  # 3% move
            
            # Consolidation phase
            base_price = df.iloc[i]['close']
            for j in range(i, min(i + consolidation_range, len(df))):
                df.iloc[j, df.columns.get_loc('close')] = base_price * (1 + random.uniform(-0.005, 0.005))
            
            # Strong breakout
            if i + consolidation_range < len(df):
                breakout_price = base_price * (1 + breakout_strength)
                df.iloc[i + consolidation_range, df.columns.get_loc('close')] = breakout_price
                df.iloc[i + consolidation_range, df.columns.get_loc('high')] = breakout_price * 1.01
    
    return df.to_dict('records')

def save_demo_data():
    """Generate and save demo data for different symbols and timeframes"""
    symbols_config = {
        'BTCUSDT': {'base_price': 50000, 'days': 90},
        'ETHUSDT': {'base_price': 3000, 'days': 90},
        'ADAUSDT': {'base_price': 0.5, 'days': 90},
        'EURUSD': {'base_price': 1.1, 'days': 90}
    }
    
    timeframes = ['1h', '4h', '1d']
    
    demo_data = {}
    
    for symbol, config in symbols_config.items():
        demo_data[symbol] = {}
        
        for timeframe in timeframes:
            print(f"Generating data for {symbol} - {timeframe}")
            
            # Generate base data
            raw_data = generate_realistic_ohlcv(
                symbol=symbol,
                days=config['days'],
                timeframe=timeframe,
                base_price=config['base_price']
            )
            
            # Embed SMC patterns
            enhanced_data = embed_smc_patterns(raw_data)
            
            demo_data[symbol][timeframe] = enhanced_data
    
    # Save to JSON file
    with open('backend/demo_data.json', 'w') as f:
        json.dump(demo_data, f, indent=2, default=str)
    
    print("Demo data saved to backend/demo_data.json")
    
    # Generate summary
    print("\nDemo Data Summary:")
    for symbol in demo_data:
        print(f"\n{symbol}:")
        for timeframe in demo_data[symbol]:
            candle_count = len(demo_data[symbol][timeframe])
            first_candle = demo_data[symbol][timeframe][0]
            last_candle = demo_data[symbol][timeframe][-1]
            
            print(f"  {timeframe}: {candle_count} candles")
            print(f"    From: {first_candle['timestamp']}")
            print(f"    To: {last_candle['timestamp']}")
            print(f"    Price range: {first_candle['close']} - {last_candle['close']}")

if __name__ == "__main__":
    print("🎯 Generating SMC Trading System Demo Data...")
    save_demo_data()
    print("✅ Demo data generation complete!")
    print("\nTo use this data:")
    print("1. Start the backend server")
    print("2. The system will automatically use demo data when Binance API is not configured")
    print("3. Navigate to the frontend to see the patterns in action")
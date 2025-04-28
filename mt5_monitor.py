import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime
import time
import os

def get_symbol_price(symbol):
    """
    Get current price for a symbol
    
    Args:
        symbol (str): Symbol name (e.g., "EURUSD")
    
    Returns:
        dict: Bid, ask, spread information
    """
    symbol_info_tick = mt5.symbol_info_tick(symbol)
    if symbol_info_tick is None:
        print(f"Failed to get tick data for {symbol}")
        return None
    
    return {
        "symbol": symbol,
        "bid": symbol_info_tick.bid,
        "ask": symbol_info_tick.ask,
        "spread": round((symbol_info_tick.ask - symbol_info_tick.bid) * 10000, 1),
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    }

def get_price_history(symbol, timeframe=mt5.TIMEFRAME_M5, bars=100, from_date=None):
    """
    Get historical price data for a symbol
    
    Args:
        symbol (str): Symbol name (e.g., "EURUSD")
        timeframe (int): MT5 timeframe constant (default: mt5.TIMEFRAME_M5)
        bars (int): Number of bars to retrieve (default: 100)
        from_date (datetime, optional): Start date for data retrieval. If None, uses bars parameter
    
    Returns:
        pandas.DataFrame: Historical price data
    """
    print(f"Trying to get price history for {symbol} on timeframe {timeframe}")
    
    # Check if MT5 is connected
    if not mt5.terminal_info():
        print("No connection to MetaTrader 5")
        return None
    
    # Check if symbol exists
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        print(f"Symbol {symbol} not found in MT5 terminal")
        
        # Print available symbols for debugging
        symbols = mt5.symbols_get()
        print(f"Available symbols: {', '.join([s.name for s in symbols[:10]])}...")
        return None
    
    # Enable symbol if needed
    if not symbol_info.visible:
        print(f"Symbol {symbol} is not visible, enabling...")
        if not mt5.symbol_select(symbol, True):
            print(f"Failed to enable symbol {symbol}")
            return None
    
    # Get historical data
    if from_date:
        # Convert datetime to timestamp
        from_timestamp = int(from_date.timestamp())
        rates = mt5.copy_rates_from(symbol, timeframe, from_timestamp, 0)
    else:
        rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, bars)
    
    if rates is None:
        print(f"Failed to get historical data for {symbol}, error code: {mt5.last_error()}")
        return None
    
    if len(rates) == 0:
        print(f"No historical data received for {symbol}")
        return None
    
    print(f"Retrieved {len(rates)} bars for {symbol}")
    
    # Convert to DataFrame
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    
    # Add volume column if it doesn't exist
    if 'volume' not in df.columns:
        print(f"Volume column not found, adding default volume of 1")
        df['volume'] = 1
    
    return df

def calculate_indicators(df):
    """
    Calculate technical indicators on price data
    
    Args:
        df (pandas.DataFrame): Price history dataframe
        
    Returns:
        pandas.DataFrame: Dataframe with added indicators
    """
    # Make a copy to avoid modifying the original
    result = df.copy()
    
    # Add SMA indicators
    result['sma_5'] = result['close'].rolling(window=5).mean()
    result['sma_20'] = result['close'].rolling(window=20).mean()
    result['sma_50'] = result['close'].rolling(window=50).mean()
    result['sma_200'] = result['close'].rolling(window=200).mean()
    
    # Add EMA indicators
    result['ema_9'] = result['close'].ewm(span=9, adjust=False).mean()
    result['ema_12'] = result['close'].ewm(span=12, adjust=False).mean()
    result['ema_26'] = result['close'].ewm(span=26, adjust=False).mean()
    result['ema_50'] = result['close'].ewm(span=50, adjust=False).mean()
    result['ema_200'] = result['close'].ewm(span=200, adjust=False).mean()
    
    # Add RSI (14)
    delta = result['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(window=14).mean()
    loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
    
    rs = gain / loss
    result['rsi_14'] = 100 - (100 / (1 + rs))
    
    # Add stochastic oscillator
    period = 14
    result['lowest_low'] = result['low'].rolling(window=period).min()
    result['highest_high'] = result['high'].rolling(window=period).max()
    result['stoch_k'] = 100 * ((result['close'] - result['lowest_low']) / 
                               (result['highest_high'] - result['lowest_low']))
    result['stoch_d'] = result['stoch_k'].rolling(window=3).mean()
    
    # Add Bollinger Bands (20, 2)
    result['bb_middle'] = result['close'].rolling(window=20).mean()
    std_dev = result['close'].rolling(window=20).std()
    result['bb_upper'] = result['bb_middle'] + (std_dev * 2)
    result['bb_lower'] = result['bb_middle'] - (std_dev * 2)
    result['bb_width'] = (result['bb_upper'] - result['bb_lower']) / result['bb_middle']
    
    # Add MACD
    result['macd'] = result['ema_12'] - result['ema_26']
    result['signal'] = result['macd'].ewm(span=9, adjust=False).mean()
    result['histogram'] = result['macd'] - result['signal']
    
    # Add ATR (Average True Range)
    tr1 = abs(result['high'] - result['low'])
    tr2 = abs(result['high'] - result['close'].shift())
    tr3 = abs(result['low'] - result['close'].shift())
    result['tr'] = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    result['atr_14'] = result['tr'].rolling(window=14).mean()
    
    # Add ADX (Average Directional Index)
    # True Range
    result['plus_dm'] = result['high'].diff().clip(lower=0)
    result['minus_dm'] = (-result['low'].diff()).clip(lower=0)
    
    # Ensure plus_dm is greater than minus_dm
    cond = (result['plus_dm'] > result['minus_dm']) & (result['plus_dm'] > 0)
    result.loc[~cond, 'plus_dm'] = 0
    
    # Ensure minus_dm is greater than plus_dm
    cond = (result['minus_dm'] > result['plus_dm']) & (result['minus_dm'] > 0)
    result.loc[~cond, 'minus_dm'] = 0
    
    # Smooth with EMA
    result['plus_di_14'] = 100 * (result['plus_dm'].ewm(alpha=1/14, adjust=False).mean() / 
                                   result['tr'].ewm(alpha=1/14, adjust=False).mean())
    result['minus_di_14'] = 100 * (result['minus_dm'].ewm(alpha=1/14, adjust=False).mean() / 
                                    result['tr'].ewm(alpha=1/14, adjust=False).mean())
    
    # Calculate ADX
    result['dx'] = 100 * abs(result['plus_di_14'] - result['minus_di_14']) / (result['plus_di_14'] + result['minus_di_14'])
    result['adx_14'] = result['dx'].ewm(alpha=1/14, adjust=False).mean()
    
    # Add Ichimoku Cloud
    # Tenkan-sen (Conversion Line): (9-period high + 9-period low) / 2
    period9_high = result['high'].rolling(window=9).max()
    period9_low = result['low'].rolling(window=9).min()
    result['tenkan_sen'] = (period9_high + period9_low) / 2
    
    # Kijun-sen (Base Line): (26-period high + 26-period low) / 2
    period26_high = result['high'].rolling(window=26).max()
    period26_low = result['low'].rolling(window=26).min()
    result['kijun_sen'] = (period26_high + period26_low) / 2
    
    # Senkou Span A (Leading Span A): (Conversion Line + Base Line) / 2 (26 periods ahead)
    result['senkou_span_a'] = ((result['tenkan_sen'] + result['kijun_sen']) / 2).shift(26)
    
    # Senkou Span B (Leading Span B): (52-period high + 52-period low) / 2 (26 periods ahead)
    period52_high = result['high'].rolling(window=52).max()
    period52_low = result['low'].rolling(window=52).min()
    result['senkou_span_b'] = ((period52_high + period52_low) / 2).shift(26)
    
    # Chikou Span (Lagging Span): Current closing price (26 periods behind)
    result['chikou_span'] = result['close'].shift(-26)
    
    return result

def get_trade_signal(df):
    """
    Generate buy/sell signals based on technical indicators
    
    Args:
        df (pandas.DataFrame): Dataframe with indicators
        
    Returns:
        dict: Trading signal recommendation
    """
    last_row = df.iloc[-1]
    prev_row = df.iloc[-2]
    
    signal = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "price": last_row['close'],
        "signal": "HOLD",
        "strength": 0,
        "reason": []
    }
    
    # SMA crossover (5 and 20)
    if prev_row['sma_5'] <= prev_row['sma_20'] and last_row['sma_5'] > last_row['sma_20']:
        signal["signal"] = "BUY"
        signal["strength"] += 2
        signal["reason"].append("SMA 5 crossed above SMA 20")
    elif prev_row['sma_5'] >= prev_row['sma_20'] and last_row['sma_5'] < last_row['sma_20']:
        signal["signal"] = "SELL"
        signal["strength"] += 2
        signal["reason"].append("SMA 5 crossed below SMA 20")
    
    # EMA crossover (9 and 20)
    if prev_row['ema_9'] <= prev_row['sma_20'] and last_row['ema_9'] > last_row['sma_20']:
        if signal["signal"] == "SELL":
            signal["signal"] = "CONFLICTING"
        else:
            signal["signal"] = "BUY"
        signal["strength"] += 1
        signal["reason"].append("EMA 9 crossed above SMA 20")
    elif prev_row['ema_9'] >= prev_row['sma_20'] and last_row['ema_9'] < last_row['sma_20']:
        if signal["signal"] == "BUY":
            signal["signal"] = "CONFLICTING"
        else:
            signal["signal"] = "SELL"
        signal["strength"] += 1
        signal["reason"].append("EMA 9 crossed below SMA 20")
    
    # RSI signals
    if last_row['rsi_14'] < 30:
        if signal["signal"] == "SELL":
            signal["signal"] = "CONFLICTING"
        else:
            signal["signal"] = "BUY"
        signal["strength"] += 1
        signal["reason"].append(f"RSI oversold ({last_row['rsi_14']:.2f})")
    elif last_row['rsi_14'] > 70:
        if signal["signal"] == "BUY":
            signal["signal"] = "CONFLICTING"
        else:
            signal["signal"] = "SELL"
        signal["strength"] += 1
        signal["reason"].append(f"RSI overbought ({last_row['rsi_14']:.2f})")
    
    # Stochastic signals
    if last_row['stoch_k'] < 20 and last_row['stoch_k'] > last_row['stoch_d']:
        if signal["signal"] == "SELL":
            signal["signal"] = "CONFLICTING"
        else:
            signal["signal"] = "BUY"
        signal["strength"] += 1
        signal["reason"].append(f"Stochastic oversold and K>D ({last_row['stoch_k']:.2f})")
    elif last_row['stoch_k'] > 80 and last_row['stoch_k'] < last_row['stoch_d']:
        if signal["signal"] == "BUY":
            signal["signal"] = "CONFLICTING"
        else:
            signal["signal"] = "SELL"
        signal["strength"] += 1
        signal["reason"].append(f"Stochastic overbought and K<D ({last_row['stoch_k']:.2f})")
    
    # MACD signals
    if prev_row['macd'] <= prev_row['signal'] and last_row['macd'] > last_row['signal']:
        if signal["signal"] == "SELL":
            signal["signal"] = "CONFLICTING"
        else:
            signal["signal"] = "BUY"
        signal["strength"] += 2
        signal["reason"].append("MACD crossed above signal line")
    elif prev_row['macd'] >= prev_row['signal'] and last_row['macd'] < last_row['signal']:
        if signal["signal"] == "BUY":
            signal["signal"] = "CONFLICTING"
        else:
            signal["signal"] = "SELL"
        signal["strength"] += 2
        signal["reason"].append("MACD crossed below signal line")
    
    # Bollinger Bands signals
    if last_row['close'] < last_row['bb_lower']:
        if signal["signal"] == "SELL":
            signal["signal"] = "CONFLICTING"
        else:
            signal["signal"] = "BUY"
        signal["strength"] += 2
        signal["reason"].append("Price below lower Bollinger Band")
    elif last_row['close'] > last_row['bb_upper']:
        if signal["signal"] == "BUY":
            signal["signal"] = "CONFLICTING"
        else:
            signal["signal"] = "SELL"
        signal["strength"] += 2
        signal["reason"].append("Price above upper Bollinger Band")
    
    # ADX trend strength
    if last_row['adx_14'] > 25:
        # Strong trend detected, increase strength of existing signal
        if signal["signal"] in ["BUY", "SELL"]:
            signal["strength"] += 1
            signal["reason"].append(f"Strong trend detected (ADX: {last_row['adx_14']:.2f})")
        
        # Directional movement checks
        if last_row['plus_di_14'] > last_row['minus_di_14']:
            if signal["signal"] == "SELL":
                signal["signal"] = "CONFLICTING"
            else:
                signal["signal"] = "BUY"
            signal["strength"] += 1
            signal["reason"].append(f"+DI > -DI ({last_row['plus_di_14']:.2f} > {last_row['minus_di_14']:.2f})")
        elif last_row['minus_di_14'] > last_row['plus_di_14']:
            if signal["signal"] == "BUY":
                signal["signal"] = "CONFLICTING"
            else:
                signal["signal"] = "SELL"
            signal["strength"] += 1
            signal["reason"].append(f"-DI > +DI ({last_row['minus_di_14']:.2f} > {last_row['plus_di_14']:.2f})")
    
    # Ichimoku Cloud signals
    # Current price above the cloud
    if (last_row['close'] > last_row['senkou_span_a']) and (last_row['close'] > last_row['senkou_span_b']):
        if signal["signal"] == "SELL":
            signal["signal"] = "CONFLICTING"
        else:
            signal["signal"] = "BUY"
        signal["strength"] += 1
        signal["reason"].append("Price above Ichimoku Cloud")
    # Current price below the cloud
    elif (last_row['close'] < last_row['senkou_span_a']) and (last_row['close'] < last_row['senkou_span_b']):
        if signal["signal"] == "BUY":
            signal["signal"] = "CONFLICTING"
        else:
            signal["signal"] = "SELL"
        signal["strength"] += 1
        signal["reason"].append("Price below Ichimoku Cloud")
    
    # Tenkan-sen/Kijun-sen cross (similar to moving average crossover)
    if prev_row['tenkan_sen'] <= prev_row['kijun_sen'] and last_row['tenkan_sen'] > last_row['kijun_sen']:
        if signal["signal"] == "SELL":
            signal["signal"] = "CONFLICTING"
        else:
            signal["signal"] = "BUY"
        signal["strength"] += 1
        signal["reason"].append("Tenkan-sen crossed above Kijun-sen")
    elif prev_row['tenkan_sen'] >= prev_row['kijun_sen'] and last_row['tenkan_sen'] < last_row['kijun_sen']:
        if signal["signal"] == "BUY":
            signal["signal"] = "CONFLICTING"
        else:
            signal["signal"] = "SELL"
        signal["strength"] += 1
        signal["reason"].append("Tenkan-sen crossed below Kijun-sen")
    
    # Price momentum
    price_change_pct = (last_row['close'] - prev_row['close']) / prev_row['close'] * 100
    if price_change_pct > 0.2:
        if signal["signal"] == "SELL":
            signal["strength"] -= 1
        else:
            signal["strength"] += 1
        signal["reason"].append(f"Strong upward momentum ({price_change_pct:.2f}%)")
    elif price_change_pct < -0.2:
        if signal["signal"] == "BUY":
            signal["strength"] -= 1
        else:
            signal["strength"] += 1
        signal["reason"].append(f"Strong downward momentum ({price_change_pct:.2f}%)")
    
    # Final check for conflicting signals
    if signal["signal"] == "CONFLICTING":
        if signal["strength"] > 0:
            signal["signal"] = "HOLD"
            signal["reason"].append("Mixed signals - consider waiting")
    
    # Generate order parameters based on signal
    if signal["signal"] in ["BUY", "SELL"]:
        # Calculate entry, stop loss and take profit levels
        current_price = last_row['close']
        atr = last_row['atr_14']
        
        # Suggested order params - Scalping settings with tighter SL and smaller TP
        signal["order_params"] = {
            "entry_type": signal["signal"],
            "entry_price": current_price,
            "stop_loss": current_price - (atr * 0.8) if signal["signal"] == "BUY" else current_price + (atr * 0.8),
            "take_profit": current_price + (atr * 1.2) if signal["signal"] == "BUY" else current_price - (atr * 1.2),
            "risk_reward_ratio": 1.5,
            "suggested_volume": 0.01  # Default minimal lot size
        }
        
        # Add limit order options
        spread = atr * 0.5
        if signal["signal"] == "BUY":
            signal["order_params"]["buy_limit_price"] = current_price - spread
            signal["order_params"]["buy_stop_price"] = current_price + spread
        else:  # SELL
            signal["order_params"]["sell_limit_price"] = current_price + spread
            signal["order_params"]["sell_stop_price"] = current_price - spread
    
    return signal

def monitor_symbols(symbols, interval=5, max_records=1000, save_data=True, data_dir="price_data", 
                  auto_trade=False, risk_percent=1.0, order_type="MARKET", min_signal_strength=3):
    """
    Monitor symbols in real-time, record data, and provide trading suggestions
    
    Args:
        symbols (list): List of symbol names to monitor
        interval (int): Time interval between checks in seconds
        max_records (int): Maximum number of price records to keep in memory
        save_data (bool): Whether to save price data to CSV files
        data_dir (str): Directory to save data files
        auto_trade (bool): Whether to automatically place trades based on signals
        risk_percent (float): Percentage of account balance to risk per trade
        order_type (str): Type of order to place ("MARKET", "LIMIT", "STOP", "STOP_LIMIT")
        min_signal_strength (int): Minimum signal strength required for auto-trading
    """
    if not mt5.terminal_info():
        print("No connection to MetaTrader 5")
        return
    
    # Create data directory if it doesn't exist
    if save_data and not os.path.exists(data_dir):
        os.makedirs(data_dir)
    
    # Initialize price records dictionary
    price_records = {symbol: [] for symbol in symbols}
    
    # Track the last trading signal to avoid duplicate orders
    last_signals = {symbol: {"timestamp": None, "signal": None} for symbol in symbols}
    
    try:
        print(f"Starting monitoring for symbols: {', '.join(symbols)}")
        if auto_trade:
            print(f"Auto-trading enabled! Risk: {risk_percent}%, Order type: {order_type}, Min strength: {min_signal_strength}")
        print(f"Press Ctrl+C to stop monitoring\n")
        
        while True:
            for symbol in symbols:
                # Get current price
                price_data = get_symbol_price(symbol)
                if price_data:
                    # Add to records
                    price_records[symbol].append(price_data)
                    
                    # Limit the number of records kept in memory
                    if len(price_records[symbol]) > max_records:
                        price_records[symbol] = price_records[symbol][-max_records:]
                    
                    # Get price history and calculate indicators
                    history_df = get_price_history(symbol)
                    if history_df is not None:
                        indicators_df = calculate_indicators(history_df)
                        
                        # Get trading signal
                        signal = get_trade_signal(indicators_df)
                        
                        # Display current price and signal
                        print(f"\n{'-'*65}")
                        print(f"Symbol: {symbol} | Time: {price_data['time']}")
                        print(f"Bid: {price_data['bid']} | Ask: {price_data['ask']} | Spread: {price_data['spread']} points")
                        
                        # Display key indicators
                        last_row = indicators_df.iloc[-1]
                        print(f"\n--- Technical Indicators ---")
                        print(f"RSI(14): {last_row['rsi_14']:.2f} | "
                              f"Stoch K/D: {last_row['stoch_k']:.2f}/{last_row['stoch_d']:.2f} | "
                              f"ADX: {last_row['adx_14']:.2f}")
                        print(f"MACD: {last_row['macd']:.5f} | Signal: {last_row['signal']:.5f} | "
                              f"Histogram: {last_row['histogram']:.5f}")
                        print(f"SMA5/20/50: {last_row['sma_5']:.5f}/{last_row['sma_20']:.5f}/{last_row['sma_50']:.5f}")
                        print(f"BB Upper/Middle/Lower: {last_row['bb_upper']:.5f}/{last_row['bb_middle']:.5f}/{last_row['bb_lower']:.5f}")
                        
                        # Display trading suggestion
                        print(f"\n--- Trading Signal ---")
                        print(f"Suggestion: {signal['signal']} (Strength: {signal['strength']})")
                        if signal['reason']:
                            print(f"Reason: {', '.join(signal['reason'])}")
                        
                        # Display order parameters if a signal is present
                        if "order_params" in signal and signal["signal"] in ["BUY", "SELL"]:
                            params = signal["order_params"]
                            print(f"\n--- Order Parameters ---")
                            print(f"Entry Type: {params['entry_type']}")
                            print(f"Entry Price: {params['entry_price']:.5f}")
                            print(f"Stop Loss: {params['stop_loss']:.5f} ({abs(params['entry_price'] - params['stop_loss']):.1f} points)")
                            print(f"Take Profit: {params['take_profit']:.5f} ({abs(params['entry_price'] - params['take_profit']):.1f} points)")
                            print(f"Risk/Reward Ratio: {params['risk_reward_ratio']:.2f}")
                            
                            # Display limit and stop prices
                            if params["entry_type"] == "BUY":
                                print(f"Buy Limit Price: {params['buy_limit_price']:.5f}")
                                print(f"Buy Stop Price: {params['buy_stop_price']:.5f}")
                            else:  # SELL
                                print(f"Sell Limit Price: {params['sell_limit_price']:.5f}")
                                print(f"Sell Stop Price: {params['sell_stop_price']:.5f}")
                            
                            # Auto-trading logic
                            if (auto_trade and 
                                signal["signal"] in ["BUY", "SELL"] and 
                                signal["strength"] >= min_signal_strength):
                                
                                # Avoid duplicate orders within a timeframe
                                current_time = datetime.now()
                                last_signal_time = last_signals[symbol]["timestamp"]
                                last_signal_type = last_signals[symbol]["signal"]
                                
                                # Only trade if we haven't seen this signal in the last 5 minutes
                                # or if the signal has changed direction (scalping mode)
                                if (last_signal_time is None or 
                                    (current_time - last_signal_time).total_seconds() > 300 or
                                    (last_signal_type != signal["signal"])):
                                    
                                    print(f"\n--- Placing Auto Order ---")
                                    order_result = place_order_from_signal(
                                        symbol=symbol,
                                        signal=signal,
                                        risk_percent=risk_percent,
                                        order_type=order_type
                                    )
                                    
                                    if order_result:
                                        # Update the last signal
                                        last_signals[symbol]["timestamp"] = current_time
                                        last_signals[symbol]["signal"] = signal["signal"]
                                else:
                                    print(f"\nAuto-trading skipped: Similar signal already processed recently")
                        
                        # Save to CSV if enabled
                        if save_data:
                            df = pd.DataFrame(price_records[symbol])
                            filename = os.path.join(data_dir, f"{symbol}_prices.csv")
                            df.to_csv(filename, index=False)
                            
                            # Also save the indicators dataframe
                            indicators_filename = os.path.join(data_dir, f"{symbol}_indicators.csv")
                            indicators_df.to_csv(indicators_filename, index=False)
            
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\nMonitoring stopped")
        
    finally:
        print("Saved price data to", data_dir)

def place_order_from_signal(symbol, signal, risk_percent=1.0, order_type=None):
    """
    Place an order based on the trading signal
    
    Args:
        symbol (str): Symbol to trade
        signal (dict): Trading signal with recommendations
        risk_percent (float): Percentage of account balance to risk (1.0 = 1%)
        order_type (str, optional): Override the order type ("MARKET", "LIMIT", "STOP", "STOP_LIMIT")
        
    Returns:
        dict: Order result
    """
    if not signal or "order_params" not in signal:
        print("No valid signal or order parameters found")
        return None
        
    # Check if MT5 is initialized
    if not mt5.terminal_info():
        print("No connection to MetaTrader 5")
        return None
        
    # Get account info for position sizing
    account_info = mt5.account_info()
    if not account_info:
        print("Could not get account info")
        return None
    
    # Print account details for debugging
    print("\n=== Account Information ===")
    print(f"Server: {account_info.server}")
    print(f"Balance: {account_info.balance} {account_info.currency}")
    print(f"Leverage: {account_info.leverage}")
    print(f"Trade Allowed: {account_info.trade_allowed}")
    print(f"Trade Mode: {account_info.trade_mode}")
    print(f"Margin Free: {account_info.margin_free}")
        
    # Check if trading is allowed on this account
    if not account_info.trade_allowed:
        print("Trading is not allowed on this account. Check your MetaTrader 5 settings.")
        return None
        
    # Get symbol info
    symbol_info = mt5.symbol_info(symbol)
    if not symbol_info:
        print(f"Symbol {symbol} not found")
        return None
        
    # Print symbol details for debugging
    print(f"\n=== Symbol Information: {symbol} ===")
    print(f"Bid: {symbol_info.bid}, Ask: {symbol_info.ask}")
    print(f"Trade Mode: {symbol_info.trade_mode}")
    print(f"Volume Min: {symbol_info.volume_min}, Volume Step: {symbol_info.volume_step}")
    print(f"Volume Max: {symbol_info.volume_max}")
    print(f"Margin Initial: {symbol_info.margin_initial}")
    print(f"Trade Allowed: {symbol_info.trade_calc_mode}")
    
    # Check if trading is allowed for this symbol
    if symbol_info.trade_mode == 0:  # SYMBOL_TRADE_MODE_DISABLED
        print(f"Trading is disabled for {symbol}")
        return None
        
    # Enable symbol for trading if needed
    if not symbol_info.visible:
        print(f"Symbol {symbol} is not visible, enabling...")
        if not mt5.symbol_select(symbol, True):
            print(f"Failed to enable symbol {symbol}")
            return None
            
    # Get order parameters
    params = signal["order_params"]
    action = params["entry_type"]
    entry_price = params["entry_price"]
    stop_loss = params["stop_loss"]
    take_profit = params["take_profit"]
    
    # Calculate position size based on risk
    account_balance = account_info.balance
    risk_amount = account_balance * (risk_percent / 100)
    
    # Risk per pip calculation
    pip_value = symbol_info.trade_tick_value
    stop_loss_pips = abs(entry_price - stop_loss) / symbol_info.trade_tick_size
    
    # Position size calculation
    if stop_loss_pips > 0:
        position_size = risk_amount / (stop_loss_pips * pip_value)
        # Adjust to symbol's volume step
        position_size = round(position_size / symbol_info.volume_step) * symbol_info.volume_step
        # Ensure minimum volume
        position_size = max(position_size, symbol_info.volume_min)
        # Ensure maximum volume
        position_size = min(position_size, symbol_info.volume_max)
    else:
        position_size = symbol_info.volume_min
    
    print(f"\n=== Order Calculation ===")
    print(f"Risk Amount: {risk_amount} {account_info.currency}")
    print(f"Stop Loss Pips: {stop_loss_pips}")
    print(f"Calculated Position Size: {position_size}")
    
    # Determine order type
    if not order_type:
        # Default to market order
        order_type = "MARKET"
    
    # Prepare order request based on order type
    request = {
        "action": mt5.TRADE_ACTION_DEAL if order_type == "MARKET" else mt5.TRADE_ACTION_PENDING,
        "symbol": symbol,
        "volume": position_size,
        "type": None,  # To be set based on action and order type
        "price": None,  # To be set based on order type
        "sl": stop_loss,
        "tp": take_profit,
        "deviation": 10,  # Allowed slippage in points
        "magic": 12345,  # Magic number for identification
        "comment": f"Python {signal['signal']} signal ({signal['strength']})",
        "type_time": mt5.ORDER_TIME_GTC,  # Good till canceled
        "type_filling": mt5.ORDER_FILLING_IOC,  # Immediate or Cancel
    }
    
    # Set order type based on action and order type
    if action == "BUY":
        if order_type == "MARKET":
            request["type"] = mt5.ORDER_TYPE_BUY
            request["price"] = mt5.symbol_info_tick(symbol).ask
        elif order_type == "LIMIT":
            request["type"] = mt5.ORDER_TYPE_BUY_LIMIT
            request["price"] = params["buy_limit_price"]
        elif order_type == "STOP":
            request["type"] = mt5.ORDER_TYPE_BUY_STOP
            request["price"] = params["buy_stop_price"]
        elif order_type == "STOP_LIMIT":
            request["type"] = mt5.ORDER_TYPE_BUY_STOP_LIMIT
            request["price"] = params["buy_stop_price"]
            request["stoplimit"] = params["buy_limit_price"]
    elif action == "SELL":
        if order_type == "MARKET":
            request["type"] = mt5.ORDER_TYPE_SELL
            request["price"] = mt5.symbol_info_tick(symbol).bid
        elif order_type == "LIMIT":
            request["type"] = mt5.ORDER_TYPE_SELL_LIMIT
            request["price"] = params["sell_limit_price"]
        elif order_type == "STOP":
            request["type"] = mt5.ORDER_TYPE_SELL_STOP
            request["price"] = params["sell_stop_price"]
        elif order_type == "STOP_LIMIT":
            request["type"] = mt5.ORDER_TYPE_SELL_STOP_LIMIT
            request["price"] = params["sell_stop_price"]
            request["stoplimit"] = params["sell_limit_price"]
    
    # Check if the order type is valid
    if request["type"] is None:
        print(f"Invalid order type: {order_type} for action {action}")
        return None
    
    # Try different filling types if needed
    filling_types = [
        mt5.ORDER_FILLING_IOC,    # Immediate or Cancel
        mt5.ORDER_FILLING_FOK,    # Fill or Kill
        mt5.ORDER_FILLING_RETURN  # Return
    ]
    
    # Print order details
    print("\n=== Order Request ===")
    for key, value in request.items():
        print(f"{key}: {value}")
    
    # Try different filling types
    order_success = False
    result = None
    
    for filling_type in filling_types:
        if order_success:
            break
            
        request["type_filling"] = filling_type
        print(f"\nTrying with filling type: {filling_type}")
        
        # Send the order
        result = mt5.order_send(request)
        
        # Check if the order was successful
        if result is None:
            print(f"Failed to send order, error: {mt5.last_error()}")
            continue
            
        print(f"Order send result: {result}")
        print(f"Retcode: {result.retcode}")
        
        if result.retcode == mt5.TRADE_RETCODE_DONE or result.retcode == mt5.TRADE_RETCODE_PLACED:
            order_success = True
            print(f"Order placed successfully with filling type {filling_type}")
        else:
            print(f"Order failed with retcode {result.retcode}: {mt5.last_error()}")
            
            # Check for specific errors and provide more details
            if result.retcode == 10027:  # TRADE_RETCODE_INVALID_FILL
                print("Error: Invalid fill type. Try changing order_filling type.")
            elif result.retcode == 10016:  # TRADE_RETCODE_INVALID_VOLUME
                print(f"Error: Invalid volume. Min: {symbol_info.volume_min}, Step: {symbol_info.volume_step}")
            elif result.retcode == 10026:  # TRADE_RETCODE_TRADE_DISABLED
                print("Error: Trading is disabled. Check if your account allows trading.")
            elif result.retcode == 10019:  # TRADE_RETCODE_NO_MONEY
                print("Error: Not enough money to complete the request.")
    
    if not order_success:
        print("Order failed after trying all filling types")
        return None
    
    # Format the result
    order_result = {
        "order": result.order,
        "symbol": symbol,
        "volume": position_size,
        "price": result.price,
        "type": request["type"],
        "stop_loss": stop_loss,
        "take_profit": take_profit,
        "risk_percent": risk_percent,
        "risk_amount": risk_amount,
        "signal_strength": signal["strength"]
    }
    
    print(f"\nOrder placed successfully: {order_result}")
    return order_result

if __name__ == "__main__":
    # Example usage
    monitor_symbols(["EURUSD", "GBPUSD", "USDJPY"], interval=10) 
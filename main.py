import os
import time
import pandas as pd
import MetaTrader5 as mt5
from dotenv import load_dotenv
from datetime import datetime
import numpy as np
from colorama import init, Fore, Style

# Import our MetaTrader 5 modules
from mt5_init import initialize_mt5, shutdown_mt5
from mt5_account import get_account_info, get_positions, get_orders, get_history_deals
from mt5_order import place_market_order, place_pending_order, close_position, cancel_order
from mt5_monitor import monitor_symbols, get_price_history, calculate_indicators, get_trade_signal

# Initialize colorama
init()

def main():
    """
    Main function to demonstrate the use of MetaTrader 5 modules
    """
    # Initialize MetaTrader 5 connection
    if not initialize_mt5():
        print("Failed to initialize MetaTrader 5")
        return
    
    try:
        # Print account information
        print("\n--- Account Information ---")
        account_info = get_account_info()
        if account_info:
            print(f"Login: {account_info['login']}")
            print(f"Server: {account_info['server']}")
            print(f"Balance: {account_info['balance']} {account_info['currency']}")
            print(f"Equity: {account_info['equity']} {account_info['currency']}")
            print(f"Margin: {account_info['margin']} {account_info['currency']}")
            print(f"Free Margin: {account_info['margin_free']} {account_info['currency']}")
            print(f"Margin Level: {account_info['margin_level']}%")
        
        # Get current positions
        print("\n--- Current Positions ---")
        positions = get_positions()
        if positions is not None and not positions.empty:
            print(positions[['symbol', 'type', 'volume', 'price_open', 'price_current', 'profit']])
        else:
            print("No open positions")
        
        # Get pending orders
        print("\n--- Pending Orders ---")
        orders = get_orders()
        if orders is not None and not orders.empty:
            print(orders[['symbol', 'type', 'volume', 'price_open', 'sl', 'tp']])
        else:
            print("No pending orders")
        
        # Example of placing a market order (commented out by default)
        # Uncomment to test placing orders (adjust symbol and parameters as needed)
        """
        print("\n--- Placing Market Order ---")
        order_result = place_market_order(
            symbol="EURUSD",
            order_type=mt5.ORDER_TYPE_BUY,
            volume=0.01,
            stop_loss=0.0,  # Set appropriate SL
            take_profit=0.0,  # Set appropriate TP
            comment="Python MT5 order"
        )
        
        if order_result:
            print(f"Order placed successfully. Order ID: {order_result['order']}")
            time.sleep(2)  # Wait a bit to let the order execute
            
            # Get updated positions
            positions = get_positions()
            if positions is not None and not positions.empty:
                print("\n--- Updated Positions after order ---")
                print(positions[['symbol', 'type', 'volume', 'price_open', 'price_current', 'profit']])
                
                # Example of closing a position (commented out by default)
                # position_id = positions.iloc[0].ticket  # Get ticket of the first position
                # close_result = close_position(position_id)
                # if close_result:
                #     print(f"Position {position_id} closed successfully")
        """
        
        # Example of placing a pending order (commented out by default)
        """
        print("\n--- Placing Pending Order ---")
        # Get current price
        symbol = "EURUSD"
        symbol_info = mt5.symbol_info_tick(symbol)
        
        # For BUY_LIMIT, place below current ask price
        price = symbol_info.ask * 0.99  # 1% below current price
        
        pending_result = place_pending_order(
            symbol=symbol,
            order_type=mt5.ORDER_TYPE_BUY_LIMIT,
            volume=0.01,
            price=price,
            stop_loss=0.0,  # Set appropriate SL
            take_profit=0.0,  # Set appropriate TP
            comment="Python MT5 pending order"
        )
        
        if pending_result:
            print(f"Pending order placed successfully. Order ID: {pending_result['order']}")
            
            # Example of canceling the pending order (commented out by default)
            # time.sleep(2)
            # cancel_result = cancel_order(pending_result['order'])
            # if cancel_result:
            #     print(f"Order {pending_result['order']} canceled successfully")
        """
        
        # Get recent deals history
        print("\n--- Recent Deal History (last 7 days) ---")
        deals = get_history_deals(days=7)
        if deals is not None and not deals.empty:
            print(deals[['symbol', 'type', 'volume', 'price', 'profit', 'time']])
        else:
            print("No recent deals found")
            
        # Ask if user wants to run real-time monitoring
        choice = input("\nDo you want to run real-time symbol monitoring? (y/n): ")
        if choice.lower() == 'y':
            # Ask for symbols to monitor
            symbols_input = input("Enter symbols to monitor (comma separated, e.g., EURUSD,GBPUSD): ")
            symbols = [sym.strip() for sym in symbols_input.split(',')]
            
            # Ask for update interval
            interval_input = input("Enter update interval in seconds (default 10): ")
            interval = int(interval_input) if interval_input.strip() else 10
            
            # Run the monitoring function
            print(f"\nStarting real-time monitoring for {', '.join(symbols)}...")
            print("Press Ctrl+C to stop monitoring")
            monitor_symbols(symbols, interval=interval)
        
    except Exception as e:
        print(f"An error occurred: {e}")
    
    finally:
        # Always shut down the connection when done
        shutdown_mt5()
        print("\nMetaTrader 5 connection closed")

def analyze_market():
    """
    Run market analysis on multiple symbols and provide trading suggestions
    """
    # Initialize MetaTrader 5 connection
    if not initialize_mt5():
        print("Failed to initialize MetaTrader 5")
        return
    
    try:
        symbols = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "XAUUSD"]
        timeframes = {
            "M5": mt5.TIMEFRAME_M5,
            "M15": mt5.TIMEFRAME_M15,
            "H1": mt5.TIMEFRAME_H1,
        }
        
        print("\n=== Market Analysis ===")
        
        for symbol in symbols:
            print(f"\n--- {symbol} Analysis ---")
            
            for tf_name, tf_value in timeframes.items():
                print(f"\nTimeframe: {tf_name}")
                
                # Get price history
                df = get_price_history(symbol, timeframe=tf_value, bars=100)
                if df is None:
                    print(f"Could not get data for {symbol} on {tf_name}")
                    continue
                
                # Calculate indicators
                indicators_df = calculate_indicators(df)
                
                # Get trading signal
                signal = get_trade_signal(indicators_df)
                
                # Display current indicators
                last_row = indicators_df.iloc[-1]
                print(f"Price: {last_row['close']}")
                print(f"RSI(14): {last_row['rsi_14']:.2f}")
                print(f"MACD: {last_row['macd']:.5f}, Signal: {last_row['signal']:.5f}")
                print(f"SMA5/SMA20: {last_row['sma_5']:.5f}/{last_row['sma_20']:.5f}")
                
                # Display trading suggestion
                print(f"Suggestion: {signal['signal']} (Strength: {signal['strength']})")
                if signal['reason']:
                    print(f"Reason: {', '.join(signal['reason'])}")
                
    except Exception as e:
        print(f"An error occurred: {e}")
    
    finally:
        # Always shut down the connection when done
        shutdown_mt5()
        print("\nMetaTrader 5 connection closed")

def list_available_symbols():
    """
    List symbols available in MetaTrader 5
    """
    if not initialize_mt5():
        print(f"{Fore.RED}Failed to initialize MetaTrader 5{Style.RESET_ALL}")
        return
    
    try:
        # Get all symbols
        symbols = mt5.symbols_get()
        
        if symbols is None:
            print(f"{Fore.RED}Failed to get symbols, error code: {mt5.last_error()}{Style.RESET_ALL}")
            return
        
        # Group by first few characters to reduce output
        symbol_groups = {}
        for s in symbols:
            # Get first 3 characters as group
            prefix = s.name[:3]
            if prefix not in symbol_groups:
                symbol_groups[prefix] = []
            symbol_groups[prefix].append(s.name)
        
        # Print symbol groups
        print(f"\n{Fore.CYAN}=== Available Symbol Groups ==={Style.RESET_ALL}")
        for prefix, symbol_list in sorted(symbol_groups.items()):
            print(f"{Fore.YELLOW}{prefix}*{Style.RESET_ALL}: {Fore.GREEN}{len(symbol_list)}{Style.RESET_ALL} symbols")
        
        # Print some examples from each group
        print(f"\n{Fore.CYAN}=== Sample Symbols ==={Style.RESET_ALL}")
        for prefix, symbol_list in sorted(symbol_groups.items()):
            samples = symbol_list[:5]  # Take first 5 from each group
            print(f"{Fore.YELLOW}{prefix}*{Style.RESET_ALL}: {Fore.WHITE}{', '.join(samples)}{Style.RESET_ALL}")
            
    finally:
        shutdown_mt5()

def check_trading_allowed():
    """
    Check if trading is allowed in the MetaTrader 5 account
    
    Returns:
        tuple: (bool, str) - Whether trading is allowed and a message
    """
    if not initialize_mt5():
        return False, f"{Fore.RED}Failed to initialize MetaTrader 5{Style.RESET_ALL}"
    
    try:
        # Get account info
        account_info = mt5.account_info()
        if account_info is None:
            return False, f"{Fore.RED}Could not get account info{Style.RESET_ALL}"
        
        # Check if trading is allowed
        if not account_info.trade_allowed:
            return False, f"{Fore.RED}Trading is not allowed on this account (Server: {account_info.server}){Style.RESET_ALL}"
        
        # Print account details
        print(f"\n{Fore.CYAN}=== Account Information ==={Style.RESET_ALL}")
        print(f"Login: {Fore.YELLOW}{account_info.login}{Style.RESET_ALL}")
        print(f"Server: {Fore.YELLOW}{account_info.server}{Style.RESET_ALL}")
        print(f"Balance: {Fore.GREEN}{account_info.balance} {account_info.currency}{Style.RESET_ALL}")
        print(f"Leverage: {Fore.YELLOW}1:{account_info.leverage}{Style.RESET_ALL}")
        print(f"Trade Allowed: {Fore.GREEN if account_info.trade_allowed else Fore.RED}{account_info.trade_allowed}{Style.RESET_ALL}")
        print(f"Trade Mode: {Fore.YELLOW}{account_info.trade_mode}{Style.RESET_ALL}")
        
        # Check account type
        if account_info.trade_mode == 0:  # ACCOUNT_TRADE_MODE_DEMO
            return True, f"{Fore.GREEN}Demo account - Trading is allowed{Style.RESET_ALL}"
        elif account_info.trade_mode == 1:  # ACCOUNT_TRADE_MODE_CONTEST
            return True, f"{Fore.GREEN}Contest account - Trading is allowed{Style.RESET_ALL}"
        elif account_info.trade_mode == 2:  # ACCOUNT_TRADE_MODE_REAL
            return True, f"{Fore.GREEN}Real account - Trading is allowed{Style.RESET_ALL}"
        else:
            return False, f"{Fore.RED}Unknown account type: {account_info.trade_mode}{Style.RESET_ALL}"
        
    except Exception as e:
        return False, f"{Fore.RED}Error checking trading status: {str(e)}{Style.RESET_ALL}"
    finally:
        shutdown_mt5()

def monitor_symbols(symbols, interval=10, auto_trade=False, risk_percent=1.0, order_type="MARKET", 
                   min_signal_strength=3, scalping_mode=False, quick_close=False, quick_close_target=5.0):
    """
    Monitor multiple symbols and execute trades based on signals
    
    Args:
        symbols (list): List of symbols to monitor
        interval (int): Update interval in seconds
        auto_trade (bool): Whether to automatically execute trades
        risk_percent (float): Risk percentage per trade
        order_type (str): Type of order to place (MARKET, LIMIT, STOP, STOP_LIMIT)
        min_signal_strength (int): Minimum signal strength to consider (1-5)
        scalping_mode (bool): Whether to use scalping mode
        quick_close (bool): Whether to use quick close feature
        quick_close_target (float): Target profit in pips for quick close
    """
    print(f"\n{Fore.CYAN}=== Starting Symbol Monitoring ==={Style.RESET_ALL}")
    print(f"Symbols: {', '.join(symbols)}")
    print(f"Interval: {interval} seconds")
    print(f"Auto Trade: {'Enabled' if auto_trade else 'Disabled'}")
    if auto_trade:
        print(f"Risk per trade: {risk_percent}%")
        print(f"Order type: {order_type}")
        print(f"Min signal strength: {min_signal_strength}")
        print(f"Scalping mode: {'Enabled' if scalping_mode else 'Disabled'}")
        if scalping_mode:
            print(f"Quick close: {'Enabled' if quick_close else 'Disabled'}")
            if quick_close:
                print(f"Quick close target: {quick_close_target} pips")
    
    try:
        while True:
            for symbol in symbols:
                try:
                    # Get price history
                    df = get_price_history(symbol, timeframe=mt5.TIMEFRAME_M1 if scalping_mode else mt5.TIMEFRAME_M15)
                    if df is None or df.empty:
                        print(f"{Fore.YELLOW}No data available for {symbol}{Style.RESET_ALL}")
                        continue
                    
                    # Calculate indicators
                    indicators_df = calculate_indicators(df)
                    
                    # Get trading signal
                    signal = get_trade_signal(indicators_df)
                    
                    # Print current status
                    current_price = indicators_df['close'].iloc[-1]
                    print(f"\n{Fore.CYAN}{symbol} - {datetime.now().strftime('%H:%M:%S')}{Style.RESET_ALL}")
                    print(f"Price: {current_price}")
                    print(f"Signal: {signal['signal']} (Strength: {signal['strength']})")
                    if signal['reason']:
                        print(f"Reason: {', '.join(signal['reason'])}")
                    
                    # Check if we should trade
                    if auto_trade and signal['strength'] >= min_signal_strength:
                        # Adjust signal strength threshold for scalping
                        if scalping_mode and signal['strength'] >= 2:  # Lower threshold for scalping
                            # Place order
                            result = place_order_from_signal(
                                symbol=symbol,
                                signal=signal,
                                risk_percent=risk_percent,
                                order_type=order_type
                            )
                            
                            if result:
                                print(f"{Fore.GREEN}Order placed successfully{Style.RESET_ALL}")
                                
                                # If quick close is enabled, monitor the position
                                if quick_close and result.get('position_id'):
                                    monitor_position_for_quick_close(
                                        position_id=result['position_id'],
                                        target_pips=quick_close_target
                                    )
                            else:
                                print(f"{Fore.RED}Failed to place order{Style.RESET_ALL}")
                    
                except Exception as e:
                    print(f"{Fore.RED}Error processing {symbol}: {str(e)}{Style.RESET_ALL}")
            
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Monitoring stopped by user{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}Error in monitoring: {str(e)}{Style.RESET_ALL}")

def monitor_position_for_quick_close(position_id, target_pips):
    """
    Monitor a position and close it when target profit is reached
    
    Args:
        position_id (int): Position ticket ID
        target_pips (float): Target profit in pips
    """
    try:
        while True:
            position = mt5.positions_get(ticket=position_id)
            if not position:
                break
                
            position = position[0]
            current_profit = position.profit
            current_price = position.price_current
            open_price = position.price_open
            
            # Calculate profit in pips
            if position.type == mt5.POSITION_TYPE_BUY:
                profit_pips = (current_price - open_price) * 10000  # For 5-digit brokers
            else:
                profit_pips = (open_price - current_price) * 10000
                
            if profit_pips >= target_pips:
                print(f"{Fore.GREEN}Quick close target reached: {profit_pips:.1f} pips{Style.RESET_ALL}")
                close_position(position_id)
                break
                
            time.sleep(1)  # Check every second
            
    except Exception as e:
        print(f"{Fore.RED}Error monitoring position: {str(e)}{Style.RESET_ALL}")

if __name__ == "__main__":
    print(f"{Fore.CYAN}=== MetaTrader 5 Python Interface ==={Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Choose an option:{Style.RESET_ALL}")
    print(f"{Fore.GREEN}1.{Style.RESET_ALL} Run basic MetaTrader 5 demo")
    print(f"{Fore.GREEN}2.{Style.RESET_ALL} Run market analysis with trading suggestions")
    print(f"{Fore.GREEN}3.{Style.RESET_ALL} Run real-time symbol monitoring")
    print(f"{Fore.GREEN}4.{Style.RESET_ALL} Show interactive chart with trading options")
    print(f"{Fore.GREEN}5.{Style.RESET_ALL} List available symbols in MT5")
    
    choice = input(f"{Fore.YELLOW}Enter your choice (1-5): {Style.RESET_ALL}")
    
    if choice == "1":
        main()
    elif choice == "2":
        analyze_market()
    elif choice == "3":
        # Initialize MetaTrader 5 connection
        if not initialize_mt5():
            print(f"{Fore.RED}Failed to initialize MetaTrader 5{Style.RESET_ALL}")
        else:
            try:
                # Ask for scalping mode
                scalping_mode = input(f"{Fore.YELLOW}Use scalping mode for small, frequent profits? (y/n, default: n): {Style.RESET_ALL}")
                use_scalping = scalping_mode.lower() == 'y'
                
                # Ask for quick close if scalping is enabled
                quick_close = False
                quick_close_target = 5.0
                if use_scalping:
                    quick_close_input = input(f"{Fore.YELLOW}Enable quick close feature? (y/n, default: n): {Style.RESET_ALL}")
                    quick_close = quick_close_input.lower() == 'y'
                    if quick_close:
                        target_input = input(f"{Fore.YELLOW}Enter quick close target in pips (default 5.0): {Style.RESET_ALL}")
                        quick_close_target = float(target_input) if target_input.strip() else 5.0
                
                # Ask for symbols to monitor
                symbols_input = input(f"{Fore.YELLOW}Enter symbols to monitor (comma separated, e.g., EURUSD,GBPUSD): {Style.RESET_ALL}")
                symbols = [sym.strip() for sym in symbols_input.split(',')]
                
                # Ask for update interval
                if use_scalping:
                    interval = 5  # 5 seconds for scalping
                    print(f"{Fore.GREEN}Using fast 5-second interval for scalping mode{Style.RESET_ALL}")
                else:
                    interval_input = input(f"{Fore.YELLOW}Enter update interval in seconds (default 10): {Style.RESET_ALL}")
                    interval = int(interval_input) if interval_input.strip() else 10
                
                # Ask if auto-trading should be enabled
                auto_trade_input = input(f"{Fore.YELLOW}Enable auto-trading? (y/n, default: n): {Style.RESET_ALL}")
                auto_trade = auto_trade_input.lower() == 'y'
                
                # Default settings
                risk_percent = 0.5 if use_scalping else 1.0  # Lower risk for scalping
                order_type = "MARKET"
                min_signal_strength = 2 if use_scalping else 3  # Lower threshold for scalping
                
                if auto_trade:
                    if not use_scalping:
                        # Ask for risk percentage
                        risk_input = input(f"{Fore.YELLOW}Enter risk percentage per trade (default 1.0%): {Style.RESET_ALL}")
                        if risk_input.strip():
                            risk_percent = float(risk_input)
                    else:
                        print(f"{Fore.GREEN}Using lower 0.5% risk for scalping mode{Style.RESET_ALL}")
                    
                    # Ask for order type
                    print(f"\n{Fore.CYAN}Select order type:{Style.RESET_ALL}")
                    print(f"{Fore.GREEN}1.{Style.RESET_ALL} MARKET (Immediate execution)")
                    print(f"{Fore.GREEN}2.{Style.RESET_ALL} LIMIT (Buy lower, sell higher than current price)")
                    print(f"{Fore.GREEN}3.{Style.RESET_ALL} STOP (Buy higher, sell lower than current price)")
                    print(f"{Fore.GREEN}4.{Style.RESET_ALL} STOP_LIMIT (Combines stop and limit orders)")
                    order_type_input = input(f"{Fore.YELLOW}Enter order type (1-4, default 1): {Style.RESET_ALL}")
                    
                    order_types = {
                        "1": "MARKET",
                        "2": "LIMIT",
                        "3": "STOP",
                        "4": "STOP_LIMIT"
                    }
                    
                    order_type = order_types.get(order_type_input, "MARKET")
                    
                    if not use_scalping:
                        # Ask for minimum signal strength
                        strength_input = input(f"{Fore.YELLOW}Enter minimum signal strength for auto-trading (1-10, default 3): {Style.RESET_ALL}")
                        if strength_input.strip():
                            min_signal_strength = int(strength_input)
                    else:
                        print(f"{Fore.GREEN}Using lower signal strength threshold (2) for scalping mode{Style.RESET_ALL}")
                
                # Run the monitoring function
                monitor_symbols(
                    symbols=symbols, 
                    interval=interval,
                    auto_trade=auto_trade,
                    risk_percent=risk_percent,
                    order_type=order_type,
                    min_signal_strength=min_signal_strength,
                    scalping_mode=use_scalping,
                    quick_close=quick_close,
                    quick_close_target=quick_close_target
                )
            finally:
                shutdown_mt5()
    elif choice == "4":
        # Show interactive chart
        from mt5_chart import show_chart_window
        
        # Check if trading is allowed
        can_trade, trade_msg = check_trading_allowed()
        print(trade_msg)
        
        if can_trade:
            # Ask for symbol
            symbol_input = input(f"{Fore.YELLOW}Enter symbol to chart (e.g., EURUSD): {Style.RESET_ALL}")
            symbol = symbol_input.strip() if symbol_input.strip() else "EURUSD"
            
            # Ask for timeframe
            print(f"\n{Fore.CYAN}Select timeframe:{Style.RESET_ALL}")
            print(f"{Fore.GREEN}1.{Style.RESET_ALL} M1 (1 minute)")
            print(f"{Fore.GREEN}2.{Style.RESET_ALL} M5 (5 minutes)")
            print(f"{Fore.GREEN}3.{Style.RESET_ALL} M15 (15 minutes)")
            print(f"{Fore.GREEN}4.{Style.RESET_ALL} M30 (30 minutes)")
            print(f"{Fore.GREEN}5.{Style.RESET_ALL} H1 (1 hour)")
            print(f"{Fore.GREEN}6.{Style.RESET_ALL} H4 (4 hours)")
            print(f"{Fore.GREEN}7.{Style.RESET_ALL} D1 (Daily)")
            
            timeframe_input = input(f"{Fore.YELLOW}Select timeframe (1-7, default 5): {Style.RESET_ALL}")
            
            timeframes = {
                "1": mt5.TIMEFRAME_M1,
                "2": mt5.TIMEFRAME_M5,
                "3": mt5.TIMEFRAME_M15,
                "4": mt5.TIMEFRAME_M30,
                "5": mt5.TIMEFRAME_H1,
                "6": mt5.TIMEFRAME_H4,
                "7": mt5.TIMEFRAME_D1
            }
            
            timeframe = timeframes.get(timeframe_input, mt5.TIMEFRAME_H1)
            
            # Ask for number of candles
            candles_input = input(f"{Fore.YELLOW}Number of candles to display (default 100): {Style.RESET_ALL}")
            candles = int(candles_input) if candles_input.strip() else 100
            
            # Show the chart
            show_chart_window(symbol, timeframe, candles, allow_trading=can_trade)
        
    elif choice == "5":
        # Check if MetaTrader 5 can be initialized
        if not initialize_mt5():
            print(f"{Fore.RED}Failed to initialize MetaTrader 5{Style.RESET_ALL}")
        else:
            try:
                # Call the function to list available symbols
                list_available_symbols()
            finally:
                # Ensure MT5 is shut down properly
                shutdown_mt5()
    else:
        print(f"{Fore.RED}Invalid choice. Please run the script again and select a valid option (1-5).{Style.RESET_ALL}") 
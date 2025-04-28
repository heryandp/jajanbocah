import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime

def get_account_info():
    """
    Get account information
    
    Returns:
        dict: Account information
    """
    if not mt5.terminal_info():
        print("No connection to MetaTrader 5")
        return None
    
    account_info = mt5.account_info()
    if account_info is None:
        print(f"Failed to get account info. Error code: {mt5.last_error()}")
        return None
    
    # Convert tuple to dictionary
    account_info_dict = {
        "login": account_info.login,
        "server": account_info.server,
        "currency": account_info.currency,
        "leverage": account_info.leverage,
        "balance": account_info.balance,
        "equity": account_info.equity,
        "margin": account_info.margin,
        "margin_free": account_info.margin_free,
        "margin_level": account_info.margin_level,
        "margin_so_call": account_info.margin_so_call,
        "margin_so_so": account_info.margin_so_so
    }
    
    return account_info_dict

def get_positions():
    """
    Get all open positions
    
    Returns:
        pandas.DataFrame: Open positions
    """
    if not mt5.terminal_info():
        print("No connection to MetaTrader 5")
        return None
    
    positions = mt5.positions_get()
    if positions is None or len(positions) == 0:
        print(f"No positions found. Error code: {mt5.last_error()}")
        return pd.DataFrame()
    
    # Convert to DataFrame
    df = pd.DataFrame(list(positions), columns=positions[0]._asdict().keys())
    
    # Add human-readable time
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df['time_update'] = pd.to_datetime(df['time_update'], unit='s')
    
    return df

def get_orders():
    """
    Get all pending orders
    
    Returns:
        pandas.DataFrame: Pending orders
    """
    if not mt5.terminal_info():
        print("No connection to MetaTrader 5")
        return None
    
    orders = mt5.orders_get()
    if orders is None or len(orders) == 0:
        print(f"No orders found. Error code: {mt5.last_error()}")
        return pd.DataFrame()
    
    # Convert to DataFrame
    df = pd.DataFrame(list(orders), columns=orders[0]._asdict().keys())
    
    # Add human-readable time
    df['time_setup'] = pd.to_datetime(df['time_setup'], unit='s')
    df['time_expiration'] = pd.to_datetime(df['time_expiration'], unit='s')
    
    return df

def get_history_orders(days=7):
    """
    Get historical orders
    
    Args:
        days (int): Number of days to look back
    
    Returns:
        pandas.DataFrame: Historical orders
    """
    if not mt5.terminal_info():
        print("No connection to MetaTrader 5")
        return None
    
    # Calculate the start date
    from_date = datetime.now() - pd.Timedelta(days=days)
    
    # Get history orders
    history_orders = mt5.history_orders_get(from_date, datetime.now())
    if history_orders is None or len(history_orders) == 0:
        print(f"No history orders found. Error code: {mt5.last_error()}")
        return pd.DataFrame()
    
    # Convert to DataFrame
    df = pd.DataFrame(list(history_orders), columns=history_orders[0]._asdict().keys())
    
    # Add human-readable time
    df['time_setup'] = pd.to_datetime(df['time_setup'], unit='s')
    df['time_done'] = pd.to_datetime(df['time_done'], unit='s')
    
    return df

def get_history_deals(days=7):
    """
    Get historical deals
    
    Args:
        days (int): Number of days to look back
    
    Returns:
        pandas.DataFrame: Historical deals
    """
    if not mt5.terminal_info():
        print("No connection to MetaTrader 5")
        return None
    
    # Calculate the start date
    from_date = datetime.now() - pd.Timedelta(days=days)
    
    # Get history deals
    history_deals = mt5.history_deals_get(from_date, datetime.now())
    if history_deals is None or len(history_deals) == 0:
        print(f"No history deals found. Error code: {mt5.last_error()}")
        return pd.DataFrame()
    
    # Convert to DataFrame
    df = pd.DataFrame(list(history_deals), columns=history_deals[0]._asdict().keys())
    
    # Add human-readable time
    df['time'] = pd.to_datetime(df['time'], unit='s')
    
    return df 
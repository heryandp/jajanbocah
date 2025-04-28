import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime

def place_market_order(symbol, order_type, volume, stop_loss=0.0, take_profit=0.0, comment=""):
    """
    Place a market order
    
    Args:
        symbol (str): Symbol to trade
        order_type (int): Order type (mt5.ORDER_TYPE_BUY or mt5.ORDER_TYPE_SELL)
        volume (float): Volume in lots
        stop_loss (float, optional): Stop loss price. Defaults to 0.0.
        take_profit (float, optional): Take profit price. Defaults to 0.0.
        comment (str, optional): Order comment. Defaults to "".
    
    Returns:
        dict: Order result
    """
    if not mt5.terminal_info():
        print("No connection to MetaTrader 5")
        return None
    
    # Check if symbol exists
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        print(f"Symbol {symbol} not found")
        return None
    
    if not symbol_info.visible:
        print(f"Symbol {symbol} is not visible, trying to switch on")
        if not mt5.symbol_select(symbol, True):
            print(f"Symbol {symbol} selection failed. Error code: {mt5.last_error()}")
            return None
    
    # Prepare the order request
    price = mt5.symbol_info_tick(symbol).ask if order_type == mt5.ORDER_TYPE_BUY else mt5.symbol_info_tick(symbol).bid
    
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": float(volume),
        "type": order_type,
        "price": price,
        "sl": stop_loss,
        "tp": take_profit,
        "deviation": 20,
        "magic": 234000,
        "comment": comment,
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    
    # Send the order
    result = mt5.order_send(request)
    
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"Order placement failed. Error code: {result.retcode}")
        print(f"Error description: {mt5.last_error()}")
        return None
    
    # Return information about the order
    order_result = {
        "retcode": result.retcode,
        "order": result.order,
        "volume": result.volume,
        "price": result.price,
        "bid": result.bid,
        "ask": result.ask,
        "comment": result.comment,
        "request": request
    }
    
    return order_result

def place_pending_order(symbol, order_type, volume, price, stop_loss=0.0, take_profit=0.0, expiration=None, comment=""):
    """
    Place a pending order
    
    Args:
        symbol (str): Symbol to trade
        order_type (int): Order type (mt5.ORDER_TYPE_BUY_LIMIT, mt5.ORDER_TYPE_SELL_LIMIT, 
                          mt5.ORDER_TYPE_BUY_STOP, mt5.ORDER_TYPE_SELL_STOP)
        volume (float): Volume in lots
        price (float): Order price
        stop_loss (float, optional): Stop loss price. Defaults to 0.0.
        take_profit (float, optional): Take profit price. Defaults to 0.0.
        expiration (datetime, optional): Order expiration date. Defaults to None.
        comment (str, optional): Order comment. Defaults to "".
    
    Returns:
        dict: Order result
    """
    if not mt5.terminal_info():
        print("No connection to MetaTrader 5")
        return None
    
    # Check if symbol exists
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        print(f"Symbol {symbol} not found")
        return None
    
    if not symbol_info.visible:
        print(f"Symbol {symbol} is not visible, trying to switch on")
        if not mt5.symbol_select(symbol, True):
            print(f"Symbol {symbol} selection failed. Error code: {mt5.last_error()}")
            return None
    
    # Prepare the order request
    request = {
        "action": mt5.TRADE_ACTION_PENDING,
        "symbol": symbol,
        "volume": float(volume),
        "type": order_type,
        "price": price,
        "sl": stop_loss,
        "tp": take_profit,
        "deviation": 20,
        "magic": 234000,
        "comment": comment,
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_RETURN,
    }
    
    # Add expiration if provided
    if expiration:
        request["type_time"] = mt5.ORDER_TIME_SPECIFIED
        request["expiration"] = expiration
    
    # Send the order
    result = mt5.order_send(request)
    
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"Order placement failed. Error code: {result.retcode}")
        print(f"Error description: {mt5.last_error()}")
        return None
    
    # Return information about the order
    order_result = {
        "retcode": result.retcode,
        "order": result.order,
        "volume": result.volume,
        "price": result.price,
        "bid": result.bid,
        "ask": result.ask,
        "comment": result.comment,
        "request": request
    }
    
    return order_result

def modify_position(position_id, symbol, stop_loss=None, take_profit=None):
    """
    Modify an existing position
    
    Args:
        position_id (int): Position ticket
        symbol (str): Symbol of the position
        stop_loss (float, optional): New stop loss price. Defaults to None.
        take_profit (float, optional): New take profit price. Defaults to None.
    
    Returns:
        dict: Modification result
    """
    if not mt5.terminal_info():
        print("No connection to MetaTrader 5")
        return None
    
    # Get the position
    position = mt5.positions_get(ticket=position_id)
    if position is None or len(position) == 0:
        print(f"Position {position_id} not found. Error code: {mt5.last_error()}")
        return None
    
    position = position[0]
    
    # If no new SL/TP provided, use existing ones
    if stop_loss is None:
        stop_loss = position.sl
    if take_profit is None:
        take_profit = position.tp
    
    # Prepare the modification request
    request = {
        "action": mt5.TRADE_ACTION_SLTP,
        "symbol": symbol,
        "sl": stop_loss,
        "tp": take_profit,
        "position": position_id
    }
    
    # Send the modification request
    result = mt5.order_send(request)
    
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"Position modification failed. Error code: {result.retcode}")
        print(f"Error description: {mt5.last_error()}")
        return None
    
    # Return information about the modification
    mod_result = {
        "retcode": result.retcode,
        "order": result.order,
        "volume": result.volume,
        "price": result.price,
        "bid": result.bid,
        "ask": result.ask,
        "comment": result.comment,
        "request": request
    }
    
    return mod_result

def close_position(position_id, volume=None):
    """
    Close an existing position
    
    Args:
        position_id (int): Position ticket
        volume (float, optional): Volume to close. If None, close all. Defaults to None.
    
    Returns:
        dict: Close result
    """
    if not mt5.terminal_info():
        print("No connection to MetaTrader 5")
        return None
    
    # Get the position
    position = mt5.positions_get(ticket=position_id)
    if position is None or len(position) == 0:
        print(f"Position {position_id} not found. Error code: {mt5.last_error()}")
        return None
    
    position = position[0]
    
    # If no volume specified, close all
    if volume is None:
        volume = position.volume
    
    # Determine the price and order type for closing
    if position.type == mt5.ORDER_TYPE_BUY:
        price = mt5.symbol_info_tick(position.symbol).bid
        order_type = mt5.ORDER_TYPE_SELL
    else:
        price = mt5.symbol_info_tick(position.symbol).ask
        order_type = mt5.ORDER_TYPE_BUY
    
    # Prepare the close request
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": position.symbol,
        "volume": float(volume),
        "type": order_type,
        "position": position_id,
        "price": price,
        "deviation": 20,
        "magic": 234000,
        "comment": "Close position",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    
    # Send the close request
    result = mt5.order_send(request)
    
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"Position close failed. Error code: {result.retcode}")
        print(f"Error description: {mt5.last_error()}")
        return None
    
    # Return information about the close
    close_result = {
        "retcode": result.retcode,
        "order": result.order,
        "volume": result.volume,
        "price": result.price,
        "bid": result.bid,
        "ask": result.ask,
        "comment": result.comment,
        "request": request
    }
    
    return close_result

def cancel_order(order_id):
    """
    Cancel a pending order
    
    Args:
        order_id (int): Order ticket
    
    Returns:
        dict: Cancel result
    """
    if not mt5.terminal_info():
        print("No connection to MetaTrader 5")
        return None
    
    # Get the order
    order = mt5.orders_get(ticket=order_id)
    if order is None or len(order) == 0:
        print(f"Order {order_id} not found. Error code: {mt5.last_error()}")
        return None
    
    # Prepare the cancel request
    request = {
        "action": mt5.TRADE_ACTION_REMOVE,
        "order": order_id,
    }
    
    # Send the cancel request
    result = mt5.order_send(request)
    
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"Order cancel failed. Error code: {result.retcode}")
        print(f"Error description: {mt5.last_error()}")
        return None
    
    # Return information about the cancellation
    cancel_result = {
        "retcode": result.retcode,
        "order": result.order,
        "volume": result.volume,
        "price": result.price,
        "bid": result.bid,
        "ask": result.ask,
        "comment": result.comment,
        "request": request
    }
    
    return cancel_result 
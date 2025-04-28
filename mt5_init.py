import os
import MetaTrader5 as mt5
from dotenv import load_dotenv

def initialize_mt5():
    """
    Initialize connection to MetaTrader 5 terminal
    
    Returns:
        bool: True if initialization was successful, False otherwise
    """
    # Load environment variables
    load_dotenv()
    
    # Initialize MetaTrader 5
    if not mt5.initialize():
        print(f"MetaTrader5 initialization failed. Error code: {mt5.last_error()}")
        return False
    
    # Login to MetaTrader 5 account
    account = os.getenv('MT5_ACCOUNT')
    password = os.getenv('MT5_PASSWORD')
    server = os.getenv('MT5_SERVER')
    
    if account and password:
        account = int(account)
        authorized = mt5.login(account, password=password, server=server)
        if not authorized:
            print(f"Login failed. Error code: {mt5.last_error()}")
            mt5.shutdown()
            return False
        
        print(f"Connected to account #{account}")
    else:
        print("No login credentials provided, using default connection")
    
    # Verify connection status
    if not mt5.terminal_info():
        print(f"Failed to get terminal info. Error code: {mt5.last_error()}")
        mt5.shutdown()
        return False
    
    print(f"MetaTrader5 version: {mt5.version()}")
    return True

def shutdown_mt5():
    """
    Shutdown connection to MetaTrader 5 terminal
    """
    mt5.shutdown()
    print("MetaTrader5 connection closed") 
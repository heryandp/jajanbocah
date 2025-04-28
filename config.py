"""
Configuration settings for the trading system
"""

# MetaTrader 5 Connection Settings
MT5_SETTINGS = {
    'account': 12345678,  # Your MT5 account number
    'password': 'your_password',  # Your MT5 password
    'server': 'your_broker_server',  # Your broker's server
}

# Trading Settings
TRADING_SETTINGS = {
    'risk_percent': 1.0,  # Risk per trade in percentage
    'min_signal_strength': 3,  # Minimum signal strength for auto-trading
    'order_type': 'MARKET',  # Order type: MARKET, LIMIT, STOP, STOP_LIMIT
    'auto_trade': False,  # Enable/disable auto-trading
}

# Monitoring Settings
MONITORING_SETTINGS = {
    'interval': 5,  # Time interval between checks in seconds
    'max_records': 1000,  # Maximum number of price records to keep
    'save_data': True,  # Whether to save price data
    'data_dir': 'price_data',  # Directory to save data files
}

# Symbol Settings
SYMBOL_SETTINGS = {
    'symbols': ['EURUSD', 'GBPUSD', 'USDJPY'],  # List of symbols to monitor
    'timeframe': 'M15',  # Default timeframe
}

# Technical Analysis Settings
TECHNICAL_SETTINGS = {
    'rsi_period': 14,
    'stoch_period': 14,
    'macd_fast': 12,
    'macd_slow': 26,
    'macd_signal': 9,
    'bb_period': 20,
    'bb_std': 2,
    'sma_periods': [5, 20, 50],
    'ema_periods': [9, 12, 26, 50],
}

# Order Settings
ORDER_SETTINGS = {
    'magic': 234000,  # Magic number for order identification
    'deviation': 20,  # Maximum price deviation in points
    'filling': 'IOC',  # Order filling type: IOC, FOK, RETURN
    'time': 'GTC',  # Order time type: GTC, DAY, SPECIFIED
}

# Notification Settings
NOTIFICATION_SETTINGS = {
    'enable': False,  # Enable/disable notifications
    'telegram_bot_token': 'your_telegram_bot_token',
    'telegram_chat_id': 'your_telegram_chat_id',
}

# Time Settings
TIME_SETTINGS = {
    'start_date': '2024-01-01',  # Start date for historical data
    'timezone': 'UTC',  # Timezone for data processing
}

# Risk Management Settings
RISK_MANAGEMENT = {
    'max_open_positions': 3,  # Maximum number of open positions
    'max_daily_trades': 10,  # Maximum number of trades per day
    'max_daily_loss': 5.0,  # Maximum daily loss in percentage
    'min_risk_reward': 1.5,  # Minimum risk/reward ratio
}

# Logging Settings
LOGGING_SETTINGS = {
    'level': 'INFO',  # Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL
    'file': 'trading.log',  # Log file name
    'max_size': 10485760,  # Maximum log file size in bytes (10MB)
    'backup_count': 5,  # Number of backup files to keep
} 
import sqlite3
import pandas as pd
from datetime import datetime
import os
import json

class TradingDatabase:
    def __init__(self, db_file="trading.db"):
        self.db_file = db_file
        self.conn = None
        self.cursor = None
        self.init_db()
        
    def init_db(self):
        """Initialize database and create tables if they don't exist"""
        self.conn = sqlite3.connect(self.db_file)
        self.cursor = self.conn.cursor()
        
        # Create settings table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP
            )
        ''')
        
        # Create trading history table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS trading_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT,
                order_type TEXT,
                volume REAL,
                price REAL,
                stop_loss REAL,
                take_profit REAL,
                profit REAL,
                created_at TIMESTAMP
            )
        ''')
        
        self.conn.commit()
        
    def save_setting(self, key, value):
        """Save a setting to the database"""
        self.cursor.execute(
            "INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES (?, ?, ?)",
            (key, json.dumps(value), datetime.now())
        )
        self.conn.commit()
        
    def get_setting(self, key, default=None):
        """Get a setting from the database"""
        self.cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        result = self.cursor.fetchone()
        if result:
            return json.loads(result[0])
        return default
        
    def save_trade(self, symbol, order_type, volume, price, stop_loss, take_profit, profit):
        """Save a trade to the history"""
        self.cursor.execute(
            "INSERT INTO trading_history (symbol, order_type, volume, price, stop_loss, take_profit, profit, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (symbol, order_type, volume, price, stop_loss, take_profit, profit, datetime.now())
        )
        self.conn.commit()
        
    def get_trading_history(self, limit=100):
        """Get trading history"""
        self.cursor.execute(
            "SELECT * FROM trading_history ORDER BY created_at DESC LIMIT ?",
            (limit,)
        )
        columns = [description[0] for description in self.cursor.description]
        return [dict(zip(columns, row)) for row in self.cursor.fetchall()]
        
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None
            
    def save_price_data(self, symbol, timeframe, df):
        """Save price data to database"""
        for _, row in df.iterrows():
            self.cursor.execute('''
            INSERT INTO price_history (symbol, timeframe, time, open, high, low, close, volume)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (symbol, timeframe, row['time'], row['open'], row['high'], 
                  row['low'], row['close'], row['volume']))
            
            price_id = self.cursor.lastrowid
            
            # Save indicators if they exist
            if 'sma_5' in row:
                self.cursor.execute('''
                INSERT INTO indicators (
                    price_history_id, sma_5, sma_20, sma_50, ema_9, ema_12, ema_26, ema_50,
                    rsi_14, stoch_k, stoch_d, bb_upper, bb_middle, bb_lower,
                    macd, signal, histogram
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (price_id, row.get('sma_5'), row.get('sma_20'), row.get('sma_50'),
                      row.get('ema_9'), row.get('ema_12'), row.get('ema_26'), row.get('ema_50'),
                      row.get('rsi_14'), row.get('stoch_k'), row.get('stoch_d'),
                      row.get('bb_upper'), row.get('bb_middle'), row.get('bb_lower'),
                      row.get('macd'), row.get('signal'), row.get('histogram')))
                
        self.conn.commit()
        
    def get_price_history(self, symbol, timeframe, start_date=None, end_date=None):
        """Get price history from database"""
        query = '''
        SELECT ph.*, i.* 
        FROM price_history ph
        LEFT JOIN indicators i ON ph.id = i.price_history_id
        WHERE ph.symbol = ? AND ph.timeframe = ?
        '''
        params = [symbol, timeframe]
        
        if start_date:
            query += ' AND ph.time >= ?'
            params.append(start_date)
        if end_date:
            query += ' AND ph.time <= ?'
            params.append(end_date)
            
        query += ' ORDER BY ph.time ASC'
        
        df = pd.read_sql_query(query, self.conn, params=params)
        return df
        
    def get_trades(self, symbol=None, status=None, start_date=None, end_date=None):
        """Get trades from database"""
        query = 'SELECT * FROM trades WHERE 1=1'
        params = []
        
        if symbol:
            query += ' AND symbol = ?'
            params.append(symbol)
        if status:
            query += ' AND status = ?'
            params.append(status)
        if start_date:
            query += ' AND time >= ?'
            params.append(start_date)
        if end_date:
            query += ' AND time <= ?'
            params.append(end_date)
            
        query += ' ORDER BY time DESC'
        
        df = pd.read_sql_query(query, self.conn, params=params)
        return df
        
    def get_signals(self, symbol=None, timeframe=None, start_date=None, end_date=None):
        """Get signals from database"""
        query = 'SELECT * FROM signals WHERE 1=1'
        params = []
        
        if symbol:
            query += ' AND symbol = ?'
            params.append(symbol)
        if timeframe:
            query += ' AND timeframe = ?'
            params.append(timeframe)
        if start_date:
            query += ' AND time >= ?'
            params.append(start_date)
        if end_date:
            query += ' AND time <= ?'
            params.append(end_date)
            
        query += ' ORDER BY time DESC'
        
        df = pd.read_sql_query(query, self.conn, params=params)
        return df
        
    def backup_database(self, backup_path=None):
        """Create a backup of the database"""
        if not backup_path:
            backup_path = f"trading_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            
        with sqlite3.connect(backup_path) as backup_conn:
            self.conn.backup(backup_conn)
            
        return backup_path 
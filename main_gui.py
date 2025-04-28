import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QTabWidget, QPushButton, QLabel, 
                            QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox,
                            QCheckBox, QGroupBox, QFormLayout, QMessageBox,
                            QFileDialog, QTextEdit, QTableWidget, QTableWidgetItem,
                            QDateEdit, QCalendarWidget)
from PyQt5.QtCore import Qt, QTimer, QDate
from PyQt5.QtGui import QFont, QIcon
import MetaTrader5 as mt5
from datetime import datetime
import pandas as pd
from config import *
from mt5_init import initialize_mt5, shutdown_mt5
from mt5_monitor import monitor_symbols, get_symbol_price
from mt5_chart import show_chart_window
from database import TradingDatabase

class TradingGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Trading System")
        self.setGeometry(100, 100, 1200, 800)
        
        # Initialize MT5
        if not initialize_mt5():
            QMessageBox.critical(self, "Error", "Failed to initialize MetaTrader 5")
            sys.exit(1)
            
        # Initialize database
        self.db = TradingDatabase()
            
        self.init_ui()
        self.setup_timer()
        
    def init_ui(self):
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Create tab widget
        tabs = QTabWidget()
        main_layout.addWidget(tabs)
        
        # Add tabs
        tabs.addTab(self.create_dashboard_tab(), "Dashboard")
        tabs.addTab(self.create_settings_tab(), "Settings")
        tabs.addTab(self.create_monitoring_tab(), "Monitoring")
        tabs.addTab(self.create_history_tab(), "History")
        tabs.addTab(self.create_database_tab(), "Database")
        
    def create_dashboard_tab(self):
        dashboard = QWidget()
        layout = QVBoxLayout(dashboard)
        
        # Status group
        status_group = QGroupBox("System Status")
        status_layout = QFormLayout()
        
        self.connection_status = QLabel("Connected")
        self.connection_status.setStyleSheet("color: green")
        status_layout.addRow("MT5 Status:", self.connection_status)
        
        self.account_info = QLabel("Account: -")
        status_layout.addRow("Account Info:", self.account_info)
        
        self.balance_info = QLabel("Balance: -")
        status_layout.addRow("Balance:", self.balance_info)
        
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        # Quick actions
        actions_group = QGroupBox("Quick Actions")
        actions_layout = QHBoxLayout()
        
        self.start_monitoring_btn = QPushButton("Start Monitoring")
        self.start_monitoring_btn.clicked.connect(self.start_monitoring)
        actions_layout.addWidget(self.start_monitoring_btn)
        
        self.stop_monitoring_btn = QPushButton("Stop Monitoring")
        self.stop_monitoring_btn.clicked.connect(self.stop_monitoring)
        self.stop_monitoring_btn.setEnabled(False)
        actions_layout.addWidget(self.stop_monitoring_btn)
        
        self.show_chart_btn = QPushButton("Show Chart")
        self.show_chart_btn.clicked.connect(self.show_chart)
        actions_layout.addWidget(self.show_chart_btn)
        
        actions_group.setLayout(actions_layout)
        layout.addWidget(actions_group)
        
        # Price table
        self.price_table = QTableWidget()
        self.price_table.setColumnCount(5)
        self.price_table.setHorizontalHeaderLabels(["Symbol", "Bid", "Ask", "Spread", "Time"])
        layout.addWidget(self.price_table)
        
        return dashboard
        
    def create_settings_tab(self):
        settings = QWidget()
        layout = QVBoxLayout(settings)
        
        # MT5 Settings
        mt5_group = QGroupBox("MetaTrader 5 Settings")
        mt5_layout = QFormLayout()
        
        self.account_input = QLineEdit(str(MT5_SETTINGS['account']))
        mt5_layout.addRow("Account:", self.account_input)
        
        self.password_input = QLineEdit(MT5_SETTINGS['password'])
        self.password_input.setEchoMode(QLineEdit.Password)
        mt5_layout.addRow("Password:", self.password_input)
        
        self.server_input = QLineEdit(MT5_SETTINGS['server'])
        mt5_layout.addRow("Server:", self.server_input)
        
        mt5_group.setLayout(mt5_layout)
        layout.addWidget(mt5_group)
        
        # Trading Settings
        trading_group = QGroupBox("Trading Settings")
        trading_layout = QFormLayout()
        
        self.risk_input = QDoubleSpinBox()
        self.risk_input.setRange(0.1, 10.0)
        self.risk_input.setValue(TRADING_SETTINGS['risk_percent'])
        trading_layout.addRow("Risk %:", self.risk_input)
        
        self.signal_strength_input = QSpinBox()
        self.signal_strength_input.setRange(1, 5)
        self.signal_strength_input.setValue(TRADING_SETTINGS['min_signal_strength'])
        trading_layout.addRow("Min Signal Strength:", self.signal_strength_input)
        
        self.order_type_combo = QComboBox()
        self.order_type_combo.addItems(["MARKET", "LIMIT", "STOP", "STOP_LIMIT"])
        self.order_type_combo.setCurrentText(TRADING_SETTINGS['order_type'])
        trading_layout.addRow("Order Type:", self.order_type_combo)
        
        self.auto_trade_check = QCheckBox()
        self.auto_trade_check.setChecked(TRADING_SETTINGS['auto_trade'])
        trading_layout.addRow("Auto Trade:", self.auto_trade_check)
        
        # Tambahkan mode scalping
        self.scalping_check = QCheckBox()
        self.scalping_check.setChecked(TRADING_SETTINGS.get('scalping_mode', False))
        trading_layout.addRow("Scalping Mode:", self.scalping_check)
        
        # Tambahkan quick close settings
        self.quick_close_check = QCheckBox()
        self.quick_close_check.setChecked(TRADING_SETTINGS.get('quick_close', False))
        trading_layout.addRow("Quick Close:", self.quick_close_check)
        
        self.quick_close_target = QDoubleSpinBox()
        self.quick_close_target.setRange(0.1, 100.0)
        self.quick_close_target.setValue(TRADING_SETTINGS.get('quick_close_target', 5.0))
        self.quick_close_target.setSuffix(" pips")
        trading_layout.addRow("Quick Close Target:", self.quick_close_target)
        
        trading_group.setLayout(trading_layout)
        layout.addWidget(trading_group)
        
        # Symbol Settings
        symbol_group = QGroupBox("Symbol Settings")
        symbol_layout = QFormLayout()
        
        self.symbols_input = QLineEdit(",".join(SYMBOL_SETTINGS['symbols']))
        symbol_layout.addRow("Symbols:", self.symbols_input)
        
        self.timeframe_combo = QComboBox()
        self.timeframe_combo.addItems(["M1", "M5", "M15", "M30", "H1", "H4", "D1"])
        self.timeframe_combo.setCurrentText(SYMBOL_SETTINGS['timeframe'])
        symbol_layout.addRow("Timeframe:", self.timeframe_combo)
        
        symbol_group.setLayout(symbol_layout)
        layout.addWidget(symbol_group)
        
        # Save button
        save_btn = QPushButton("Save Settings")
        save_btn.clicked.connect(self.save_settings)
        layout.addWidget(save_btn)
        
        return settings
        
    def create_monitoring_tab(self):
        monitoring = QWidget()
        layout = QVBoxLayout(monitoring)
        
        # Monitoring settings
        monitor_group = QGroupBox("Monitoring Settings")
        monitor_layout = QFormLayout()
        
        self.interval_input = QSpinBox()
        self.interval_input.setRange(1, 60)
        self.interval_input.setValue(MONITORING_SETTINGS['interval'])
        monitor_layout.addRow("Interval (seconds):", self.interval_input)
        
        self.max_records_input = QSpinBox()
        self.max_records_input.setRange(100, 10000)
        self.max_records_input.setValue(MONITORING_SETTINGS['max_records'])
        monitor_layout.addRow("Max Records:", self.max_records_input)
        
        self.save_data_check = QCheckBox()
        self.save_data_check.setChecked(MONITORING_SETTINGS['save_data'])
        monitor_layout.addRow("Save Data:", self.save_data_check)
        
        self.data_dir_input = QLineEdit(MONITORING_SETTINGS['data_dir'])
        monitor_layout.addRow("Data Directory:", self.data_dir_input)
        
        monitor_group.setLayout(monitor_layout)
        layout.addWidget(monitor_group)
        
        # Log display
        log_group = QGroupBox("Monitoring Log")
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        log_group.setLayout(QVBoxLayout())
        log_group.layout().addWidget(self.log_display)
        layout.addWidget(log_group)
        
        return monitoring
        
    def create_history_tab(self):
        history = QWidget()
        layout = QVBoxLayout(history)
        
        # History table
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(7)
        self.history_table.setHorizontalHeaderLabels([
            "Time", "Symbol", "Type", "Volume", "Price", "SL", "TP"
        ])
        layout.addWidget(self.history_table)
        
        # Load history button
        load_btn = QPushButton("Load History")
        load_btn.clicked.connect(self.load_history)
        layout.addWidget(load_btn)
        
        return history
        
    def create_database_tab(self):
        database = QWidget()
        layout = QVBoxLayout(database)
        
        # Database operations group
        db_group = QGroupBox("Database Operations")
        db_layout = QFormLayout()
        
        # Backup button
        backup_btn = QPushButton("Backup Database")
        backup_btn.clicked.connect(self.backup_database)
        db_layout.addRow(backup_btn)
        
        # Date range selection
        date_group = QGroupBox("Date Range")
        date_layout = QHBoxLayout()
        
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate().addDays(-7))
        date_layout.addWidget(QLabel("Start Date:"))
        date_layout.addWidget(self.start_date)
        
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate())
        date_layout.addWidget(QLabel("End Date:"))
        date_layout.addWidget(self.end_date)
        
        date_group.setLayout(date_layout)
        db_layout.addRow(date_group)
        
        # Export buttons
        export_group = QGroupBox("Export Data")
        export_layout = QHBoxLayout()
        
        export_prices_btn = QPushButton("Export Price History")
        export_prices_btn.clicked.connect(self.export_price_history)
        export_layout.addWidget(export_prices_btn)
        
        export_trades_btn = QPushButton("Export Trades")
        export_trades_btn.clicked.connect(self.export_trades)
        export_layout.addWidget(export_trades_btn)
        
        export_signals_btn = QPushButton("Export Signals")
        export_signals_btn.clicked.connect(self.export_signals)
        export_layout.addWidget(export_signals_btn)
        
        export_group.setLayout(export_layout)
        db_layout.addRow(export_group)
        
        db_group.setLayout(db_layout)
        layout.addWidget(db_group)
        
        # Database statistics
        stats_group = QGroupBox("Database Statistics")
        stats_layout = QFormLayout()
        
        self.price_count = QLabel("0")
        stats_layout.addRow("Price Records:", self.price_count)
        
        self.trade_count = QLabel("0")
        stats_layout.addRow("Trade Records:", self.trade_count)
        
        self.signal_count = QLabel("0")
        stats_layout.addRow("Signal Records:", self.signal_count)
        
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)
        
        return database
        
    def setup_timer(self):
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_dashboard)
        self.update_timer.start(1000)  # Update every second
        
    def update_dashboard(self):
        # Update connection status
        if mt5.terminal_info():
            self.connection_status.setText("Connected")
            self.connection_status.setStyleSheet("color: green")
        else:
            self.connection_status.setText("Disconnected")
            self.connection_status.setStyleSheet("color: red")
            
        # Update account info
        account_info = mt5.account_info()
        if account_info:
            self.account_info.setText(f"Account: {account_info.login}")
            self.balance_info.setText(f"Balance: {account_info.balance:.2f}")
            
        # Update price table
        symbols = self.symbols_input.text().split(",")
        self.price_table.setRowCount(len(symbols))
        for i, symbol in enumerate(symbols):
            price_data = get_symbol_price(symbol)
            if price_data:
                self.price_table.setItem(i, 0, QTableWidgetItem(symbol))
                self.price_table.setItem(i, 1, QTableWidgetItem(str(price_data['bid'])))
                self.price_table.setItem(i, 2, QTableWidgetItem(str(price_data['ask'])))
                self.price_table.setItem(i, 3, QTableWidgetItem(str(price_data['spread'])))
                self.price_table.setItem(i, 4, QTableWidgetItem(price_data['time']))
                
    def start_monitoring(self):
        symbols = self.symbols_input.text().split(",")
        interval = self.interval_input.value()
        max_records = self.max_records_input.value()
        save_data = self.save_data_check.isChecked()
        data_dir = self.data_dir_input.text()
        
        self.start_monitoring_btn.setEnabled(False)
        self.stop_monitoring_btn.setEnabled(True)
        
        # Start monitoring in a separate thread
        # (Implementation depends on your threading setup)
        
    def stop_monitoring(self):
        self.start_monitoring_btn.setEnabled(True)
        self.stop_monitoring_btn.setEnabled(False)
        
        # Stop monitoring
        # (Implementation depends on your threading setup)
        
    def show_chart(self):
        symbol = self.symbols_input.text().split(",")[0]  # Get first symbol
        timeframe = self.timeframe_combo.currentText()
        tf_map = {
            "M1": mt5.TIMEFRAME_M1,
            "M5": mt5.TIMEFRAME_M5,
            "M15": mt5.TIMEFRAME_M15,
            "M30": mt5.TIMEFRAME_M30,
            "H1": mt5.TIMEFRAME_H1,
            "H4": mt5.TIMEFRAME_H4,
            "D1": mt5.TIMEFRAME_D1,
            "W1": mt5.TIMEFRAME_W1
        }
        timeframe = tf_map.get(timeframe, mt5.TIMEFRAME_M15)
        
        # Create and show chart window
        self.chart_window = show_chart_window(symbol, timeframe)
        self.chart_window.show()
        
    def save_settings(self):
        # Save settings to database
        db = TradingDatabase()
        
        # Save MT5 settings
        mt5_settings = {
            'account': int(self.account_input.text()),
            'password': self.password_input.text(),
            'server': self.server_input.text()
        }
        db.save_setting('mt5_settings', mt5_settings)
        
        # Save trading settings
        trading_settings = {
            'risk_percent': self.risk_input.value(),
            'min_signal_strength': self.signal_strength_input.value(),
            'order_type': self.order_type_combo.currentText(),
            'auto_trade': self.auto_trade_check.isChecked(),
            'scalping_mode': self.scalping_check.isChecked(),
            'quick_close': self.quick_close_check.isChecked(),
            'quick_close_target': self.quick_close_target.value()
        }
        db.save_setting('trading_settings', trading_settings)
        
        # Save symbol settings
        symbol_settings = {
            'symbols': self.symbols_input.text().split(","),
            'timeframe': self.timeframe_combo.currentText()
        }
        db.save_setting('symbol_settings', symbol_settings)
        
        # Save monitoring settings
        monitoring_settings = {
            'interval': self.interval_input.value(),
            'max_records': self.max_records_input.value(),
            'save_data': self.save_data_check.isChecked(),
            'data_dir': self.data_dir_input.text()
        }
        db.save_setting('monitoring_settings', monitoring_settings)
        
        db.close()
        QMessageBox.information(self, "Success", "Settings saved successfully")
    
    def load_settings(self):
        """Load settings from database"""
        db = TradingDatabase()
        
        # Load MT5 settings
        mt5_settings = db.get_setting('mt5_settings', {})
        self.account_input.setText(str(mt5_settings.get('account', '')))
        self.password_input.setText(mt5_settings.get('password', ''))
        self.server_input.setText(mt5_settings.get('server', ''))
        
        # Load trading settings
        trading_settings = db.get_setting('trading_settings', {})
        self.risk_input.setValue(trading_settings.get('risk_percent', 1.0))
        self.signal_strength_input.setValue(trading_settings.get('min_signal_strength', 3))
        self.order_type_combo.setCurrentText(trading_settings.get('order_type', 'MARKET'))
        self.auto_trade_check.setChecked(trading_settings.get('auto_trade', False))
        self.scalping_check.setChecked(trading_settings.get('scalping_mode', False))
        self.quick_close_check.setChecked(trading_settings.get('quick_close', False))
        self.quick_close_target.setValue(trading_settings.get('quick_close_target', 5.0))
        
        # Load symbol settings
        symbol_settings = db.get_setting('symbol_settings', {})
        self.symbols_input.setText(','.join(symbol_settings.get('symbols', [])))
        self.timeframe_combo.setCurrentText(symbol_settings.get('timeframe', 'M15'))
        
        # Load monitoring settings
        monitoring_settings = db.get_setting('monitoring_settings', {})
        self.interval_input.setValue(monitoring_settings.get('interval', 5))
        self.max_records_input.setValue(monitoring_settings.get('max_records', 1000))
        self.save_data_check.setChecked(monitoring_settings.get('save_data', True))
        self.data_dir_input.setText(monitoring_settings.get('data_dir', 'price_data'))
        
        db.close()
        
    def load_history(self):
        # Load trading history
        # (Implementation depends on your history storage method)
        pass
        
    def backup_database(self):
        try:
            backup_path = self.db.backup_database()
            QMessageBox.information(self, "Success", f"Database backed up to: {backup_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to backup database: {str(e)}")
            
    def export_price_history(self):
        try:
            start_date = self.start_date.date().toPyDate()
            end_date = self.end_date.date().toPyDate()
            
            # Get symbols from settings
            symbols = self.symbols_input.text().split(",")
            timeframe = self.timeframe_combo.currentText()
            
            # Create export directory if it doesn't exist
            export_dir = "exports"
            if not os.path.exists(export_dir):
                os.makedirs(export_dir)
                
            # Export data for each symbol
            for symbol in symbols:
                df = self.db.get_price_history(symbol, timeframe, start_date, end_date)
                if not df.empty:
                    filename = f"{export_dir}/price_history_{symbol}_{timeframe}_{start_date}_{end_date}.csv"
                    df.to_csv(filename, index=False)
                    
            QMessageBox.information(self, "Success", "Price history exported successfully")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export price history: {str(e)}")
            
    def export_trades(self):
        try:
            start_date = self.start_date.date().toPyDate()
            end_date = self.end_date.date().toPyDate()
            
            # Get symbols from settings
            symbols = self.symbols_input.text().split(",")
            
            # Create export directory if it doesn't exist
            export_dir = "exports"
            if not os.path.exists(export_dir):
                os.makedirs(export_dir)
                
            # Export data for each symbol
            for symbol in symbols:
                df = self.db.get_trades(symbol, start_date=start_date, end_date=end_date)
                if not df.empty:
                    filename = f"{export_dir}/trades_{symbol}_{start_date}_{end_date}.csv"
                    df.to_csv(filename, index=False)
                    
            QMessageBox.information(self, "Success", "Trades exported successfully")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export trades: {str(e)}")
            
    def export_signals(self):
        try:
            start_date = self.start_date.date().toPyDate()
            end_date = self.end_date.date().toPyDate()
            
            # Get symbols from settings
            symbols = self.symbols_input.text().split(",")
            timeframe = self.timeframe_combo.currentText()
            
            # Create export directory if it doesn't exist
            export_dir = "exports"
            if not os.path.exists(export_dir):
                os.makedirs(export_dir)
                
            # Export data for each symbol
            for symbol in symbols:
                df = self.db.get_signals(symbol, timeframe, start_date, end_date)
                if not df.empty:
                    filename = f"{export_dir}/signals_{symbol}_{timeframe}_{start_date}_{end_date}.csv"
                    df.to_csv(filename, index=False)
                    
            QMessageBox.information(self, "Success", "Signals exported successfully")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export signals: {str(e)}")
            
    def update_database_stats(self):
        try:
            # Get price count
            self.cursor.execute("SELECT COUNT(*) FROM price_history")
            self.price_count.setText(str(self.cursor.fetchone()[0]))
            
            # Get trade count
            self.cursor.execute("SELECT COUNT(*) FROM trades")
            self.trade_count.setText(str(self.cursor.fetchone()[0]))
            
            # Get signal count
            self.cursor.execute("SELECT COUNT(*) FROM signals")
            self.signal_count.setText(str(self.cursor.fetchone()[0]))
        except Exception as e:
            print(f"Error updating database stats: {str(e)}")
            
    def closeEvent(self, event):
        self.db.close()
        shutdown_mt5()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TradingGUI()
    window.show()
    sys.exit(app.exec_()) 
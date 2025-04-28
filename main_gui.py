import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QTabWidget, QPushButton, QLabel, 
                            QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox,
                            QCheckBox, QGroupBox, QFormLayout, QMessageBox,
                            QFileDialog, QTextEdit, QTableWidget, QTableWidgetItem,
                            QDateEdit, QCalendarWidget, QFrame, QListWidget, QDialog, QDialogButtonBox)
from PyQt5.QtCore import Qt, QTimer, QDate
from PyQt5.QtGui import QFont, QIcon
import MetaTrader5 as mt5
from datetime import datetime, timedelta
import pandas as pd
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
        
        # Load default settings if not exists
        self.load_default_settings()
            
        self.init_ui()
        self.setup_timer()
        
    def load_default_settings(self):
        """Load default settings if not exists in database"""
        try:
            # Check if settings exist
            mt5_settings = self.db.get_setting('mt5_settings')
            if not mt5_settings:
                # Save default MT5 settings
                self.db.save_setting('mt5_settings', {
                    'account': '',
                    'password': '',
                    'server': ''
                })
                
            trading_settings = self.db.get_setting('trading_settings')
            if not trading_settings:
                # Save default trading settings
                self.db.save_setting('trading_settings', {
                    'risk_percent': 1.0,
                    'min_signal_strength': 3,
                    'order_type': 'MARKET',
                    'auto_trade': False,
                    'scalping_mode': False,
                    'quick_close': False,
                    'quick_close_target': 5.0
                })
                
            symbol_settings = self.db.get_setting('symbol_settings')
            if not symbol_settings:
                # Save default symbol settings
                self.db.save_setting('symbol_settings', {
                    'symbols': ['EURUSD', 'GBPUSD'],
                    'timeframe': 'M15'
                })
                
            monitoring_settings = self.db.get_setting('monitoring_settings')
            if not monitoring_settings:
                # Save default monitoring settings
                self.db.save_setting('monitoring_settings', {
                    'interval': 5,
                    'max_records': 1000,
                    'save_data': True,
                    'data_dir': 'price_data'
                })
                
        except Exception as e:
            print(f"Error loading default settings: {str(e)}")
            
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
        tabs.addTab(self.create_pairs_tab(), "Pairs")
        tabs.addTab(self.create_monitoring_tab(), "Monitoring")
        tabs.addTab(self.create_history_tab(), "History")
        tabs.addTab(self.create_signals_tab(), "Signals")
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
        actions_layout = QVBoxLayout()
        
        # Add explanation labels
        monitor_label = QLabel("Monitoring: Real-time price and signal monitoring")
        monitor_label.setStyleSheet("color: blue; font-style: italic;")
        actions_layout.addWidget(monitor_label)
        
        monitor_buttons = QHBoxLayout()
        self.start_monitoring_btn = QPushButton("Start Monitoring")
        self.start_monitoring_btn.clicked.connect(self.start_monitoring)
        monitor_buttons.addWidget(self.start_monitoring_btn)
        
        self.stop_monitoring_btn = QPushButton("Stop Monitoring")
        self.stop_monitoring_btn.clicked.connect(self.stop_monitoring)
        self.stop_monitoring_btn.setEnabled(False)
        monitor_buttons.addWidget(self.stop_monitoring_btn)
        
        actions_layout.addLayout(monitor_buttons)
        
        # Add separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        actions_layout.addWidget(separator)
        
        # Add chart explanation
        chart_label = QLabel("Chart: Technical analysis and manual trading")
        chart_label.setStyleSheet("color: green; font-style: italic;")
        actions_layout.addWidget(chart_label)
        
        chart_buttons = QHBoxLayout()
        self.show_chart_btn = QPushButton("Show Chart")
        self.show_chart_btn.clicked.connect(self.show_chart)
        chart_buttons.addWidget(self.show_chart_btn)
        
        actions_layout.addLayout(chart_buttons)
        
        actions_group.setLayout(actions_layout)
        layout.addWidget(actions_group)
        
        # Price table
        self.price_table = QTableWidget()
        self.price_table.setColumnCount(6)
        self.price_table.setHorizontalHeaderLabels(["Symbol", "Bid", "Ask", "Spread", "Change", "Time"])
        
        # Set column widths
        self.price_table.setColumnWidth(0, 100)  # Symbol
        self.price_table.setColumnWidth(1, 100)  # Bid
        self.price_table.setColumnWidth(2, 100)  # Ask
        self.price_table.setColumnWidth(3, 80)   # Spread
        self.price_table.setColumnWidth(4, 80)   # Change
        self.price_table.setColumnWidth(5, 150)  # Time
        
        # Enable sorting
        self.price_table.setSortingEnabled(True)
        
        # Enable alternating row colors
        self.price_table.setAlternatingRowColors(True)
        
        # Enable selection
        self.price_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.price_table.setSelectionMode(QTableWidget.SingleSelection)
        
        # Enable horizontal header to be clickable
        header = self.price_table.horizontalHeader()
        header.setSectionsClickable(True)
        header.sectionClicked.connect(self.on_header_clicked)
        
        # Store previous prices for comparison
        self.previous_prices = {}
        
        layout.addWidget(self.price_table)
        
        return dashboard
        
    def on_header_clicked(self, logical_index):
        """Handle header click for sorting"""
        self.price_table.sortItems(logical_index)
        
    def update_dashboard(self):
        """Update dashboard with current data"""
        try:
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
                symbol = symbol.strip()
                price_data = get_symbol_price(symbol)
                
                if price_data:
                    # Get previous price for comparison
                    prev_price = self.previous_prices.get(symbol, {'bid': price_data['bid'], 'ask': price_data['ask']})
                    
                    # Calculate price change
                    bid_change = price_data['bid'] - prev_price['bid']
                    ask_change = price_data['ask'] - prev_price['ask']
                    
                    # Set items
                    self.price_table.setItem(i, 0, QTableWidgetItem(symbol))
                    
                    # Bid with color
                    bid_item = QTableWidgetItem(f"{price_data['bid']:.5f}")
                    if bid_change > 0:
                        bid_item.setForeground(Qt.darkGreen)
                        bid_item.setText(f"↑ {price_data['bid']:.5f}")
                    elif bid_change < 0:
                        bid_item.setForeground(Qt.darkRed)
                        bid_item.setText(f"↓ {price_data['bid']:.5f}")
                    self.price_table.setItem(i, 1, bid_item)
                    
                    # Ask with color
                    ask_item = QTableWidgetItem(f"{price_data['ask']:.5f}")
                    if ask_change > 0:
                        ask_item.setForeground(Qt.darkGreen)
                        ask_item.setText(f"↑ {price_data['ask']:.5f}")
                    elif ask_change < 0:
                        ask_item.setForeground(Qt.darkRed)
                        ask_item.setText(f"↓ {price_data['ask']:.5f}")
                    self.price_table.setItem(i, 2, ask_item)
                    
                    # Spread with color
                    spread_item = QTableWidgetItem(f"{price_data['spread']:.1f}")
                    if price_data['spread'] > 2.0:  # High spread
                        spread_item.setForeground(Qt.darkRed)
                    elif price_data['spread'] < 1.0:  # Low spread
                        spread_item.setForeground(Qt.darkGreen)
                    self.price_table.setItem(i, 3, spread_item)
                    
                    # Change percentage
                    change_pct = (bid_change / prev_price['bid'] * 100) if prev_price['bid'] != 0 else 0
                    change_item = QTableWidgetItem(f"{change_pct:+.2f}%")
                    if change_pct > 0:
                        change_item.setForeground(Qt.darkGreen)
                    elif change_pct < 0:
                        change_item.setForeground(Qt.darkRed)
                    self.price_table.setItem(i, 4, change_item)
                    
                    # Time
                    self.price_table.setItem(i, 5, QTableWidgetItem(price_data['time']))
                    
                    # Update previous price
                    self.previous_prices[symbol] = {
                        'bid': price_data['bid'],
                        'ask': price_data['ask']
                    }
                    
            # Resize columns to fit content
            self.price_table.resizeColumnsToContents()
            
        except Exception as e:
            print(f"Error updating dashboard: {str(e)}")
        
    def create_settings_tab(self):
        settings = QWidget()
        layout = QVBoxLayout(settings)
        
        # MT5 Settings
        mt5_group = QGroupBox("MetaTrader 5 Settings")
        mt5_layout = QFormLayout()
        
        # Load settings from database
        mt5_settings = self.db.get_setting('mt5_settings', {})
        
        self.account_input = QLineEdit(str(mt5_settings.get('account', '')))
        mt5_layout.addRow("Account:", self.account_input)
        
        self.password_input = QLineEdit(mt5_settings.get('password', ''))
        self.password_input.setEchoMode(QLineEdit.Password)
        mt5_layout.addRow("Password:", self.password_input)
        
        self.server_input = QLineEdit(mt5_settings.get('server', ''))
        mt5_layout.addRow("Server:", self.server_input)
        
        mt5_group.setLayout(mt5_layout)
        layout.addWidget(mt5_group)
        
        # Trading Settings
        trading_group = QGroupBox("Trading Settings")
        trading_layout = QFormLayout()
        
        # Load settings from database
        trading_settings = self.db.get_setting('trading_settings', {})
        
        self.risk_input = QDoubleSpinBox()
        self.risk_input.setRange(0.1, 10.0)
        self.risk_input.setValue(trading_settings.get('risk_percent', 1.0))
        trading_layout.addRow("Risk %:", self.risk_input)
        
        self.signal_strength_input = QSpinBox()
        self.signal_strength_input.setRange(1, 5)
        self.signal_strength_input.setValue(trading_settings.get('min_signal_strength', 3))
        trading_layout.addRow("Min Signal Strength:", self.signal_strength_input)
        
        self.order_type_combo = QComboBox()
        self.order_type_combo.addItems(["MARKET", "LIMIT", "STOP", "STOP_LIMIT"])
        self.order_type_combo.setCurrentText(trading_settings.get('order_type', 'MARKET'))
        trading_layout.addRow("Order Type:", self.order_type_combo)
        
        self.auto_trade_check = QCheckBox()
        self.auto_trade_check.setChecked(trading_settings.get('auto_trade', False))
        trading_layout.addRow("Auto Trade:", self.auto_trade_check)
        
        self.scalping_check = QCheckBox()
        self.scalping_check.setChecked(trading_settings.get('scalping_mode', False))
        trading_layout.addRow("Scalping Mode:", self.scalping_check)
        
        self.quick_close_check = QCheckBox()
        self.quick_close_check.setChecked(trading_settings.get('quick_close', False))
        trading_layout.addRow("Quick Close:", self.quick_close_check)
        
        self.quick_close_target = QDoubleSpinBox()
        self.quick_close_target.setRange(0.1, 100.0)
        self.quick_close_target.setValue(trading_settings.get('quick_close_target', 5.0))
        self.quick_close_target.setSuffix(" pips")
        trading_layout.addRow("Quick Close Target:", self.quick_close_target)
        
        trading_group.setLayout(trading_layout)
        layout.addWidget(trading_group)
        
        # Symbol Settings
        symbol_group = QGroupBox("Symbol Settings")
        symbol_layout = QFormLayout()
        
        # Load settings from database
        symbol_settings = self.db.get_setting('symbol_settings', {})
        
        self.symbols_input = QLineEdit(",".join(symbol_settings.get('symbols', ['EURUSD', 'GBPUSD'])))
        symbol_layout.addRow("Symbols:", self.symbols_input)
        
        self.timeframe_combo = QComboBox()
        self.timeframe_combo.addItems(["M1", "M5", "M15", "M30", "H1", "H4", "D1", "W1"])
        self.timeframe_combo.setCurrentText(symbol_settings.get('timeframe', 'M15'))
        symbol_layout.addRow("Timeframe:", self.timeframe_combo)
        
        symbol_group.setLayout(symbol_layout)
        layout.addWidget(symbol_group)
        
        # Monitoring Settings
        monitor_group = QGroupBox("Monitoring Settings")
        monitor_layout = QFormLayout()
        
        # Load settings from database
        monitoring_settings = self.db.get_setting('monitoring_settings', {})
        
        self.interval_input = QSpinBox()
        self.interval_input.setRange(1, 60)
        self.interval_input.setValue(monitoring_settings.get('interval', 5))
        monitor_layout.addRow("Interval (seconds):", self.interval_input)
        
        self.max_records_input = QSpinBox()
        self.max_records_input.setRange(100, 10000)
        self.max_records_input.setValue(monitoring_settings.get('max_records', 1000))
        monitor_layout.addRow("Max Records:", self.max_records_input)
        
        self.save_data_check = QCheckBox()
        self.save_data_check.setChecked(monitoring_settings.get('save_data', True))
        monitor_layout.addRow("Save Data:", self.save_data_check)
        
        self.data_dir_input = QLineEdit(monitoring_settings.get('data_dir', 'price_data'))
        monitor_layout.addRow("Data Directory:", self.data_dir_input)
        
        monitor_group.setLayout(monitor_layout)
        layout.addWidget(monitor_group)
        
        # Save button
        save_btn = QPushButton("Save Settings")
        save_btn.clicked.connect(self.save_settings)
        layout.addWidget(save_btn)
        
        return settings
        
    def create_pairs_tab(self):
        pairs_tab = QWidget()
        layout = QVBoxLayout()
        
        # Available pairs group
        available_group = QGroupBox("Available Pairs")
        available_layout = QVBoxLayout()
        
        # Get all available symbols from MT5
        self.available_pairs_list = QListWidget()
        symbols = mt5.symbols_get()
        if symbols:
            for symbol in symbols:
                self.available_pairs_list.addItem(symbol.name)
        available_layout.addWidget(self.available_pairs_list)
        
        available_group.setLayout(available_layout)
        layout.addWidget(available_group)
        
        # Selected pairs group
        selected_group = QGroupBox("Selected Pairs")
        selected_layout = QVBoxLayout()
        
        # Load selected pairs from database
        self.selected_pairs_list = QListWidget()
        symbol_settings = self.db.get_setting('symbol_settings', {})
        selected_pairs = symbol_settings.get('symbols', ['EURUSD', 'GBPUSD'])
        for pair in selected_pairs:
            self.selected_pairs_list.addItem(pair)
            
        selected_layout.addWidget(self.selected_pairs_list)
        
        # Add/Remove buttons
        button_layout = QHBoxLayout()
        add_button = QPushButton("Add >>")
        add_button.clicked.connect(self.add_pair)
        remove_button = QPushButton("<< Remove")
        remove_button.clicked.connect(self.remove_pair)
        button_layout.addWidget(add_button)
        button_layout.addWidget(remove_button)
        selected_layout.addLayout(button_layout)
        
        selected_group.setLayout(selected_layout)
        layout.addWidget(selected_group)
        
        # Save button
        save_button = QPushButton("Save Pairs")
        save_button.clicked.connect(self.save_pairs)
        layout.addWidget(save_button)
        
        pairs_tab.setLayout(layout)
        return pairs_tab
        
    def add_pair(self):
        selected_items = self.available_pairs_list.selectedItems()
        for item in selected_items:
            pair = item.text()
            # Check if pair already exists
            if not self.selected_pairs_list.findItems(pair, Qt.MatchExactly):
                self.selected_pairs_list.addItem(pair)
                
    def remove_pair(self):
        selected_items = self.selected_pairs_list.selectedItems()
        for item in selected_items:
            self.selected_pairs_list.takeItem(self.selected_pairs_list.row(item))
            
    def save_pairs(self):
        try:
            # Get all selected pairs
            selected_pairs = []
            for i in range(self.selected_pairs_list.count()):
                selected_pairs.append(self.selected_pairs_list.item(i).text())
                
            # Save to database
            symbol_settings = self.db.get_setting('symbol_settings', {})
            symbol_settings['symbols'] = selected_pairs
            self.db.save_setting('symbol_settings', symbol_settings)
            
            QMessageBox.information(self, "Success", "Pairs saved successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save pairs: {str(e)}")
            
    def create_monitoring_tab(self):
        monitoring = QWidget()
        layout = QVBoxLayout(monitoring)
        
        # Monitoring settings
        monitor_group = QGroupBox("Monitoring Settings")
        monitor_layout = QFormLayout()
        
        # Load settings from database
        monitoring_settings = self.db.get_setting('monitoring_settings', {})
        
        self.interval_input = QSpinBox()
        self.interval_input.setRange(1, 60)
        self.interval_input.setValue(monitoring_settings.get('interval', 5))
        monitor_layout.addRow("Interval (seconds):", self.interval_input)
        
        self.max_records_input = QSpinBox()
        self.max_records_input.setRange(100, 10000)
        self.max_records_input.setValue(monitoring_settings.get('max_records', 1000))
        monitor_layout.addRow("Max Records:", self.max_records_input)
        
        self.save_data_check = QCheckBox()
        self.save_data_check.setChecked(monitoring_settings.get('save_data', True))
        monitor_layout.addRow("Save Data:", self.save_data_check)
        
        self.data_dir_input = QLineEdit(monitoring_settings.get('data_dir', 'price_data'))
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
        
        # Filter controls
        filter_group = QGroupBox("Filter History")
        filter_layout = QHBoxLayout()
        
        # Date range
        date_layout = QHBoxLayout()
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate().addDays(-7))
        date_layout.addWidget(QLabel("From:"))
        date_layout.addWidget(self.start_date)
        
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate())
        date_layout.addWidget(QLabel("To:"))
        date_layout.addWidget(self.end_date)
        
        # Symbol filter
        self.symbol_filter = QComboBox()
        self.symbol_filter.addItem("All Symbols")
        self.symbol_filter.currentTextChanged.connect(self.update_history)
        
        # Type filter
        self.type_filter = QComboBox()
        self.type_filter.addItem("All Types")
        self.type_filter.addItems(["BUY", "SELL"])
        self.type_filter.currentTextChanged.connect(self.update_history)
        
        # Add filters to layout
        filter_layout.addLayout(date_layout)
        filter_layout.addWidget(QLabel("Symbol:"))
        filter_layout.addWidget(self.symbol_filter)
        filter_layout.addWidget(QLabel("Type:"))
        filter_layout.addWidget(self.type_filter)
        
        # Refresh button
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.update_history)
        filter_layout.addWidget(refresh_btn)
        
        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)
        
        # History table
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(8)
        self.history_table.setHorizontalHeaderLabels([
            "Time", "Symbol", "Type", "Volume", "Price", "SL", "TP", "Profit"
        ])
        
        # Enable sorting
        self.history_table.setSortingEnabled(True)
        
        # Set column widths
        self.history_table.setColumnWidth(0, 150)  # Time
        self.history_table.setColumnWidth(1, 100)  # Symbol
        self.history_table.setColumnWidth(2, 80)   # Type
        self.history_table.setColumnWidth(3, 80)   # Volume
        self.history_table.setColumnWidth(4, 100)  # Price
        self.history_table.setColumnWidth(5, 100)  # SL
        self.history_table.setColumnWidth(6, 100)  # TP
        self.history_table.setColumnWidth(7, 100)  # Profit
        
        # Enable alternating row colors
        self.history_table.setAlternatingRowColors(True)
        
        # Enable selection
        self.history_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.history_table.setSelectionMode(QTableWidget.SingleSelection)
        
        layout.addWidget(self.history_table)
        
        # Summary group
        summary_group = QGroupBox("Summary")
        summary_layout = QHBoxLayout()
        
        self.total_trades = QLabel("Total Trades: 0")
        self.winning_trades = QLabel("Winning Trades: 0")
        self.losing_trades = QLabel("Losing Trades: 0")
        self.win_rate = QLabel("Win Rate: 0%")
        self.total_profit = QLabel("Total Profit: 0.00")
        
        summary_layout.addWidget(self.total_trades)
        summary_layout.addWidget(self.winning_trades)
        summary_layout.addWidget(self.losing_trades)
        summary_layout.addWidget(self.win_rate)
        summary_layout.addWidget(self.total_profit)
        
        summary_group.setLayout(summary_layout)
        layout.addWidget(summary_group)
        
        return history
        
    def create_signals_tab(self):
        signals_tab = QWidget()
        layout = QVBoxLayout()
        
        # Signal Settings Group
        signal_group = QGroupBox("Signal Settings")
        signal_layout = QVBoxLayout()
        
        # Create checkboxes for each indicator
        self.sma_crossover_check = QCheckBox("SMA Crossover")
        self.rsi_check = QCheckBox("RSI")
        self.price_action_check = QCheckBox("Price Action")
        self.macd_check = QCheckBox("MACD")
        self.bollinger_check = QCheckBox("Bollinger Bands")
        self.stochastic_check = QCheckBox("Stochastic")
        
        # Add checkboxes to layout
        signal_layout.addWidget(self.sma_crossover_check)
        signal_layout.addWidget(self.rsi_check)
        signal_layout.addWidget(self.price_action_check)
        signal_layout.addWidget(self.macd_check)
        signal_layout.addWidget(self.bollinger_check)
        signal_layout.addWidget(self.stochastic_check)
        
        signal_group.setLayout(signal_layout)
        layout.addWidget(signal_group)
        
        # Signal Weights Group
        weights_group = QGroupBox("Signal Weights")
        weights_layout = QVBoxLayout()
        
        # Create spinboxes for weights
        self.sma_weight = QDoubleSpinBox()
        self.sma_weight.setRange(0.1, 5.0)
        self.sma_weight.setSingleStep(0.1)
        self.sma_weight.setValue(2.0)
        
        self.rsi_weight = QDoubleSpinBox()
        self.rsi_weight.setRange(0.1, 5.0)
        self.rsi_weight.setSingleStep(0.1)
        self.rsi_weight.setValue(2.0)
        
        self.price_action_weight = QDoubleSpinBox()
        self.price_action_weight.setRange(0.1, 5.0)
        self.price_action_weight.setSingleStep(0.1)
        self.price_action_weight.setValue(1.0)
        
        self.macd_weight = QDoubleSpinBox()
        self.macd_weight.setRange(0.1, 5.0)
        self.macd_weight.setSingleStep(0.1)
        self.macd_weight.setValue(2.0)
        
        self.bollinger_weight = QDoubleSpinBox()
        self.bollinger_weight.setRange(0.1, 5.0)
        self.bollinger_weight.setSingleStep(0.1)
        self.bollinger_weight.setValue(2.0)
        
        self.stochastic_weight = QDoubleSpinBox()
        self.stochastic_weight.setRange(0.1, 5.0)
        self.stochastic_weight.setSingleStep(0.1)
        self.stochastic_weight.setValue(2.0)
        
        # Add weight controls to layout
        weights_layout.addWidget(QLabel("SMA Weight:"))
        weights_layout.addWidget(self.sma_weight)
        weights_layout.addWidget(QLabel("RSI Weight:"))
        weights_layout.addWidget(self.rsi_weight)
        weights_layout.addWidget(QLabel("Price Action Weight:"))
        weights_layout.addWidget(self.price_action_weight)
        weights_layout.addWidget(QLabel("MACD Weight:"))
        weights_layout.addWidget(self.macd_weight)
        weights_layout.addWidget(QLabel("Bollinger Weight:"))
        weights_layout.addWidget(self.bollinger_weight)
        weights_layout.addWidget(QLabel("Stochastic Weight:"))
        weights_layout.addWidget(self.stochastic_weight)
        
        weights_group.setLayout(weights_layout)
        layout.addWidget(weights_group)
        
        # Add save button
        save_button = QPushButton("Save Signal Settings")
        save_button.clicked.connect(self.save_signal_settings)
        layout.addWidget(save_button)
        
        signals_tab.setLayout(layout)
        return signals_tab
        
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
        """Setup timers for updates"""
        # Dashboard update timer
        self.dashboard_timer = QTimer()
        self.dashboard_timer.timeout.connect(self.update_dashboard)
        self.dashboard_timer.start(1000)  # Update every second
        
        # Monitoring update timer
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self.update_monitoring)
        self.monitor_timer.start(5000)  # Update every 5 seconds
        
        # History update timer
        self.history_timer = QTimer()
        self.history_timer.timeout.connect(self.update_history)
        self.history_timer.start(10000)  # Update every 10 seconds
        
    def update_monitoring(self):
        """Update monitoring tab with real-time data"""
        try:
            # Get current positions
            positions = mt5.positions_get()
            if positions is None:
                positions = []
                
            # Get pending orders
            orders = mt5.orders_get()
            if orders is None:
                orders = []
                
            # Update log display
            current_time = datetime.now().strftime("%H:%M:%S")
            log_text = f"\n=== Update {current_time} ===\n"
            
            # Add positions info
            if positions:
                log_text += "\nOpen Positions:\n"
                for pos in positions:
                    log_text += f"{pos.symbol} {pos.type} {pos.volume} @ {pos.price_open} (Profit: {pos.profit})\n"
            else:
                log_text += "\nNo open positions\n"
                
            # Add orders info
            if orders:
                log_text += "\nPending Orders:\n"
                for order in orders:
                    log_text += f"{order.symbol} {order.type} {order.volume} @ {order.price_open}\n"
            else:
                log_text += "\nNo pending orders\n"
                
            # Add price info for monitored symbols
            symbols = self.symbols_input.text().split(",")
            log_text += "\nCurrent Prices:\n"
            for symbol in symbols:
                symbol = symbol.strip()
                price_data = get_symbol_price(symbol)
                if price_data:
                    log_text += f"{symbol}: Bid={price_data['bid']} Ask={price_data['ask']} Spread={price_data['spread']}\n"
                    
            # Add trading signals and execute auto-trading
            log_text += "\nTrading Signals:\n"
            for symbol in symbols:
                symbol = symbol.strip()
                # Get settings from database
                trading_settings = self.db.get_setting('trading_settings', {})
                min_signal_strength = trading_settings.get('min_signal_strength', 3)
                scalping_mode = trading_settings.get('scalping_mode', False)
                auto_trade = trading_settings.get('auto_trade', False)
                risk_percent = trading_settings.get('risk_percent', 1.0)
                
                # Get timeframe based on scalping mode
                timeframe = mt5.TIMEFRAME_M1 if scalping_mode else mt5.TIMEFRAME_M15
                
                # Get price history
                rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, 100)
                if rates is not None:
                    df = pd.DataFrame(rates)
                    
                    # Calculate indicators
                    df['SMA20'] = df['close'].rolling(window=20).mean()
                    df['SMA50'] = df['close'].rolling(window=50).mean()
                    df['RSI'] = self.calculate_rsi(df['close'])
                    
                    # Get latest values
                    latest = df.iloc[-1]
                    prev = df.iloc[-2]
                    
                    # Generate signals
                    signals = []
                    signal_strength = 0
                    
                    # SMA Crossover
                    if latest['SMA20'] > latest['SMA50'] and prev['SMA20'] <= prev['SMA50']:
                        signals.append("SMA Crossover: BUY")
                        signal_strength += 2
                    elif latest['SMA20'] < latest['SMA50'] and prev['SMA20'] >= prev['SMA50']:
                        signals.append("SMA Crossover: SELL")
                        signal_strength += 2
                        
                    # RSI Signals
                    if latest['RSI'] < 30:
                        signals.append("RSI Oversold: BUY")
                        signal_strength += 2
                    elif latest['RSI'] > 70:
                        signals.append("RSI Overbought: SELL")
                        signal_strength += 2
                        
                    # Price Action
                    if latest['close'] > latest['SMA20'] and latest['close'] > latest['SMA50']:
                        signals.append("Price Above SMAs: BULLISH")
                        signal_strength += 1
                    elif latest['close'] < latest['SMA20'] and latest['close'] < latest['SMA50']:
                        signals.append("Price Below SMAs: BEARISH")
                        signal_strength += 1
                        
                    # Add signals to log
                    if signals:
                        log_text += f"\n{symbol} Signals:\n"
                        for signal in signals:
                            log_text += f"- {signal}\n"
                        log_text += f"RSI: {latest['RSI']:.2f}\n"
                        log_text += f"SMA20: {latest['SMA20']:.5f}\n"
                        log_text += f"SMA50: {latest['SMA50']:.5f}\n"
                        log_text += f"Signal Strength: {signal_strength}\n"
                        
                        # Execute auto-trading if enabled and signal strength is sufficient
                        if auto_trade and signal_strength >= min_signal_strength:
                            # Calculate position size based on risk
                            account_info = mt5.account_info()
                            if account_info:
                                balance = account_info.balance
                                risk_amount = balance * (risk_percent / 100)
                                
                                # Get current price
                                symbol_info = mt5.symbol_info(symbol)
                                if symbol_info:
                                    point = symbol_info.point
                                    price = symbol_info.ask if "BUY" in signals else symbol_info.bid
                                    
                                    # Calculate stop loss (50 pips for example)
                                    stop_loss = 50 * point
                                    
                                    # Calculate position size
                                    position_size = risk_amount / stop_loss
                                    
                                    # Execute trade
                                    if "BUY" in signals:
                                        self.execute_trade(symbol, mt5.ORDER_TYPE_BUY, position_size, price, stop_loss)
                                    elif "SELL" in signals:
                                        self.execute_trade(symbol, mt5.ORDER_TYPE_SELL, position_size, price, stop_loss)
                    else:
                        log_text += f"\n{symbol}: No strong signals\n"
                        
            # Update log display
            self.log_display.append(log_text)
            
            # Auto-scroll to bottom
            self.log_display.verticalScrollBar().setValue(
                self.log_display.verticalScrollBar().maximum()
            )
            
        except Exception as e:
            print(f"Error updating monitoring: {str(e)}")
            
    def calculate_rsi(self, prices, period=14):
        """Calculate RSI indicator"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
            
    def update_history(self):
        """Update history table with filtered data"""
        try:
            # Get date range
            start_date = self.start_date.date().toPyDate()
            end_date = self.end_date.date().toPyDate()
            
            # Get filters
            symbol_filter = self.symbol_filter.currentText()
            type_filter = self.type_filter.currentText()
            
            # Get deals from MT5
            deals = mt5.history_deals_get(start_date, end_date)
            if deals is None:
                return
                
            # Clear existing table
            self.history_table.setRowCount(0)
            
            # Update symbol filter
            symbols = set()
            for deal in deals:
                symbols.add(deal.symbol)
            current_symbol = self.symbol_filter.currentText()
            self.symbol_filter.clear()
            self.symbol_filter.addItem("All Symbols")
            self.symbol_filter.addItems(sorted(symbols))
            if current_symbol in symbols:
                self.symbol_filter.setCurrentText(current_symbol)
            
            # Filter and add deals to table
            total_trades = 0
            winning_trades = 0
            losing_trades = 0
            total_profit = 0.0
            
            for deal in deals:
                # Apply filters
                if symbol_filter != "All Symbols" and deal.symbol != symbol_filter:
                    continue
                if type_filter != "All Types" and deal.type != (mt5.DEAL_TYPE_BUY if type_filter == "BUY" else mt5.DEAL_TYPE_SELL):
                    continue
                    
                row = self.history_table.rowCount()
                self.history_table.insertRow(row)
                
                # Convert time
                deal_time = datetime.fromtimestamp(deal.time)
                
                # Add items to table
                self.history_table.setItem(row, 0, QTableWidgetItem(deal_time.strftime("%Y-%m-%d %H:%M:%S")))
                self.history_table.setItem(row, 1, QTableWidgetItem(deal.symbol))
                self.history_table.setItem(row, 2, QTableWidgetItem("BUY" if deal.type == mt5.DEAL_TYPE_BUY else "SELL"))
                self.history_table.setItem(row, 3, QTableWidgetItem(str(deal.volume)))
                self.history_table.setItem(row, 4, QTableWidgetItem(str(deal.price)))
                self.history_table.setItem(row, 5, QTableWidgetItem(str(deal.sl)))
                self.history_table.setItem(row, 6, QTableWidgetItem(str(deal.tp)))
                self.history_table.setItem(row, 7, QTableWidgetItem(str(deal.profit)))
                
                # Update summary
                total_trades += 1
                if deal.profit > 0:
                    winning_trades += 1
                else:
                    losing_trades += 1
                total_profit += deal.profit
                
            # Update summary labels
            self.total_trades.setText(f"Total Trades: {total_trades}")
            self.winning_trades.setText(f"Winning Trades: {winning_trades}")
            self.losing_trades.setText(f"Losing Trades: {losing_trades}")
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            self.win_rate.setText(f"Win Rate: {win_rate:.1f}%")
            self.total_profit.setText(f"Total Profit: {total_profit:.2f}")
            
            # Sort by time (newest first)
            self.history_table.sortItems(0, Qt.DescendingOrder)
            
        except Exception as e:
            print(f"Error updating history: {str(e)}")
            
    def start_monitoring(self):
        """Start monitoring process"""
        try:
            # Get settings from database
            monitoring_settings = self.db.get_setting('monitoring_settings', {})
            interval = monitoring_settings.get('interval', 5)
            max_records = monitoring_settings.get('max_records', 1000)
            save_data = monitoring_settings.get('save_data', True)
            data_dir = monitoring_settings.get('data_dir', 'price_data')
            
            # Start monitoring
            self.monitor_timer.start(interval * 1000)  # Convert to milliseconds
            self.start_monitoring_btn.setEnabled(False)
            self.stop_monitoring_btn.setEnabled(True)
            
            # Show status
            self.log_display.append(f"Monitoring started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            self.log_display.append(f"Interval: {interval} seconds")
            self.log_display.append(f"Max records: {max_records}")
            self.log_display.append(f"Save data: {'Yes' if save_data else 'No'}")
            self.log_display.append(f"Data directory: {data_dir}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to start monitoring: {str(e)}")
            
    def stop_monitoring(self):
        """Stop monitoring process"""
        try:
            self.monitor_timer.stop()
            self.start_monitoring_btn.setEnabled(True)
            self.stop_monitoring_btn.setEnabled(False)
            self.log_display.append(f"Monitoring stopped at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to stop monitoring: {str(e)}")
            
    def show_chart(self):
        try:
            # Get selected pairs
            selected_pairs = []
            for i in range(self.selected_pairs_list.count()):
                selected_pairs.append(self.selected_pairs_list.item(i).text())
                
            if not selected_pairs:
                QMessageBox.warning(self, "Warning", "Please select at least one pair first")
                return
                
            # Create dialog to select pair
            dialog = QDialog(self)
            dialog.setWindowTitle("Select Pair")
            layout = QVBoxLayout()
            
            # Create combo box for pairs
            pair_combo = QComboBox()
            pair_combo.addItems(selected_pairs)
            layout.addWidget(QLabel("Select Pair:"))
            layout.addWidget(pair_combo)
            
            # Create combo box for timeframe
            timeframe_combo = QComboBox()
            timeframe_combo.addItems(["M1", "M5", "M15", "M30", "H1", "H4", "D1", "W1"])
            timeframe_combo.setCurrentText("M15")
            layout.addWidget(QLabel("Select Timeframe:"))
            layout.addWidget(timeframe_combo)
            
            # Add buttons
            button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            button_box.accepted.connect(dialog.accept)
            button_box.rejected.connect(dialog.reject)
            layout.addWidget(button_box)
            
            dialog.setLayout(layout)
            
            if dialog.exec_() == QDialog.Accepted:
                selected_pair = pair_combo.currentText()
                selected_timeframe = timeframe_combo.currentText()
                
                # Map timeframe to MT5 constant
                timeframe_map = {
                    "M1": mt5.TIMEFRAME_M1,
                    "M5": mt5.TIMEFRAME_M5,
                    "M15": mt5.TIMEFRAME_M15,
                    "M30": mt5.TIMEFRAME_M30,
                    "H1": mt5.TIMEFRAME_H1,
                    "H4": mt5.TIMEFRAME_H4,
                    "D1": mt5.TIMEFRAME_D1,
                    "W1": mt5.TIMEFRAME_W1
                }
                
                self.chart_window = show_chart_window(
                    selected_pair,
                    timeframe_map[selected_timeframe]
                )
                self.chart_window.show()
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to show chart: {str(e)}")
            
    def save_settings(self):
        """Save all settings to database"""
        try:
            # Save MT5 settings
            mt5_settings = {
                'account': self.account_input.text(),
                'password': self.password_input.text(),
                'server': self.server_input.text()
            }
            self.db.save_setting('mt5_settings', mt5_settings)
            
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
            self.db.save_setting('trading_settings', trading_settings)
            
            # Save symbol settings
            symbol_settings = {
                'symbols': [s.strip() for s in self.symbols_input.text().split(',')],
                'timeframe': self.timeframe_combo.currentText()
            }
            self.db.save_setting('symbol_settings', symbol_settings)
            
            # Save monitoring settings
            monitoring_settings = {
                'interval': self.interval_input.value(),
                'max_records': self.max_records_input.value(),
                'save_data': self.save_data_check.isChecked(),
                'data_dir': self.data_dir_input.text()
            }
            self.db.save_setting('monitoring_settings', monitoring_settings)
            
            QMessageBox.information(self, "Success", "Settings saved successfully")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save settings: {str(e)}")
            
    def load_settings(self):
        """Load settings from database"""
        try:
            # Load MT5 settings
            mt5_settings = self.db.get_setting('mt5_settings', {})
            self.account_input.setText(mt5_settings.get('account', ''))
            self.password_input.setText(mt5_settings.get('password', ''))
            self.server_input.setText(mt5_settings.get('server', ''))
            
            # Load trading settings
            trading_settings = self.db.get_setting('trading_settings', {})
            self.risk_input.setValue(trading_settings.get('risk_percent', 1.0))
            self.signal_strength_input.setValue(trading_settings.get('min_signal_strength', 3))
            self.order_type_combo.setCurrentText(trading_settings.get('order_type', 'MARKET'))
            self.auto_trade_check.setChecked(trading_settings.get('auto_trade', False))
            self.scalping_check.setChecked(trading_settings.get('scalping_mode', False))
            self.quick_close_check.setChecked(trading_settings.get('quick_close', False))
            self.quick_close_target.setValue(trading_settings.get('quick_close_target', 5.0))
            
            # Load symbol settings
            symbol_settings = self.db.get_setting('symbol_settings', {})
            self.symbols_input.setText(','.join(symbol_settings.get('symbols', ['EURUSD'])))
            self.timeframe_combo.setCurrentText(symbol_settings.get('timeframe', 'M15'))
            
            # Load monitoring settings
            monitoring_settings = self.db.get_setting('monitoring_settings', {})
            self.interval_input.setValue(monitoring_settings.get('interval', 5))
            self.max_records_input.setValue(monitoring_settings.get('max_records', 1000))
            self.save_data_check.setChecked(monitoring_settings.get('save_data', True))
            self.data_dir_input.setText(monitoring_settings.get('data_dir', 'price_data'))
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load settings: {str(e)}")
        
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
            
    def execute_trade(self, symbol, order_type, volume, price, stop_loss):
        """Execute a trade with proper position sizing"""
        try:
            # Prepare the trade request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": volume,
                "type": order_type,
                "price": price,
                "sl": price - stop_loss if order_type == mt5.ORDER_TYPE_BUY else price + stop_loss,
                "tp": price + (stop_loss * 2) if order_type == mt5.ORDER_TYPE_BUY else price - (stop_loss * 2),
                "deviation": 20,
                "magic": 234000,
                "comment": "Auto-trade",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            # Send the trade request
            result = mt5.order_send(request)
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                print(f"Trade failed: {result.comment}")
            else:
                print(f"Trade executed: {symbol} {order_type} {volume} @ {price}")
                
        except Exception as e:
            print(f"Error executing trade: {str(e)}")
            
    def save_signal_settings(self):
        try:
            signal_settings = {
                'sma_crossover': self.sma_crossover_check.isChecked(),
                'rsi': self.rsi_check.isChecked(),
                'price_action': self.price_action_check.isChecked(),
                'macd': self.macd_check.isChecked(),
                'bollinger': self.bollinger_check.isChecked(),
                'stochastic': self.stochastic_check.isChecked(),
                'sma_weight': self.sma_weight.value(),
                'rsi_weight': self.rsi_weight.value(),
                'price_action_weight': self.price_action_weight.value(),
                'macd_weight': self.macd_weight.value(),
                'bollinger_weight': self.bollinger_weight.value(),
                'stochastic_weight': self.stochastic_weight.value()
            }
            
            self.db.save_setting('signal_settings', signal_settings)
            QMessageBox.information(self, "Success", "Signal settings saved successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save signal settings: {str(e)}")
            
    def closeEvent(self, event):
        self.db.close()
        shutdown_mt5()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TradingGUI()
    window.show()
    sys.exit(app.exec_()) 
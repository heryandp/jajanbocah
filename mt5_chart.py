import matplotlib.pyplot as plt
import mplfinance as mpf
import pandas as pd
import numpy as np
import MetaTrader5 as mt5
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QComboBox, 
                             QCheckBox, QFrame, QSizePolicy, QMessageBox)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont, QColor
import sys
from datetime import datetime, timedelta
from mt5_monitor import get_price_history, calculate_indicators, get_trade_signal

def create_chart_figure(symbol, timeframe=mt5.TIMEFRAME_M15, bars=100):
    """
    Create a matplotlib figure with price chart and indicators
    
    Args:
        symbol (str): Symbol to chart
        timeframe (int): MT5 timeframe constant
        bars (int): Number of bars to retrieve
        
    Returns:
        tuple: (fig, signal) - matplotlib figure and trading signal
    """
    # Get price history
    df = get_price_history(symbol, timeframe=timeframe, bars=bars)
    if df is None or df.empty:
        print(f"No data available for {symbol} on {timeframe_to_str(timeframe)} timeframe")
        fig = plt.figure(figsize=(12, 9))
        plt.text(0.5, 0.5, f"No data available for {symbol}\nCheck if the symbol exists in your MT5 terminal", 
                 horizontalalignment='center', verticalalignment='center', transform=plt.gca().transAxes)
        return fig, None
    
    # Calculate indicators
    try:
        indicators_df = calculate_indicators(df)
        
        # Get trading signal
        signal = get_trade_signal(indicators_df)
    except Exception as e:
        print(f"Error calculating indicators: {e}")
        fig = plt.figure(figsize=(12, 9))
        plt.text(0.5, 0.5, f"Error calculating indicators for {symbol}: {str(e)}", 
                 horizontalalignment='center', verticalalignment='center', transform=plt.gca().transAxes)
        return fig, None
    
    # Create the figure
    fig = plt.figure(figsize=(12, 9))
    
    # Set up the grid
    grid = plt.GridSpec(5, 1, height_ratios=[4, 1, 1, 1, 1])
    
    # Create the main price chart
    ax1 = plt.subplot(grid[0])
    
    # Convert to OHLC format for mplfinance
    ohlc = indicators_df[['time', 'open', 'high', 'low', 'close', 'volume']].copy()
    ohlc.set_index('time', inplace=True)
    
    # Add moving averages to be plotted
    ma_styles = [
        mpf.make_addplot(indicators_df['sma_5'], color='blue', width=0.7, ax=ax1),
        mpf.make_addplot(indicators_df['sma_20'], color='red', width=0.7, ax=ax1),
        mpf.make_addplot(indicators_df['sma_50'], color='green', width=0.7, ax=ax1),
        mpf.make_addplot(indicators_df['bb_upper'], color='gray', alpha=0.3, ax=ax1),
        mpf.make_addplot(indicators_df['bb_lower'], color='gray', alpha=0.3, ax=ax1),
        mpf.make_addplot(indicators_df['bb_middle'], color='purple', alpha=0.5, ax=ax1),
    ]
    
    # Plot the candlestick chart
    mpf.plot(ohlc, type='candle', style='yahoo', ax=ax1, volume=False, addplot=ma_styles, warn_too_much_data=len(ohlc)+100)
    
    # Add legend to main chart
    ax1.legend(['SMA 5', 'SMA 20', 'SMA 50', 'BB Upper', 'BB Lower', 'BB Middle'])
    
    # Set title
    current_price = indicators_df['close'].iloc[-1]
    current_time = indicators_df['time'].iloc[-1]
    
    # Format signal for title
    signal_text = f"{signal['signal']} (Strength: {signal['strength']})"
    
    title = f'{symbol} - {timeframe_to_str(timeframe)} - Price: {current_price:.5f}\n'
    title += f'Signal: {signal_text} - {current_time}'
    ax1.set_title(title)
    
    # Plot RSI
    ax2 = plt.subplot(grid[1], sharex=ax1)
    ax2.plot(indicators_df['time'], indicators_df['rsi_14'], color='purple')
    ax2.axhline(y=70, color='r', linestyle='--', alpha=0.3)
    ax2.axhline(y=30, color='g', linestyle='--', alpha=0.3)
    ax2.set_ylabel('RSI (14)')
    ax2.grid(True, alpha=0.3)
    
    # Plot Stochastic
    ax3 = plt.subplot(grid[2], sharex=ax1)
    ax3.plot(indicators_df['time'], indicators_df['stoch_k'], color='blue', label='%K')
    ax3.plot(indicators_df['time'], indicators_df['stoch_d'], color='red', label='%D')
    ax3.axhline(y=80, color='r', linestyle='--', alpha=0.3)
    ax3.axhline(y=20, color='g', linestyle='--', alpha=0.3)
    ax3.set_ylabel('Stochastic')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # Plot MACD
    ax4 = plt.subplot(grid[3], sharex=ax1)
    ax4.plot(indicators_df['time'], indicators_df['macd'], color='blue', label='MACD')
    ax4.plot(indicators_df['time'], indicators_df['signal'], color='red', label='Signal')
    # Add histogram
    positive = indicators_df['histogram'] > 0
    negative = indicators_df['histogram'] <= 0
    ax4.bar(indicators_df.loc[positive, 'time'], indicators_df.loc[positive, 'histogram'], color='green', alpha=0.5, width=0.0005)
    ax4.bar(indicators_df.loc[negative, 'time'], indicators_df.loc[negative, 'histogram'], color='red', alpha=0.5, width=0.0005)
    ax4.set_ylabel('MACD')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    # Plot Volume
    ax5 = plt.subplot(grid[4], sharex=ax1)
    ax5.bar(indicators_df['time'], indicators_df['volume'], color='blue', alpha=0.5)
    ax5.set_ylabel('Volume')
    ax5.grid(True, alpha=0.3)
    
    # Layout adjustment
    plt.tight_layout()
    
    return fig, signal

def timeframe_to_str(timeframe):
    """Convert MT5 timeframe constant to string"""
    timeframes = {
        mt5.TIMEFRAME_M1: "M1",
        mt5.TIMEFRAME_M2: "M2",
        mt5.TIMEFRAME_M3: "M3", 
        mt5.TIMEFRAME_M4: "M4",
        mt5.TIMEFRAME_M5: "M5",
        mt5.TIMEFRAME_M6: "M6",
        mt5.TIMEFRAME_M10: "M10",
        mt5.TIMEFRAME_M12: "M12",
        mt5.TIMEFRAME_M15: "M15",
        mt5.TIMEFRAME_M20: "M20",
        mt5.TIMEFRAME_M30: "M30",
        mt5.TIMEFRAME_H1: "H1",
        mt5.TIMEFRAME_H2: "H2",
        mt5.TIMEFRAME_H3: "H3",
        mt5.TIMEFRAME_H4: "H4",
        mt5.TIMEFRAME_H6: "H6",
        mt5.TIMEFRAME_H8: "H8",
        mt5.TIMEFRAME_H12: "H12",
        mt5.TIMEFRAME_D1: "D1",
        mt5.TIMEFRAME_W1: "W1",
        mt5.TIMEFRAME_MN1: "MN1"
    }
    return timeframes.get(timeframe, str(timeframe))

class ChartWindow(QMainWindow):
    def __init__(self, symbol, timeframe=mt5.TIMEFRAME_M15, auto_refresh=True, refresh_interval=10):
        super().__init__()
        
        self.symbol = symbol
        self.timeframe = timeframe
        self.auto_refresh = auto_refresh
        self.refresh_interval = refresh_interval  # in seconds
        self.signal = None
        
        self.init_ui()
        self.update_chart()
        
        # Set up auto-refresh timer
        if self.auto_refresh:
            self.timer = QTimer(self)
            self.timer.timeout.connect(self.update_chart)
            self.timer.start(self.refresh_interval * 1000)
    
    def init_ui(self):
        # Set window properties
        self.setWindowTitle(f"MT5 Chart - {self.symbol} - {timeframe_to_str(self.timeframe)}")
        self.setGeometry(100, 100, 1200, 900)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Create chart frame
        self.chart_frame = QWidget()
        self.chart_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        chart_layout = QVBoxLayout(self.chart_frame)
        self.chart_layout = chart_layout
        
        # Create control panel
        control_panel = QFrame()
        control_panel.setFrameShape(QFrame.StyledPanel)
        control_panel.setMaximumHeight(50)
        control_layout = QHBoxLayout(control_panel)
        
        # Create signal label
        self.signal_label = QLabel("Signal: Calculating...")
        self.signal_label.setFont(QFont("Arial", 10))
        control_layout.addWidget(self.signal_label)
        
        # Create timeframe selection
        control_layout.addWidget(QLabel("Timeframe:"))
        self.timeframe_combo = QComboBox()
        self.timeframe_combo.addItems(["M1", "M5", "M15", "M30", "H1", "H4", "D1", "W1"])
        self.timeframe_combo.setCurrentText(timeframe_to_str(self.timeframe))
        self.timeframe_combo.currentTextChanged.connect(self.on_timeframe_changed)
        control_layout.addWidget(self.timeframe_combo)
        
        # Create refresh button
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.update_chart)
        control_layout.addWidget(refresh_btn)
        
        # Create auto-refresh checkbox
        self.auto_refresh_check = QCheckBox("Auto-refresh")
        self.auto_refresh_check.setChecked(self.auto_refresh)
        self.auto_refresh_check.stateChanged.connect(self.toggle_auto_refresh)
        control_layout.addWidget(self.auto_refresh_check)
        
        # Add spacer
        control_layout.addStretch(1)
        
        # Create order panel
        order_panel = QFrame()
        order_panel.setFrameShape(QFrame.StyledPanel)
        order_panel.setMaximumHeight(70)
        order_layout = QHBoxLayout(order_panel)
        
        # Create order buttons
        buy_btn = QPushButton("BUY MARKET")
        buy_btn.setStyleSheet("background-color: green; color: white;")
        buy_btn.setMinimumHeight(40)
        buy_btn.clicked.connect(self.on_buy_market)
        order_layout.addWidget(buy_btn)
        
        sell_btn = QPushButton("SELL MARKET")
        sell_btn.setStyleSheet("background-color: red; color: white;")
        sell_btn.setMinimumHeight(40)
        sell_btn.clicked.connect(self.on_sell_market)
        order_layout.addWidget(sell_btn)
        
        buy_limit_btn = QPushButton("BUY LIMIT")
        buy_limit_btn.setStyleSheet("background-color: darkgreen; color: white;")
        buy_limit_btn.setMinimumHeight(40)
        buy_limit_btn.clicked.connect(self.on_buy_limit)
        order_layout.addWidget(buy_limit_btn)
        
        sell_limit_btn = QPushButton("SELL LIMIT")
        sell_limit_btn.setStyleSheet("background-color: darkred; color: white;")
        sell_limit_btn.setMinimumHeight(40)
        sell_limit_btn.clicked.connect(self.on_sell_limit)
        order_layout.addWidget(sell_limit_btn)
        
        # Add frames to main layout
        main_layout.addWidget(self.chart_frame)
        main_layout.addWidget(control_panel)
        main_layout.addWidget(order_panel)
    
    def update_chart(self):
        # Clear previous chart
        for i in reversed(range(self.chart_layout.count())): 
            self.chart_layout.itemAt(i).widget().setParent(None)
        
        # Get current timeframe from the combobox
        tf_str = self.timeframe_combo.currentText()
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
        self.timeframe = tf_map.get(tf_str, self.timeframe)
        
        # Create new chart figure
        fig, signal = create_chart_figure(self.symbol, self.timeframe)
        
        if fig:
            # Store the signal
            self.signal = signal
            
            # Update signal label
            if signal:
                signal_text = f"Signal: {signal['signal']} (Strength: {signal['strength']})"
                if signal["reason"]:
                    signal_text += f" - {', '.join(signal['reason'])}"
                self.signal_label.setText(signal_text)
            
            # Create canvas
            canvas = FigureCanvas(fig)
            toolbar = NavigationToolbar(canvas, self)
            
            # Add to layout
            self.chart_layout.addWidget(toolbar)
            self.chart_layout.addWidget(canvas)
            
            # Update window title
            self.setWindowTitle(f"MT5 Chart - {self.symbol} - {timeframe_to_str(self.timeframe)}")
    
    def on_timeframe_changed(self, text):
        self.update_chart()
    
    def toggle_auto_refresh(self, state):
        self.auto_refresh = (state == Qt.Checked)
        
        if hasattr(self, 'timer'):
            if self.auto_refresh:
                self.timer.start(self.refresh_interval * 1000)
            else:
                self.timer.stop()
    
    def show_message(self, title, message, icon=None):
        """Show a message box to the user"""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        
        if icon == "error":
            msg_box.setIcon(QMessageBox.Critical)
        elif icon == "warning":
            msg_box.setIcon(QMessageBox.Warning)
        elif icon == "info":
            msg_box.setIcon(QMessageBox.Information)
        
        msg_box.exec_()

    def on_buy_market(self):
        from mt5_monitor import place_order_from_signal
        if self.signal and "order_params" in self.signal:
            # Override the signal type to BUY
            self.signal["signal"] = "BUY"
            self.signal["order_params"]["entry_type"] = "BUY"
            
            # Show a confirmation dialog
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Confirm Order")
            current_price = self.signal["order_params"]["entry_price"]
            sl = self.signal["order_params"]["stop_loss"]
            tp = self.signal["order_params"]["take_profit"]
            
            # Calculate pip risk
            risk_pips = abs(current_price - sl)
            reward_pips = abs(tp - current_price)
            
            msg_box.setText(f"Place BUY MARKET order for {self.symbol}?")
            msg_box.setInformativeText(
                f"Entry Price: {current_price:.5f}\n"
                f"Stop Loss: {sl:.5f} ({risk_pips:.1f} pips)\n"
                f"Take Profit: {tp:.5f} ({reward_pips:.1f} pips)\n"
                f"Risk/Reward: 1:{(reward_pips/risk_pips if risk_pips else 0):.2f}"
            )
            msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msg_box.setDefaultButton(QMessageBox.No)
            
            if msg_box.exec_() == QMessageBox.Yes:
                # Place the order
                result = place_order_from_signal(
                    symbol=self.symbol,
                    signal=self.signal,
                    risk_percent=1.0,
                    order_type="MARKET"
                )
                
                if result:
                    self.show_message("Order Placed", f"BUY MARKET order placed successfully.\nOrder ID: {result['order']}", "info")
                else:
                    self.show_message("Order Failed", "Failed to place order. Check terminal output for details.", "error")
        else:
            self.show_message("Cannot Place Order", "No valid signal available. Try refreshing the chart.", "warning")
    
    def on_sell_market(self):
        from mt5_monitor import place_order_from_signal
        if self.signal and "order_params" in self.signal:
            # Override the signal type to SELL
            self.signal["signal"] = "SELL"
            self.signal["order_params"]["entry_type"] = "SELL"
            
            # Show a confirmation dialog
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Confirm Order")
            current_price = self.signal["order_params"]["entry_price"]
            sl = self.signal["order_params"]["stop_loss"]
            tp = self.signal["order_params"]["take_profit"]
            
            # Calculate pip risk
            risk_pips = abs(current_price - sl)
            reward_pips = abs(tp - current_price)
            
            msg_box.setText(f"Place SELL MARKET order for {self.symbol}?")
            msg_box.setInformativeText(
                f"Entry Price: {current_price:.5f}\n"
                f"Stop Loss: {sl:.5f} ({risk_pips:.1f} pips)\n"
                f"Take Profit: {tp:.5f} ({reward_pips:.1f} pips)\n"
                f"Risk/Reward: 1:{(reward_pips/risk_pips if risk_pips else 0):.2f}"
            )
            msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msg_box.setDefaultButton(QMessageBox.No)
            
            if msg_box.exec_() == QMessageBox.Yes:
                # Place the order
                result = place_order_from_signal(
                    symbol=self.symbol,
                    signal=self.signal,
                    risk_percent=1.0,
                    order_type="MARKET"
                )
                
                if result:
                    self.show_message("Order Placed", f"SELL MARKET order placed successfully.\nOrder ID: {result['order']}", "info")
                else:
                    self.show_message("Order Failed", "Failed to place order. Check terminal output for details.", "error")
        else:
            self.show_message("Cannot Place Order", "No valid signal available. Try refreshing the chart.", "warning")
    
    def on_buy_limit(self):
        from mt5_monitor import place_order_from_signal
        if self.signal and "order_params" in self.signal:
            # Override the signal type to BUY
            self.signal["signal"] = "BUY"
            self.signal["order_params"]["entry_type"] = "BUY"
            
            # Get buy limit price
            limit_price = self.signal["order_params"]["buy_limit_price"]
            
            # Show a confirmation dialog
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Confirm Order")
            current_price = self.signal["order_params"]["entry_price"]
            sl = self.signal["order_params"]["stop_loss"]
            tp = self.signal["order_params"]["take_profit"]
            
            msg_box.setText(f"Place BUY LIMIT order for {self.symbol}?")
            msg_box.setInformativeText(
                f"Current Price: {current_price:.5f}\n"
                f"Limit Price: {limit_price:.5f}\n"
                f"Stop Loss: {sl:.5f}\n"
                f"Take Profit: {tp:.5f}"
            )
            msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msg_box.setDefaultButton(QMessageBox.No)
            
            if msg_box.exec_() == QMessageBox.Yes:
                # Place the order
                result = place_order_from_signal(
                    symbol=self.symbol,
                    signal=self.signal,
                    risk_percent=1.0,
                    order_type="LIMIT"
                )
                
                if result:
                    self.show_message("Order Placed", f"BUY LIMIT order placed successfully.\nOrder ID: {result['order']}", "info")
                else:
                    self.show_message("Order Failed", "Failed to place order. Check terminal output for details.", "error")
        else:
            self.show_message("Cannot Place Order", "No valid signal available. Try refreshing the chart.", "warning")
    
    def on_sell_limit(self):
        from mt5_monitor import place_order_from_signal
        if self.signal and "order_params" in self.signal:
            # Override the signal type to SELL
            self.signal["signal"] = "SELL"
            self.signal["order_params"]["entry_type"] = "SELL"
            
            # Get sell limit price
            limit_price = self.signal["order_params"]["sell_limit_price"]
            
            # Show a confirmation dialog
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Confirm Order")
            current_price = self.signal["order_params"]["entry_price"]
            sl = self.signal["order_params"]["stop_loss"]
            tp = self.signal["order_params"]["take_profit"]
            
            msg_box.setText(f"Place SELL LIMIT order for {self.symbol}?")
            msg_box.setInformativeText(
                f"Current Price: {current_price:.5f}\n"
                f"Limit Price: {limit_price:.5f}\n"
                f"Stop Loss: {sl:.5f}\n"
                f"Take Profit: {tp:.5f}"
            )
            msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msg_box.setDefaultButton(QMessageBox.No)
            
            if msg_box.exec_() == QMessageBox.Yes:
                # Place the order
                result = place_order_from_signal(
                    symbol=self.symbol,
                    signal=self.signal,
                    risk_percent=1.0,
                    order_type="LIMIT"
                )
                
                if result:
                    self.show_message("Order Placed", f"SELL LIMIT order placed successfully.\nOrder ID: {result['order']}", "info")
                else:
                    self.show_message("Order Failed", "Failed to place order. Check terminal output for details.", "error")
        else:
            self.show_message("Cannot Place Order", "No valid signal available. Try refreshing the chart.", "warning")

def show_chart_window(symbol, timeframe=mt5.TIMEFRAME_M15, auto_refresh=True, refresh_interval=10):
    """
    Display a real-time chart window with indicators
    
    Args:
        symbol (str): Symbol to chart
        timeframe (int): MT5 timeframe constant
        auto_refresh (bool): Whether to auto-refresh the chart
        refresh_interval (int): Refresh interval in seconds
    """
    window = ChartWindow(symbol, timeframe, auto_refresh, refresh_interval)
    window.show()
    return window

if __name__ == "__main__":
    # Example usage
    from mt5_init import initialize_mt5, shutdown_mt5
    
    if initialize_mt5():
        try:
            show_chart_window("EURUSD", mt5.TIMEFRAME_M15)
        finally:
            shutdown_mt5() 
# MetaTrader 5 Python Integration

This project provides Python modules to integrate with MetaTrader 5 for retrieving account information, placing orders, and real-time market monitoring with trading suggestions.

## Features

- Connect to MetaTrader 5 terminal
- Get account information
- View open positions and pending orders
- Place market and pending orders
- Close positions and cancel orders
- View trading history
- Real-time price monitoring with data recording
- Technical analysis with trading suggestions
- Multiple timeframe analysis

## Requirements

- MetaTrader 5 terminal installed
- Python 3.7+
- Required packages:
  - MetaTrader5
  - pandas
  - numpy
  - python-dotenv

## Setup

1. Install required packages:
```
pip install -r requirements.txt
```

2. Make sure your MetaTrader 5 terminal is running
3. Run the main script:
```
python main.py
```

## Module Overview

- **mt5_init.py** - Connection management functions
- **mt5_account.py** - Account information, positions, orders
- **mt5_order.py** - Order placement and management
- **mt5_monitor.py** - Real-time monitoring and trading suggestions

## Real-time Monitoring

The real-time monitoring feature:
- Collects and saves price data
- Calculates technical indicators (RSI, MACD, SMAs)
- Provides trading suggestions based on indicator signals
- Records data to CSV files for further analysis

## Trading Signals

Trading signals are based on the following indicators:
- SMA 5 and SMA 20 crossovers
- RSI overbought/oversold levels (70/30)
- MACD crossovers
- Price momentum

Each signal has a strength indicator that shows how strong the recommendation is based on multiple factors.

## Usage Examples

### Basic Account Information and Orders
```python
python main.py
# Choose option 1
```

### Market Analysis with Trading Suggestions
```python
python main.py
# Choose option 2
```

### Real-time Symbol Monitoring
```python
python main.py
# Choose option 3
# Enter symbols to monitor (e.g., EURUSD,GBPUSD)
# Enter update interval
```

## Data Storage

Price data and indicators are stored in the `price_data` directory by default:
- `{symbol}_prices.csv` - Historical price data
- `{symbol}_indicators.csv` - Technical indicators

## Webapp Signal Trading (Next.js)

Tersedia webapp berbasis Next.js di subfolder `webapp` untuk:
- Generate signal trading otomatis berdasarkan indikator populer (RSI, MACD, MA, BB, dll)
- Mendukung scalping/shortterm (M15/H1)
- Data harga diambil dari Yahoo Finance (tanpa backend Python)
- Pair default: GOLD, bisa pilih pair lain (BTCUSD, EURUSD, saham, dll)
- Chart harga dan indikator langsung di web

### Cara Menjalankan Webapp

1. Masuk ke folder webapp:
   ```bash
   cd webapp
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Jalankan development server:
   ```bash
   npm run dev
   ```
4. Buka [http://localhost:3000](http://localhost:3000) di browser.

### Deploy ke Vercel

- Webapp siap untuk deploy ke Vercel (lihat instruksi di `webapp/README.md`)

## License

This project is licensed under the MIT License - see the LICENSE file for details.

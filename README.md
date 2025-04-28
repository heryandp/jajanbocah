# TradingView API Client

Client Python untuk terhubung ke TradingView API.

## Instalasi

1. Clone repository ini
2. Install dependensi:
```bash
pip install -r requirements.txt
```
3. Salin file `.env.example` menjadi `.env` dan isi dengan kredensial TradingView Anda:
```bash
cp .env.example .env
```

## Penggunaan

```python
from tradingview_client import TradingViewClient

# Inisialisasi client
client = TradingViewClient()

# Mendapatkan data market
data = client.get_market_data("NASDAQ:AAPL")
print(data)

# Menghubungkan ke WebSocket untuk data realtime
client.connect()
client.start()
```

## Fitur

- Koneksi WebSocket untuk data realtime
- Mendapatkan data market melalui REST API
- Manajemen koneksi otomatis
- Error handling

## Catatan

Pastikan Anda memiliki kredensial TradingView yang valid sebelum menggunakan client ini.

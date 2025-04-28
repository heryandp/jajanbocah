import os
import json
import websocket
import requests
from dotenv import load_dotenv

class TradingViewClient:
    def __init__(self):
        load_dotenv()
        self.username = os.getenv('TRADINGVIEW_USERNAME')
        self.password = os.getenv('TRADINGVIEW_PASSWORD')
        self.api_key = os.getenv('TRADINGVIEW_API_KEY')
        self.ws = None
        self.session = requests.Session()
        
    def connect(self):
        """Membuat koneksi WebSocket ke TradingView"""
        websocket.enableTrace(True)
        self.ws = websocket.WebSocketApp(
            "wss://data.tradingview.com/socket.io/websocket",
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close,
            on_open=self._on_open
        )
        
    def _on_message(self, ws, message):
        """Handler untuk pesan yang diterima"""
        print(f"Pesan diterima: {message}")
        
    def _on_error(self, ws, error):
        """Handler untuk error"""
        print(f"Error: {error}")
        
    def _on_close(self, ws, close_status_code, close_msg):
        """Handler untuk koneksi tertutup"""
        print("Koneksi ditutup")
        
    def _on_open(self, ws):
        """Handler untuk koneksi terbuka"""
        print("Koneksi terbuka")
        # Kirim pesan autentikasi
        auth_message = {
            "m": "quote_add_symbols",
            "p": ["NASDAQ:AAPL"],
            "v": ["realtime"]
        }
        ws.send(json.dumps(auth_message))
        
    def start(self):
        """Memulai koneksi WebSocket"""
        self.ws.run_forever()
        
    def get_market_data(self, symbol):
        """Mendapatkan data market untuk simbol tertentu"""
        url = f"https://scanner.tradingview.com/{symbol}/scan"
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        response = self.session.get(url, headers=headers)
        return response.json()
        
    def close(self):
        """Menutup koneksi"""
        if self.ws:
            self.ws.close()
            
if __name__ == "__main__":
    client = TradingViewClient()
    try:
        client.connect()
        client.start()
    except KeyboardInterrupt:
        client.close() 
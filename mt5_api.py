from flask import Flask, request, jsonify
import MetaTrader5 as mt5
import pandas as pd
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Inisialisasi MT5 saat server start
if not mt5.initialize():
    raise Exception("MT5 initialization failed")

# Mapping timeframe string ke MT5
TF_MAP = {
    'M1': mt5.TIMEFRAME_M1,
    'M5': mt5.TIMEFRAME_M5,
    'M15': mt5.TIMEFRAME_M15,
    'M30': mt5.TIMEFRAME_M30,
    'H1': mt5.TIMEFRAME_H1,
    'H4': mt5.TIMEFRAME_H4,
    'D1': mt5.TIMEFRAME_D1,
    'W1': mt5.TIMEFRAME_W1,
    'MN1': mt5.TIMEFRAME_MN1,
}

@app.route('/ohlc')
def ohlc():
    symbol = request.args.get('symbol', 'XAUUSD')
    tf = request.args.get('tf', 'M1')
    n = int(request.args.get('n', 200))
    timeframe = TF_MAP.get(tf.upper(), mt5.TIMEFRAME_M1)
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, n)
    if rates is None or len(rates) == 0:
        return jsonify({'error': 'No data'}), 404
    df = pd.DataFrame(rates)
    df['time'] = df['time'].astype(int)
    return jsonify(df.to_dict(orient='records'))

@app.route('/ping')
def ping():
    return jsonify({'status': 'ok'})

@app.route('/symbols')
def symbols():
    symbols = mt5.symbols_get()
    symbol_names = [s.name for s in symbols]
    return jsonify(symbol_names)

if __name__ == '__main__':
    app.run(port=5000) 
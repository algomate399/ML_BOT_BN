import threading

from StrategyFactory import AlgoTrader_GPT
from StrategyRep import PredictorEngine
from flask import Flask,render_template, jsonify, request,send_file
from database import request_position
import io
from Broker_api import BROKER_API
from TICKER import TICKER_
from FYERS_BR import HIST_BROKER_
import warnings as ws
ws.simplefilter('ignore')
import pytz
import time
import pandas as pd


# Class for for handling user Interface
TICKER_TO_SUB = {'NSE:NIFTYBANK-INDEX':'D','NSE:NIFTY50-INDEX':'D'}

TREND_EMA_components = ['NSE:NIFTY50-INDEX']

Strategy_On_params = {'TREND_EMA': {'ticker': 'NSE:NIFTYBANK-INDEX','Components':TREND_EMA_components, 'interval': 'D'},
                      'SharpeRev': {'ticker':'NSE:NIFTYBANK-INDEX','Components': None,'interval': 'D'},
                      'Volatility_BRK': {'ticker': 'NSE:NIFTY50-INDEX', 'Components': None, 'interval': 'D'}
                     }

connected = False
console = False

class TradingConsole:
    LIVE_FEED = False
    Strategy_On_Board = None
    mode = None

    def __init__(self,strategy_on_params):
        # connecting to the Brokers
        self.connected,HIST,self.LIVE_FEED = self.login()
        if self.connected:
            time_zone = pytz.timezone('Asia/Kolkata')

        # assigning the broker datafeed objects
            AlgoTrader_GPT.time_zone = time_zone
            AlgoTrader_GPT.LIVE_FEED = self.LIVE_FEED
            PredictorEngine.time_zone = time_zone
            PredictorEngine.TICKER = HIST

        #   Creating Predictors based on the selected Strategy sets
            tickers = []
            self.AlgoTrader = {}
            AlgoTrader_GPT.Predictors = []
            self.max_tp_sl = 3500
            for name,param in strategy_on_params.items():
                if self.Strategy_On_Board[name]:
                    for model_type in ['long','short']:
                        AlgoTrader_GPT.Predictors.append(PredictorEngine(name,model_type,**param))
                        tickers.append(param['ticker'])

        #   creating a strategy object
            for ticker in tickers:
                for model_type in ['long', 'short']:
                    key = f'{ticker}_{model_type}'
                    self.AlgoTrader[key] = AlgoTrader_GPT(self.mode,ticker,model_type)

    def login(self):
        try:
            BROKER_APP = BROKER_API()
            HIST_APP = HIST_BROKER_()
            # login to Alice
            BROKER_APP.login()
            # login to Fyers
            HIST_APP.login()
            # initializing  the Websocket
            BROKER_APP.BROKER_WEBSOCKET_INT()
            # creating a TICKER object
            TICKER_.BROKER_OBJ = HIST_APP.BROKER_APP
            TICK = TICKER_(TICKER_TO_SUB)
            connect = True

        except Exception as e:
            msg = 'Unable to login to the User Broker due to: {}'.format(e)
            print(msg)
            connect = False

        return connect,TICK,BROKER_APP

    def on_tick(self):
        global connected

        while connected:
            for model in self.AlgoTrader:
                self.AlgoTrader[model].On_tick()

            if abs(sum([model.STR_MTM for model in self.AlgoTrader.values()])) > self.max_tp_sl:
               if all([model.squaring_of_all_position_AT_ONCE() if model.position else True for model in self.AlgoTrader.values()]):
                   pass
               else:
                   print('Unable to close all positions')

            time.sleep(0.5)
        else:
            self.LIVE_FEED.stop_websocket()


# creating flask web app
app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/on_connect', methods=['POST'])
def connect():
    global Strategy_On_params
    global connected
    global console

    status = ''
    if not connected:
        json = request.get_json()
        TradingConsole.Strategy_On_Board = json['selected_strategy']
        TradingConsole.mode = json['Mode']
        console = TradingConsole(Strategy_On_params)
        if console.connected:
            connected = console.connected
            thread = threading.Thread(target=console.on_tick)
            thread.start()
            status = 'connected'
    else:
        status = 'not connected'
        connected = False

    return status


@app.route('/get_connection_status')
def get_connection_status():
    global connected
    if connected:
        return 'connected'
    else:
        return 'not connected'


@app.route('/update-tick-data')
def Update_Ticker():
    global console

    ticker = ["NSE:NIFTYBANK-INDEX", "NSE:NIFTY50-INDEX", 'NSE:FINNIFTY-INDEX']
    if connected and all([s in console.LIVE_FEED.ltp.keys() for s in ticker]):
        updated_data = {
            'banknifty': console.LIVE_FEED.ltp["NSE:NIFTYBANK-INDEX"],
            'nifty':     console.LIVE_FEED.ltp["NSE:NIFTY50-INDEX"],
            'finnifty':  console.LIVE_FEED.ltp['NSE:FINNIFTY-INDEX']}
    else:
        updated_data = {
            'banknifty': 0,
            'nifty': 0,
            'finnifty': 0}

    return jsonify(updated_data)


@app.route('/update_positions', methods=['GET'])
def update_positions():
    global connected
    global console
    json_dt = {}
    total_mtm = 0
    if connected:
        for i,(name,model) in enumerate(console.AlgoTrader.items(), start=1):
            mtm = round(model.STR_MTM, 2)
            json_dt[str(i)] = {
            'symbol': model.index,
            'Model_Type': model.model_type,
            'POSITION': model.position,
            'MTM':mtm,}
            total_mtm += mtm

    json_dt['TOTAL'] = {'TOTAL_MTM': total_mtm}
    return jsonify(json_dt)

@app.route('/Square_off_Position',methods=['POST'])
def Sqaure_off_Position():
    resp = 'POSITION NOT AVAILABLE'
    global connected
    global console

    if connected:
        for i,(name,model) in enumerate(console.AlgoTrader.items(),start=1):
            if model.position:
                success = model.squaring_of_all_position_AT_ONCE()
                if not success:
                    resp = 'Failed'
                    break
                else:
                    resp = 'success'
    return resp

@app.route('/get_csv', methods=['POST'])
def get_csv():
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')
    df = request_position()

    # Convert the 'Date' column to datetime
    df['Date'] = pd.to_datetime(df['Date'])

    # Filter the data based on the date range
    mask = (df['Date'] >= start_date) & (df['Date'] <= end_date)
    filtered_data = df[mask]

    # Format the 'entrytime' and 'exittime' columns to include milliseconds
    filtered_data['entrytime'] = pd.to_datetime(filtered_data['entrytime']).dt.strftime('%H:%M:%S')
    filtered_data['exittime'] = pd.to_datetime(filtered_data['exittime']).dt.strftime('%H:%M:%S')

    # Generate the CSV
    csv_data = filtered_data.to_csv(index=False)

    # Return the CSV as an attachment
    return send_file(
        io.BytesIO(csv_data.encode('utf-8')),
        as_attachment=True,
        download_name='filtered_data.csv',
        mimetype='text/csv'
    )

if __name__ == '__main__':
    app.run()
from ClassLib import *
from MetaApp import MetaApi
from Forex_api import ForexApi
import threading
from flask import Flask, request, render_template , jsonify
import asyncio
import __main__

# setting Attributes to Main
setattr(__main__ , 'NoiseEnhancer' ,NoiseEnhancer)
setattr(__main__ , 'BaggingBootstrapper' ,BaggingBootstrapper)

currency = ['EURUSD' ,'GBPUSD' , 'NZDUSD']

api = MetaApi()
fx = ForexApi()

async def primary_task():
        fx.RefreshVar()
        fx.symbol_list = currency
        fx.action='close_all_positions'
        await fx.start()


async def secondary_task():
        api.Refresh_Var()
        api.UpdateHistory()
        api.GenerateSignal()
        sig_sum = np.sum([abs(s) for s in api.Signals.values()])
        if sig_sum:
            fx.RefreshVar()
            fx.symbol_list=currency
            fx.action='execute_signals'
            fx.Signals = api.Signals
            fx.sl_in_pips = api.Sl_in_PiP
            await fx.start()

        if api.error :
            api.send_email_notification(api.error)
        else :
            api.send_email_notification(api.Signals)


def run_async(x):
    asyncio.run(x)


app = Flask(__name__)

@app.route('/')
def Homepage():
    title = 'Algomate-GPT (AI Driven Model)'
    return render_template('index.html', title=title)


@app.route('/close_all_positions')
def process_signals():

    t = threading.Thread(target=run_async , args=(primary_task() , ))
    t.start()

    return jsonify({"status": "ok"})

@app.route('/submit_signals')
def submit_signal():

    t = threading.Thread(target=run_async , args=(secondary_task() , ))
    t.start()

    return jsonify({"status": "ok"})


if __name__ == '__main__':
    app.run(debug=True)




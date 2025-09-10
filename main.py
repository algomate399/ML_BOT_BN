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


ForexApi.SIG_GEN = MetaApi()
fx = ForexApi()


async def primary_task():
        fx.RefreshVar()
        fx.symbol_list = currency
        fx.action='close_all_positions'
        await fx.start()


async def secondary_task():
        fx.RefreshVar()
        fx.symbol_list = currency
        fx.action = 'execute_signals'
        await fx.start()

        if fx.error:
            fx.SIG_GEN.send_email_notification(fx.error)
        else:
            fx.SIG_GEN.send_email_notification(fx.Signals)

def run_async(x):
    asyncio.run(x)


app = Flask(__name__)

@app.route('/')
def Homepage():
    title = 'Algomate-GPT (AI Driven Model)'
    return render_template('index.html', title=title)


@app.route('/close_all_positions')
def process_positions():

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




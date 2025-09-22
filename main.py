from ClassLib import *
from MetaApp import MetaApi
from Forex_api import ForexApi
import threading
from flask import Flask, render_template , jsonify
import asyncio
import __main__

# setting Attributes to Main
setattr(__main__ , 'NoiseEnhancer' ,NoiseEnhancer)
setattr(__main__ , 'BaggingBootstrapper' ,BaggingBootstrapper)

currency = ['EURUSD' ,'GBPUSD' , 'NZDUSD']


fx = ForexApi()
fx.api = MetaApi()

async def primary_task():
        fx.RefreshVar()
        fx.symbol_list = currency
        fx.action='close_all_positions'
        await fx.start()

async def secondary_task_1():
        fx.RefreshVar()
        fx.symbol_list=currency
        fx.action='process_signals'
        await fx.start()

async def secondary_task_2():
        fx.symbol_list = currency
        fx.action = 'execute_signals'
        await fx.start()

async def task():
    await secondary_task_1()
    await secondary_task_2()

def run_async(x):
    asyncio.run(x)


app = Flask(__name__)

@app.route('/')
def Homepage():
    title = 'Algomate-GPT (AI Driven Model)'
    return render_template('index.html', title=title)


@app.route('/ping')
def pinger():
    return jsonify({"ping": "ok"})


@app.route('/close_all_positions')
def process_positions():

    t = threading.Thread(target=run_async , args=(primary_task() , ))
    t.start()

    return jsonify({"status": "ok"})


@app.route('/process_signals')
def process_signals():

    t = threading.Thread(target=run_async , args=(task() , ))
    t.start()

    return jsonify({"status": "ok"})


if __name__ == '__main__':
    app.run(debug=True)




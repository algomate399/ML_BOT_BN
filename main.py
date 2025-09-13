from ForexApi import ForexApi
from ClassLib import *
import threading
from flask import Flask,  render_template , jsonify
import asyncio
import __main__

# setting Attributes to Main
setattr(__main__ , 'NoiseEnhancer' ,NoiseEnhancer)
setattr(__main__ , 'BaggingBootstrapper' ,BaggingBootstrapper)

currency = ['EURUSD' ,'GBPUSD' , 'NZDUSD']

fx = ForexApi()


async def place_order():
    fx.RefreshVar()
    fx.symbol_list = currency
    await fx.start()
    print(fx.error)


def run_async(x):
    asyncio.run(x)


app = Flask(__name__)

@app.route('/')
def Homepage():
    title = 'Algomate-GPT (AI Driven Model)'
    return render_template('index.html', title=title)


@app.route('/submit_signals')
def submit_signal():

    t = threading.Thread(target=run_async , args=(place_order() , ))
    t.start()

    return jsonify({"status": "ok"})


if __name__ == '__main__':
    app.run(debug=True)

from ClassLib import *
from MetaApp import MetaApi
from flask import Flask, render_template,request , jsonify
import threading
import __main__

# setting Attributes to Main
setattr(__main__ , 'NoiseEnhancer' ,NoiseEnhancer)
setattr(__main__ , 'BaggingBootstrapper' ,BaggingBootstrapper)

Algo = MetaApi()
Crypto = ['ETH-USD' , 'BTC-USD']

def primary_task():
    Algo.Refresh_Var()
    Algo.symbol_list = Crypto
    Algo.UpdateHistory()
    Algo.GenerateSignals()

    if Algo.error:
       Algo.send_email_notification(Algo.error)
    else:
        msg = 'Signal Generated:{}'.format(Algo.Signals)
        Algo.send_email_notification(msg)
#
def secondary_task():
    Algo.place_order()


app = Flask(__name__)

@app.route('/')
def Homepage():
    title = 'Algomate-GPT (AI Driven Model)'
    return render_template('index.html', title=title)


@app.route('/process_signals')
def process_signals():

    t = threading.Thread(target=primary_task)
    t.start()

    return jsonify({"status": "ok"})

@app.route('/submit_signals')
def submit_signal():

    t = threading.Thread(target=secondary_task)
    t.start()

    return jsonify({"status": "ok"})


if __name__ == '__main__':
    app.run(debug=True)

from ForexApi import ForexApi
import threading
import threading
from flask import Flask, request, render_template , jsonify
import asyncio

api = ForexApi()

async def place_order():
    await api.start()


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

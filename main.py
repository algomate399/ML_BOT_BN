from ClassLib import *
from MetaApp import MetaApi
import __main__
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from flask import Flask, render_template,request
import threading
import asyncio
from pytz import timezone

# setting Attributes to Main
setattr(__main__ , 'NoiseEnhancer' ,NoiseEnhancer)
setattr(__main__ , 'BaggingBootstrapper' ,BaggingBootstrapper)

currency = ['EURUSD' ,'GBPUSD' , 'AUDUSD' , 'NZDUSD']
metals = ['XAUUSD']

fx = MetaApi()

def CheckConnection():
    fx.connector.IS_CONNECTION_ALIVE()
    if not fx.connector.connection_status:
       fx.connector.Get_CONNECTED()


def primary_task_1():
    CheckConnection()
    fx.connector.close_all_positions(metals)

def primary_task_2():
    CheckConnection()
    fx.connector.close_all_positions(currency)

def secondary_task():
    CheckConnection()
    fx.UpdateHistory()
    fx.GenerateSignals()
    fx.place_order()

    if fx.error:
        fx.send_email_notification(fx.error)
    elif fx.connector.error:
        fx.send_email_notification(fx.connector.error)
    else:
        fx.send_email_notification(fx.Signals)


app = Flask(__name__)
connected = False
passkey = '141990'

scheduler = None  # Declare the scheduler globally


async def on_tick():
    while connected:
        await asyncio.sleep(1)


@app.route('/')
def Homepage():
    title = 'Algomate-GPT(AI Driven Model)'
    return render_template('index.html', title=title)


@app.route('/on_connect', methods=['POST'])
def On_connect():
    global connected, scheduler
    status = ''
    json_data = request.get_json()

    if json_data['passkey'] == passkey:
        if not connected:
            connected = True

            # Create and start the asyncio event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            # Initialize the AsyncIOScheduler with the loop
            scheduler = AsyncIOScheduler(event_loop=loop)

            # Add tasks to the scheduler
            scheduler.add_job(primary_task_1, CronTrigger(hour=2, minute=25, timezone=timezone('Asia/Kolkata'), day_of_week='tue-sat'))
            scheduler.add_job(primary_task_2, CronTrigger(hour=3, minute=25, timezone=timezone('Asia/Kolkata'), day_of_week='tue-sat'))
            scheduler.add_job(secondary_task, CronTrigger(hour=3, minute=33, timezone=timezone('Asia/Kolkata'), day_of_week='mon-fri'))

            # Start the scheduler
            scheduler.start()

            # Start the asyncio loop in a background thread
            threading.Thread(target=loop.run_forever, daemon=True).start()

            # Schedule the on_tick coroutine
            asyncio.run_coroutine_threadsafe(on_tick(), loop)

            status = 'engine is running'
        else:
            status = 'engine stopped'
            connected = False
    else:
        status = 'Incorrect Pass key'

    return status


@app.route('/get_connection_status')
def get_connection_status():
    if connected:
        return 'engine is running'
    else:
        return 'not connected'


if __name__ == '__main__':
    app.run(debug=True)



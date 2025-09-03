import time
from ClassLib import *
from MetaApp import MetaApi
from Forex_api import ForexApi
import threading
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from pytz import timezone
import asyncio
from flask import Flask, request, render_template
import __main__

# setting Attributes to Main
setattr(__main__ , 'NoiseEnhancer' ,NoiseEnhancer)
setattr(__main__ , 'BaggingBootstrapper' ,BaggingBootstrapper)

currency = ['EURUSD' ,'GBPUSD' , 'NZDUSD']
metals = []

api = MetaApi()
fx = ForexApi()

async def primary_task_1():
    if connected and currency:
        fx.RefreshVar()
        fx.symbol_list = currency
        fx.action='close_all_positions'
        await fx.start()


async def primary_task_2():
    if connected and metals:
        fx.RefreshVar()
        fx.symbol_list = metals
        fx.action = 'close_all_positions'
        await fx.start()

async def secondary_task():
    if connected:
        api.Refresh_Var()
        api.UpdateHistory()
        api.GenerateSignal()
        print(api.Signals)
        print(api.Sl_in_PiP)
        sig_sum = np.sum([abs(s) for s in api.Signals.values()])
        if sig_sum:
            fx.RefreshVar()
            fx.symbol_list=metals+currency
            fx.action='execute_signals'
            fx.Signals = api.Signals
            fx.sl_in_pips = api.Sl_in_PiP
            await fx.start()

        if api.error :
            api.send_email_notification(api.error)
        else :
            api.send_email_notification(api.Signals)


app = Flask(__name__)
connected = False
passkey = '141990'
scheduler = None


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
            scheduler.add_job(primary_task_1 , CronTrigger(hour=21 , minute=20 , timezone=timezone('Asia/Kolkata') ,
                                                           day_of_week='tue-sat'))
            # scheduler.add_job(primary_task_2 , CronTrigger(hour=3 , minute=25 , timezone=timezone('Asia/Kolkata') ,
            #                                                day_of_week='tue-sat'))
            scheduler.add_job(secondary_task , CronTrigger(hour=21 , minute=25 , timezone=timezone('Asia/Kolkata') ,
                                                           day_of_week='mon-fri'))

            # Start the scheduler
            scheduler.start()

            # Start the asyncio loop in a background thread
            threading.Thread(target=loop.run_forever, daemon=True).start()

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





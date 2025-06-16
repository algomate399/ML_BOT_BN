
from ClassLib import *
from MetaApp import MetaApi
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from flask import Flask, render_template,request
import threading
import asyncio
from pytz import timezone
from datetime import datetime , timedelta
import __main__


# setting Attributes to Main
setattr(__main__ , 'VolatilityScaler' , VolatilityScaler)
setattr(__main__ , 'NoiseEnhancer' ,NoiseEnhancer)
setattr(__main__ , 'BaggingBootstrapper' ,BaggingBootstrapper)


MetaApp = MetaApi()

async def ConnectApp():
    await MetaApp.loadApp()

def primary_task():
    MetaApp.close_the_pending_positions()

async def secondary_task():
    MetaApp.Refresh_Var()
    await MetaApp.UpdateHistory()
    MetaApp.GenerateSignals()
    print(MetaApp.Signals)
    MetaApp.place_order()
    if MetaApp.error:
        MetaApp.send_email_notification(MetaApp.error)
    else:
        msg='Signal Generated:{}'.format(MetaApp.Signals)
        MetaApp.send_email_notification(msg)


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
            scheduler.add_job(ConnectApp,trigger='date' , run_date=datetime.now() + timedelta(seconds =5))
            scheduler.add_job(primary_task, CronTrigger(hour=10, minute=0, timezone=timezone('Asia/Kolkata'), day_of_week='tue-sat'))
            scheduler.add_job(secondary_task, CronTrigger(hour=10, minute=5, timezone=timezone('Asia/Kolkata'), day_of_week='mon-fri'))

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






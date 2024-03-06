import pandas as pd
import requests
from requests.exceptions import Timeout
from datetime import datetime
import numpy as np
def request_position():
    records = pd.DataFrame()
    url = 'https://algotrade.pythonanywhere.com/get_position'
    try:
        response = requests.get(url)
        if response.status_code == 200:
            if response.json() != 'no records':
                records = pd.DataFrame.from_records(response.json())
    except requests.exceptions.RequestException as e:
        print(f'Error:{e}')

    return records

def UpdatePositionBook(Date, entrytime, exittime ,strategy_name,spread,Transtype, Instrument,Signal, NetQty, NAV, POSITION):
    url = 'https://algotrade.pythonanywhere.com/append_position'

    # creating records
    records = {'Date': Date, 'entrytime': entrytime, 'Strategy': strategy_name,'spread':spread,'Transtype': Transtype,
               'Instrument': Instrument,'Signal': Signal, 'NetQty': NetQty,
               'NAV':  NAV, 'POSITION': POSITION,'exittime':exittime}

    payload = pd.DataFrame.from_dict([records]).to_json(orient='records')
    try:
        response = requests.post(url, json=payload)

    except Timeout:
        print('Timeout:Unable to update the PositionBook Server , Server might be busy')
        print(f'PAYLOAD:{payload}')

def GetOpenPosition(strategy):
    records = pd.DataFrame()
    Open_Pos = request_position()
    if not Open_Pos.empty:
        is_open = (Open_Pos['Strategy'] == strategy) & (Open_Pos['POSITION'] == 'OPEN')
        records = Open_Pos.loc[is_open]
    return records


def get_expiry(indices):
    #   date formats
    input_format = "%Y-%m-%d"
    output_format = "%d%b%y"

    file_name = 'NFO.csv'
    NFO = pd.read_csv(file_name)
    cond = NFO['Symbol'] == indices
    dates = NFO[cond]['Expiry Date'].unique()
    dates = np.sort(dates)
    #   format the dates
    format_dt = [datetime.strptime(date, input_format).strftime(output_format).upper() for date in dates]
    return format_dt
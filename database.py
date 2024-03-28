import pandas as pd
import requests
from requests.exceptions import Timeout
from datetime import datetime
import numpy as np
from io import StringIO
def request_position():
    records = pd.DataFrame()
    url = 'https://algomate1234.pythonanywhere.com/get_position'
    try:
        response = requests.get(url)
        if response.status_code == 200:
            if response.json() != 'no records':
                records = pd.DataFrame.from_records(response.json())
    except requests.exceptions.RequestException as e:
        print(f'Error:{e}')

    return records

def UpdatePositionBook(Date,symbol, entrytime, exittime ,strategy_name,spread,Transtype, Instrument,Signal, NetQty, NAV, POSITION):
    url = 'https://algomate1234.pythonanywhere.com/append_position'

    # creating records
    records = {'Date': Date,'Symbol':symbol,'entrytime': entrytime, 'Strategy': strategy_name,'spread':spread,'Transtype': Transtype,
               'Instrument': Instrument,'Signal': Signal, 'NetQty': NetQty,
               'NAV':  NAV, 'POSITION': POSITION,'exittime':exittime}

    payload = pd.DataFrame.from_dict([records]).to_json(orient='records')
    try:
        response = requests.post(url, json=payload)

    except Timeout:
        print('Timeout:Unable to update the PositionBook Server , Server might be busy')
        print(f'PAYLOAD:{payload}')

def GetOpenPosition(strategy,symbol):
    records = pd.DataFrame()
    Open_Pos = request_position()
    if not Open_Pos.empty:
        is_open = (Open_Pos['Strategy'] == strategy) & (Open_Pos['POSITION'] == 'OPEN') & (Open_Pos['Symbol'] == symbol)
        records = Open_Pos.loc[is_open]
    return records


def GetFormated_dates(dates_list):
    formated_dt = []
    format_dt = None
    input_format = "%Y-%m-%d"
    convert_to_custom_format = lambda date_string: ''.join([date_string.split('-')[0].replace("20", ''), date_string.split('-')[1].lstrip('0'), date_string.split('-')[2]])
    for i, dt in enumerate(dates_list):
        last_day_of_month = dates_list[i].split('-')[1] != dates_list[i + 1].split('-')[1] if i < len(dates_list) - 1 else False

        if last_day_of_month:
            month = datetime.strptime(dt, input_format).strftime('%b').upper()
            year = datetime.strptime(dt, input_format).strftime('%y').upper()
            format_dt = year + month
        else:
            format_dt = convert_to_custom_format(dt)

        formated_dt.append(format_dt)

    return formated_dt


def get_expiry(index):
    symbol = 'NIFTY' if index == 'NSE:NIFTY50-INDEX' else ('BANKNIFTY' if index == 'NSE:NIFTYBANK-INDEX' else 'FINNIFTY')
    input_format = "%Y-%m-%d"
    output_format = "%d%b%y"
    url = f"https://v2api.aliceblueonline.com/restpy/static/contract_master/NFO.csv"
    response = requests.get(url)
    csv_content = response.content.decode('utf-8')
    csv_stringio = StringIO(csv_content)
    NFO = pd.read_csv(csv_stringio)
    cond = NFO['Symbol'] == symbol
    dates = NFO[cond]['Expiry Date'].unique()
    dates = np.sort(dates)
    format_dt = [datetime.strptime(date, input_format).strftime(output_format).upper() for date in dates]
    # format the dates
    return GetFormated_dates(dates),format_dt
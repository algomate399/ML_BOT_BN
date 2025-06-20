from ejtraderCT import Ctrader
import asyncio
from Credit import *
import pandas as pd
import requests
from datetime import datetime, timedelta

def GetHistory(symbol , periods=365):
    end_date=datetime.now()
    start_date=end_date-timedelta(days=periods)

    url=f"https://api.polygon.io/v2/aggs/ticker/C:{symbol}/range/1/day/{start_date.date()}/{end_date.date()}"
    params={
        "adjusted" : "true" ,
        "sort" : "asc" ,
        "limit" : 50000 ,
        "apiKey" : api_key
    }

    # Make request
    response=requests.get(url , params=params)
    data=response.json()
    ohlc=[]
    for bar in data.get("results" , []) :
        dt=datetime.utcfromtimestamp(bar["t"] / 1000)  # Convert ms to datetime
        ohlc.append({
            "datetime" : dt ,
            "open" : bar["o"] ,
            "high" : bar["h"] ,
            "low" : bar["l"] ,
            "close" : bar["c"]
        })

    # Create DataFrame
    df=pd.DataFrame(ohlc).set_index("datetime")
    return df


class CtraderApi:
    def __init__(self , symbol_list , sl , tp):
        self.api = None
        self.symbol_list = symbol_list
        self.sl_pips = sl
        self.tp_pips = tp

    async def loadApp(self):
        self.api = Ctrader(Server , Account , password)
        self.api.subscribe(*self.symbol_list)
        await asyncio.sleep(3)

    async def logoutApp(self):
         if self.api.isconnected():
            self.api.logout()
            await asyncio.sleep(2)

    def GetQuotes(self , symbol , volume ,side):
        var='ask' if side > 0 else 'bid'
        vol =volume / 1000 if symbol == 'XAUUSD' else volume
        mul = 0.01 if 'XAUUSD' == symbol else 0.0001
        price = self.api.quote(symbol)[var]
        sl=price+-1 * side * (self.sl_pips[symbol] * mul)
        tp=price+side * (self.tp_pips[symbol] * mul)

        return vol , round(sl , 6) , round(tp , 6)

    def place_order(self , symbol , volume , side):
        id = None

        vol , sl , tp = self.GetQuotes(symbol , volume , side)

        if side > 0 :
            id = self.api.buy(symbol , vol , sl , tp)
        else:
            id = self.api.sell(symbol , vol , sl , tp)

        return id
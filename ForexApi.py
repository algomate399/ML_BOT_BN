import websockets
from Credit import*
import json
import math
import asyncio
from datetime import datetime, timedelta
from pytz import timezone
import pandas as pd

def trend_bar_transformer(trendbar: dict):
    tz = timezone("Asia/Kolkata")
    openTime = datetime.fromtimestamp(trendbar["utcTimestampInMinutes"] * 60, tz=tz).date()
    openPrice = (trendbar["low"] + trendbar["deltaOpen"]) / 100000.0
    highPrice = (trendbar["low"] + trendbar["deltaHigh"]) / 100000.0
    lowPrice = trendbar["low"] / 100000.0
    closePrice = (trendbar["low"] + trendbar["deltaClose"]) / 100000.0
    return [openTime, openPrice, highPrice, lowPrice, closePrice, trendbar["volume"]]

class ForexApi:
    def __init__(self):
        self.url = "wss://demo.ctraderapi.com:5036"
        self.time_zone = timezone("Asia/Kolkata")
        self.current_account_id = None
        self.error = []
        self.account_balance = None
        self.symbol_id = {}
        self.symbol_list = []

    def RefreshVar(self):
        self.current_account_id=None
        self.error=[]
        self.account_balance=None
        self.symbol_id={}
        self.symbol_list=[]

    def get_payload(self   , Type , add_params=None):
        payloadType=payload=None

        if Type == 'AppAuth' :
            payloadType=2100
            payload={"clientId" : client_id , "clientSecret" : client_secret}

        elif Type == 'AccountAuth' :
            payloadType=2102
            payload={"ctidTraderAccountId" : ctid_trader_account_id , "accessToken" : access_token}

        elif Type == 'AccountBal' :
            payloadType=2121
            payload={"ctidTraderAccountId" : ctid_trader_account_id}

        elif Type == 'Symbol_list' :
            payloadType=2114
            payload={"ctidTraderAccountId" : ctid_trader_account_id , "includeArchivedSymbols" : False}

        elif Type =='GetTrendBars':
            payloadType = 2137
            Days = 365
            now=datetime.now(self.time_zone)
            end_time=int(now.timestamp() * 1000)
            start_time=int((now-timedelta(days=int(Days))).timestamp() * 1000)
            payload = {"ctidTraderAccountId" : ctid_trader_account_id,
                        "fromTimestamp" : start_time,
                        "toTimestamp" : end_time,
                         "period": 12,
                          "symbolId" : add_params['symbolId']
                       }

        return json.dumps({"payloadType":payloadType , "payload":payload})

    async def GetHistory(self , symbol):
        payload = self.get_payload('GetTrendBars' , {'symbolId':self.symbol_id[symbol]})

        Daily_bars = []
        await self.ws.send(payload)

        __msg__ = await self.ws.recv()
        msg = json.loads(__msg__)

        if msg.get('payloadType') !=2138:
            return pd.DataFrame()

        Daily_bars.extend(list(map(trend_bar_transformer , msg['payload']['trendbar'])))
        history = pd.DataFrame(Daily_bars , columns=['time' , 'open' ,'high' , 'low' , 'close' , 'volume'])
        history.index = history['time']
        return history.drop(['time', 'volume'] ,axis=1)

    async def send_market_order(self ,symbol , trade_side , volume , sl):

        var = 1 if trade_side > 0 else 2

        payload={
            "payloadType" : 2106 ,
            "payload" : {
                "ctidTraderAccountId" : self.current_account_id ,
                "symbolId" : self.symbol_id[symbol] ,
                "orderType" : 1 ,
                "tradeSide": var,
                "volume" : volume,
                "relativeStopLoss" : sl
            }
        }
        await self.ws.send(json.dumps(payload))
        async with asyncio.timeout(10):
            __msg__=await self.ws.recv()
            msg=json.loads(__msg__)
            print('msg' , msg)

    async def start(self):
        async with websockets.connect(self.url) as self.ws :
            try :
                payload=self.get_payload('AppAuth')
                await self.ws.send(payload)

                __msg__=await self.ws.recv()
                msg=json.loads(__msg__)

                if msg.get('payloadType') == 2101 :
                    payload=self.get_payload('AccountAuth')
                    await self.ws.send(payload)

                    __msg__=await self.ws.recv()
                    msg=json.loads(__msg__)
                    self.current_account_id=msg["payload"]["ctidTraderAccountId"]

            except Exception as e :
                err='Unable to connect:{}'.format(e)
                self.error.append(err)

            if not self.current_account_id:
                await self.ws.close()
                return

            self.symbol_id={'GBPUSD' : 2}
            candles = await self.GetHistory('GBPUSD')
            print('candles' , candles)
            trade_dict = {'symbol': 'GBPUSD' ,"trade_side" :1  , "volume": int(0.02 * 100000 * 100) ,'sl': 558}
            await self.send_market_order(**trade_dict)
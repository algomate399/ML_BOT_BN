import pandas as pd
import websockets
import json
from Credit import *
import math
from Params import Weights
from datetime import datetime, timedelta,timezone
from pytz import timezone

def trend_bar_transformer(trendbar: dict):
    tz = timezone("Asia/Kolkata")
    openTime = datetime.fromtimestamp(trendbar["utcTimestampInMinutes"] * 60, tz = tz).date()
    openPrice = (trendbar["low"] + trendbar["deltaOpen"]) / 100000.0
    highPrice = (trendbar["low"] + trendbar["deltaHigh"]) / 100000.0
    lowPrice = trendbar["low"] / 100000.0
    closePrice = (trendbar["low"] + trendbar["deltaClose"]) / 100000.0
    return [openTime, openPrice, highPrice, lowPrice, closePrice, trendbar["volume"]]


class ForexApi:
    SIG_GEN = None

    def __init__(self):
        self.url = "wss://demo.ctraderapi.com:5036"
        self.time_zone = timezone("Asia/Kolkata")
        self.ws = None
        self.current_account_id = None
        self.error = []
        self.account_balance = None
        self.symbol_id = {}
        self.symbol_list = None
        self.action = None
        self.Signals = {}
        self.sl_in_pips = {}
        self.lot_size = {}

    #   risk setting
        self.MaxDrawdown = 8/100
        self.DailyRiskDrawdown = 5/100

    def RefreshVar(self):
        self.current_account_id=None
        self.ws = None
        self.error=[]
        self.account_balance=None
        self.symbol_id={}
        self.symbol_list=None
        self.action=None
        self.Signals={}
        self.sl_in_pips={}
        self.lot_size = {}
        self.SIG_GEN.Refresh_Var()

    def get_payload(self,Type,add_params=None):
        payloadType = payload = None

        if Type =='AppAuth':
            payloadType = 2100
            payload = {"clientId": client_id, "clientSecret": client_secret}

        elif Type =='AccountAuth':
            payloadType=2102
            payload={"ctidTraderAccountId": ctid_trader_account_id ,"accessToken": access_token}

        elif Type == 'AccountBal':
            payloadType=2121
            payload={"ctidTraderAccountId" : ctid_trader_account_id}

        elif Type =='Symbol_list':
            payloadType=2114
            payload={"ctidTraderAccountId" : ctid_trader_account_id , "includeArchivedSymbols":False}

        elif Type=='GetPositions':
            payloadType=2124
            payload={"ctidTraderAccountId" : ctid_trader_account_id}

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

    def __patch_symbol_id(self , msg) :
        for s in self.symbol_list :
            symbols=msg['payload']
            symbolsFilterResult=list(filter(lambda symbol : symbol['symbolName'] == s , symbols['symbol']))[0]
            self.symbol_id[s]=int(symbolsFilterResult['symbolId'])

    async def close_all_positions(self  , msg):
        try:
            if 'position' not in msg.get('payload'):
                return

            positions = msg.get('payload')['position']

            open_pos = [p for p in positions if int(p['tradeData']['symbolId']) in self.symbol_id.values()]

            for pos in open_pos:
                payload={
                    "payloadType" : 2111 ,
                    "payload" : {
                        "ctidTraderAccountId" : self.current_account_id ,
                        "positionId" : pos['positionId'] ,
                        "volume" : pos['tradeData']['volume']
                    }
                }
                await self.ws.send(json.dumps(payload))
        except Exception as e:
            err = {'ClosePosition:Error:{}'.format(e)}
            self.error.append(err)

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

        if trade_side <0 :
            trade_side =2

        payload={
            "payloadType" : 2106 ,
            "payload" : {
                "ctidTraderAccountId" : self.current_account_id ,
                "symbolId" : self.symbol_id[symbol] ,
                "orderType" : 1 ,
                "tradeSide": trade_side,
                "volume" : volume,
                "relativeStopLoss" : sl
            }
        }

        await self.ws.send(json.dumps(payload))

    def compute_lot_size(self) :
        # setting variables
        pip_size=lambda s : 0.01 if ('XAUUSD' == s) else (0.001 if "XAGUSD" == s else 0.0001)
        contract_size=lambda s : 100 if ('XAUUSD' == s) else (5000 if "XAGUSD" == s else 100000)
        min_lot_size=0.01

        # max drawdown in $
        max_dd= self.account_balance * self.MaxDrawdown

        # daily risk budget in $
        daily_risk=max_dd * self.DailyRiskDrawdown

        lot_sizes={}

        for symbol in self.Signals :

            # risk money allocated to this instrument
            risk_money=daily_risk * Weights[symbol]

            # lot size formula
            pip_value=contract_size(symbol) * pip_size(symbol)
            lot_size=risk_money / (self.sl_in_pips[symbol] * pip_value)
            lot_sizes[symbol]=max(round(lot_size , 2) , min_lot_size)

        return lot_sizes

    def get_sl_tp(self , symbol  , lot_size):
        contract_size = 100 if ('XAUUSD' == symbol) else (5000 if "XAGUSD" == symbol else 100000)
        pip_size=0.01 if ('XAUUSD' == symbol) else (0.001 if "XAGUSD" == symbol else 0.0001)
        pip_pos=abs(int(round(math.log10(1 / pip_size))))
        units_per_pip=10 ** (5-pip_pos)
        relative_sl=int(round(self.sl_in_pips[symbol] * units_per_pip))
        volume = int(lot_size * contract_size * 100)
        return relative_sl , volume

    async def execute_signals(self):
        for s , signal in self.Signals.items():
            if signal:
                sl , volume = self.get_sl_tp(s , self.lot_size[s])
                await self.send_market_order(s , signal , volume , sl)

    async def start(self):

        async with websockets.connect(self.url) as self.ws :
            try:
                payload = self.get_payload('AppAuth')
                await self.ws.send(payload)

                __msg__ = await self.ws.recv()
                msg = json.loads(__msg__)

                if msg.get('payloadType') ==2101:
                    payload = self.get_payload('AccountAuth')
                    await self.ws.send(payload)

                    __msg__=await self.ws.recv()
                    msg=json.loads(__msg__)
                    self.current_account_id = msg["payload"]["ctidTraderAccountId"]

            except Exception as e:
                    err = 'Unable to connect:{}'.format(e)
                    self.error.append(err)

            if not self.current_account_id:
                await self.ws.close()
                return

            payload = self.get_payload('AccountBal')
            await self.ws.send(payload)

            __msg__=await self.ws.recv()
            msg=json.loads(__msg__)

            if 'trader' not in msg.get('payload'):
                err = {'AccountBal:Error{}'.format(msg)}
                self.error.append(err)
                await self.ws.close()
                return

            account_info = msg['payload']['trader']
            self.account_balance = account_info.get('balance')/(10**account_info.get('moneyDigits'))

            payload = self.get_payload('Symbol_list')
            await self.ws.send(payload)

            __msg__=await self.ws.recv()
            msg=json.loads(__msg__)
            self.__patch_symbol_id(msg)

            if self.action =='close_all_positions':
                payload = self.get_payload('GetPositions')
                await self.ws.send(payload)

                __msg__=await self.ws.recv()
                msg=json.loads(__msg__)
                await self.close_all_positions(msg)

            else:
                await self.SIG_GEN.UpdateHistory(self)
                self.Signals , self.sl_in_pips = self.SIG_GEN.GenerateSignal()
                self.lot_size = self.compute_lot_size()

                # if self.SIG_GEN.error:
                #     self.error.append(self.SIG_GEN.error)
                #     await self.ws.close()
                #     return
                #
                # await self.execute_signals()

            await self.ws.close()
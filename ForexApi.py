import websockets
from Credit import*
import json
import math
import asyncio

class ForexApi:
    def __init__(self):
        self.url = "wss://demo.ctraderapi.com:5036"
        self.current_account_id = None
        self.error = []
        self.account_balance = None
        self.symbol_id = None
        self.symbol_list = None

    def RefreshVar(self):
        self.current_account_id=None
        self.error=[]
        self.account_balance=None
        self.symbol_id=None
        self.symbol_list=None

    def get_payload(self   , Type):
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

        return json.dumps({"payloadType":payloadType , "payload":payload})

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

            self.symbol_id = {'GBPUSD':2}
            trade_dict = {'symbol': 'GBPUSD' ,"trade_side" :1  , "volume": int(0.02 * 100000 * 100) ,'sl': 558}
            await self.send_market_order(**trade_dict)
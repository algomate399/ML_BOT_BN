from Credit import *
from Params import Weights
from ctrader_open_api import Client , Protobuf , TcpProtocol , Auth , EndPoints
from ctrader_open_api.messages.OpenApiCommonMessages_pb2 import *
from ctrader_open_api.messages.OpenApiMessages_pb2 import *
from ctrader_open_api.messages.OpenApiModelMessages_pb2 import *
from twisted.internet import reactor
import math


class ForexApi:
    def __init__(self):
        self.client = None
        self.current_account_id = None
        self.action=None
        self.execution_flag=False

        self.symbol_id = {}
        self.symbol_list = []
        self.tick_updates = {}
        self.Signals = {}
        self.sl_pips = {}

        # account setting
        self.account_balance = None
        self.MaxDrawdown = 8/100
        self.DailyRiskDrawdown = 5/100

    def Refresh_var(self):
        self.client = None
        self.current_account_id = None
        self.symbol_id = {}
        self.symbol_list = []
        self.tick_updates = {}
        self.Signals = {}
        self.sl_pips = {}
        self.account_balance = None
        self.action = None
        self.execution_flag=False

    def app_auth(self):
        req = ProtoOAApplicationAuthReq()
        req.clientId=client_id
        req.clientSecret= client_secret
        deferred=self.client.send(req)
        deferred.addErrback(self._on_error)

    def account_auth(self):
        req=ProtoOAAccountAuthReq()
        req.ctidTraderAccountId= ctid_trader_account_id
        req.accessToken=access_token
        deferred=self.client.send(req)
        deferred.addCallback(self.get_account_info)
        deferred.addCallback(self.on_symbol_list_update)
        if self.action =='close_all_positions':
            deferred.addCallback(self.get_positions)

        deferred.addErrback(self._on_error)

    def get_account_info(self , result):
        req=ProtoOATraderReq()
        req.ctidTraderAccountId=self.current_account_id
        deferred = self.client.send(req)
        return deferred

    def get_positions(self , result):
        if not self.current_account_id:
            return
        req=ProtoOAReconcileReq()
        req.ctidTraderAccountId=self.current_account_id
        deferred=self.client.send(req)
        deferred.addErrback(self._on_error)
        return deferred

    def close_all_positions(self):
        for position in self.positions:
            req = ProtoOAClosePositionReq()
            req.ctidTraderAccountId=self.current_account_id
            req.positionId = position.positionId
            req.volume = position.tradeData.volume
            deferred = self.client.send(req)
            deferred.addErrback(self._on_error)

    def on_symbol_list_update(self , result):
        if not self.current_account_id:
            return
        req=ProtoOASymbolsListReq()
        req.ctidTraderAccountId=self.current_account_id
        req.includeArchivedSymbols=False
        deferred=self.client.send(req)
        deferred.addCallback(self.__patch_symbol_id)
        if self.action !='close_all_positions':
            deferred.addCallback(self._subscribe_quotes)
        deferred.addErrback(self._on_error)
        return deferred

    def __patch_symbol_id(self , result):
        for s in self.symbol_list:
            symbols=Protobuf.extract(result)
            symbolsFilterResult=list(filter(lambda symbol : symbol.symbolName == s , symbols.symbol))[0]
            self.symbol_id[s]=int(symbolsFilterResult.symbolId)

    def _subscribe_quotes(self , result):
        req = ProtoOASubscribeSpotsReq()
        req.ctidTraderAccountId = self.current_account_id
        for i in self.symbol_id.values():
            req.symbolId.append(i)
        deferred = self.client.send(req)
        return deferred

    def _unsubscribe_quotes(self):
        req = ProtoOAUnsubscribeSpotsReq()
        req.ctidTraderAccountId = self.current_account_id
        for i in self.symbol_id.values():
            req.symbolId.append(i)
        self.client.send(req)

    def send_market_order(self , symbol_id , trade_side , volume , sl = None):
        req = ProtoOANewOrderReq()
        req.ctidTraderAccountId=self.current_account_id
        req.symbolId=symbol_id
        req.orderType=ProtoOAOrderType.MARKET
        req.tradeSide=ProtoOATradeSide.BUY if trade_side.lower() == "buy" else ProtoOATradeSide.SELL
        req.volume=volume
        if sl : req.relativeStopLoss = sl
        deferred=self.client.send(req)
        deferred.addErrback(self._on_error)

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
            lot_size=risk_money / (self.sl_pips[symbol] * pip_value)
            lot_sizes[symbol]=max(round(lot_size , 2) , min_lot_size)

        return lot_sizes

    def get_sl_tp(self , symbol , side , lot_size):
        contract_size = 100 if ('XAUUSD' == symbol) else (5000 if "XAGUSD" == symbol else 100000)
        pip_size=0.01 if ('XAUUSD' == symbol) else (0.001 if "XAGUSD" == symbol else 0.0001)
        pip_pos=abs(int(round(math.log10(1 / pip_size))))
        units_per_pip=10 ** (5-pip_pos)
        relative_sl=int(round(self.sl_pips[symbol] * units_per_pip))
        volume = int(lot_size * contract_size * 100)
        return relative_sl , volume

    def execute_signals(self):
        for s , signal in self.Signals.items():
            if signal:
               lot_size = self.compute_lot_size()
               print(lot_size)
               sl  , volume = self.get_sl_tp(s , signal ,lot_size[s])
               trade_side = 'buy' if signal > 0 else 'sell'
               self.send_market_order(self.symbol_id[s]  ,trade_side , volume=volume , sl=sl)

    def _on_connect(self ,client):
        self.app_auth()

    def _on_disconnect(self, client , msg):
        pass

    def _on_error(self, msg):
        print(msg)

    def _on_msg_(self, client , msg):

        if msg.payloadType == ProtoOAApplicationAuthRes().payloadType:
            self.account_auth()
        elif msg.payloadType == ProtoOAAccountAuthRes().payloadType:
            self.current_account_id = int(Protobuf.extract(msg).ctidTraderAccountId)
        elif msg.payloadType == ProtoOATraderRes().payloadType:
             account_info = Protobuf.extract(msg).trader
             self.account_balance = account_info.balance / (10**account_info.moneyDigits)
        elif msg.payloadType == ProtoOAReconcileRes().payloadType:
             positions = Protobuf.extract(msg).position
             self.positions = [p for p in positions if int(p.tradeData.symbolId) in self.symbol_id.values()]

             if self.positions :
                self.close_all_positions()

             reactor.callLater(10 , self.stop)

        elif msg.payloadType ==ProtoOASpotEvent().payloadType:

            if self.execution_flag:
                return

            ticks = Protobuf.extract(msg)
            self.tick_updates[int(ticks.symbolId)] = ticks

            if all([i in self.tick_updates for i in self.symbol_id.values()]):
               self.execution_flag=True
               self._unsubscribe_quotes()
               self.execute_signals()
               reactor.callLater(10 , self.stop)

    def start(self):
        self.client = Client(EndPoints.PROTOBUF_DEMO_HOST , EndPoints.PROTOBUF_PORT , TcpProtocol)
        self.client.setConnectedCallback(self._on_connect)
        self.client.setDisconnectedCallback(self._on_disconnect)
        self.client.setMessageReceivedCallback(self._on_msg_)
        self.client.startService()

    def stop(self) :
        if self.client :
            self.client.stopService()
            self.Refresh_var()


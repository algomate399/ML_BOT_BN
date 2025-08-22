from Credit import *
from ctrader_open_api import Client , Protobuf , TcpProtocol , Auth , EndPoints
from ctrader_open_api.messages.OpenApiCommonMessages_pb2 import *
from ctrader_open_api.messages.OpenApiMessages_pb2 import *
from ctrader_open_api.messages.OpenApiModelMessages_pb2 import *
from twisted.internet import reactor
from Params import sl_pips , tp_pips
import math


class ForexApi:
    def __init__(self):
        self.client = None
        self.current_account_id = None
        self.symbol_id = {}
        self.symbol_list = []
        self.tick_updates = {}
        self.Signals = {}
        self.action = None
        self.execution_flag = False

    def Refresh_var(self):
        self.client = None
        self.current_account_id = None
        self.symbol_id = {}
        self.symbol_list = []
        self.tick_updates = {}
        self.Signals = {}
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
        deferred.addCallback(self.on_symbol_list_update)
        if self.action =='close_all_positions':
            deferred.addCallback(self.get_positions)
        deferred.addErrback(self._on_error)

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

    def get_sl_tp(self , symbol , side , lot_size):
        contract_size = 100 if ('XAUUSD' == symbol) else (5000 if "XAGUSD" == symbol else 100000)
        pip_size=0.01 if ('XAUUSD' == symbol) else (0.001 if "XAGUSD" == symbol else 0.0001)
        pip_pos=abs(int(round(math.log10(1 / pip_size))))
        units_per_pip=10 ** (5-pip_pos)
        relative_sl=int(round(sl_pips[symbol] * units_per_pip))
        volume = int(lot_size * contract_size * 100)
        return relative_sl , volume

    def execute_signals(self):
        for s , signal in self.Signals.items():
            if signal:
               sl  , volume = self.get_sl_tp(s , signal , lot_size=0.01)
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


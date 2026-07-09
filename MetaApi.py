from PredictorEngine import *
from Params import *
import time
from datetime import datetime
import requests

class MetaApi:
    def __init__(self):
        self.mods = {}
        self.error = None
        self.retry_count = 5
        self.symbol_list = np.unique([v for v in strategies.values()])
        self._ON_SYMBOL_ = []
        self.__SIGNALS__ = {}
        self.weight_params = {}
        self.Weights = {}
        self.sl_points = {}
        self.trades_H , self.trades = {} , {}
        self.load_str()
        self.load_trades()

    def load_str(self):
         try:
             for s , symbols in strategies.items():
                 self.mods = {f'{s}_{symbol}' : PredictorEngine(s , symbol) for symbol in symbols}

         except Exception as e:
             self.error='Error:@load_strategy:{}'.format(e)
             print(self.error)

    def load_trades(self):
        for _STR in strategies:
            self.trades_H[_STR] , self.weight_params[_STR] = load_trade_history(_STR)

    def UpdateHistory(self) :
        for symbol in self.symbol_list :
            dir_path=os.path.join('database_fx' , symbol)
            os.makedirs(dir_path , exist_ok=True)
            file_path=os.path.join(dir_path , '{}'.format(symbol))

            for attempt in range(1 , self.retry_count+1) :
                try :
                    history=GetHistory(symbol)
                    if history is None or history.empty :
                        raise ValueError('GetHistory returned no data')

                    today=datetime.now(time_zone).date()
                    history=history[history.index.date != today]
                    history.to_csv(file_path)
                    self._ON_SYMBOL_.append(symbol)
                    time.sleep(2)
                    break

                except Exception as e :
                    if attempt == self.retry_count :
                        self.error='Error:@UpdateHistory:{}:{}'.format(symbol , e)
                        print(self.error)
                    else :
                        time.sleep(5)

    def GenerateSignals(self):

        self.__SIGNALS__  , self.Weights , self.trades , self.sl_points = {} , {} , {} , {}

        if not self._ON_SYMBOL_:
            return self.__SIGNALS__

        for __STR__ , mod in self.mods.items():
            symbol = __STR__.split('_')[1]
            if symbol in self._ON_SYMBOL_:
                self.__SIGNALS__[__STR__] , self.trades[__STR__] , self.sl_points[__STR__] = mod.__GET_SIG__()

        if self.__SIGNALS__:
           self.Weights = self.compute_weights()

    def compute_weights(self):
        inverse_vol = {s:[] for s in strategies}
        for key , signal in self.__SIGNALS__.items():
            if signal:
                _STR , symbol = key.split('_')
                on_symbol_trades = self.trades[key]
                on_symbol_H_trades = self.trades_H[_STR]
                window=self.weight_params[_STR]['window']
                mask = (on_symbol_H_trades['Ticker'] ==symbol) & (on_symbol_H_trades['Signal']!=0)
                on_trades = pd.concat([on_symbol_H_trades[mask]['NetRets'].tail(window) , on_symbol_trades] ,axis =0).sort_index()
                on_trades = on_trades[~on_trades.index.duplicated(keep='first')]
                inverse_vol[_STR].append({symbol:1/on_trades.tail(window).std()})

        # normalize weights
        weights = {}
        for _STR , entries in inverse_vol.items():
            if len(entries)==1:
                symbol=list(entries[0].keys())[0]
                weights[f'{_STR}_{symbol}'] = self.weight_params[_STR]['w_clip']
            else:
                total = np.sum([list(e.values())[0] for e in entries])
                for e in entries:
                    symbol , inv_vol=next(iter(e.items()))
                    weights[f'{_STR}_{symbol}'] = inv_vol / total

        return weights

    def place_order(self) :

        InitialCapital=100
        margin_x=2
        AvailableMargin = InitialCapital * margin_x

        for __STR__ , signal in self.__SIGNALS__.items() :
            symbol = __STR__.split('_')[1]

            if not signal :
                continue

            trade_data={
                f"SL_{ID[symbol]}" : self.sl_points[__STR__] ,
                f"V_{ID[symbol]}" : self.Weights[__STR__] * AvailableMargin ,
                f"Y_PRED_{ID[symbol]}" : signal ,
            }

            for key , val in trade_data.items() :
                url=f"https://api.tradetron.tech/api?auth-token={token}&key={key}&value={val}"
                # print(url)
                requests.get(url)

            time.sleep(3)

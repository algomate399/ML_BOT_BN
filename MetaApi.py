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
        self.inverse_vol={}
        self.load_str()

    def load_str(self):
         try:
             for s , symbols in strategies.items():
                 self.mods = {f'{s}_{symbol}' : PredictorEngine(s , symbol) for symbol in symbols}

         except Exception as e:
             self.error='Error:@load_strategy:{}'.format(e)
             print(self.error)

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
                self.__SIGNALS__[__STR__]  , self.sl_points[__STR__] , self.inverse_vol[__STR__] = mod.__GET_SIG__()

        if self.__SIGNALS__:
           self.Weights = self.compute_weights()

    def compute_weights(self , w_clip=0.20):
        weight={}
        strategy=[s.split('_')[0] for s in self.__SIGNALS__]
        for _STR in strategy :
            symbol=[s.split('_')[1] for s in self.__SIGNALS__ if s.split('_')[0] in _STR]
            inv=np.array([self.inverse_vol[i] for i in self.inverse_vol if _STR in i])
            sig=np.array([self.__SIGNALS__[i] for i in self.__SIGNALS__ if _STR in i])
            v=(inv * np.abs(sig))
            w=v / np.sum(v)
            vi=np.where(w == 1 , w_clip , w)
            w=dict(zip(symbol , vi))
            weight[_STR]=w

        return weight

    def place_order(self) :

        InitialCapital=100
        margin_x=2
        AvailableMargin = InitialCapital * margin_x
        DailyRisk = 0.05
        RiskExposure = InitialCapital * DailyRisk

        for __STR__ , signal in self.__SIGNALS__.items() :
            _STR , symbol = __STR__.split('_')

            if not signal :
                continue

            trade_data={
                f"SL_{ID[symbol]}" : self.sl_points[__STR__] ,
                f"V_{ID[symbol]}" : self.Weights[_STR][symbol] * AvailableMargin ,
                f"RV_{ID[symbol]}" : self.Weights[_STR][symbol] * RiskExposure ,
                f"Y_PRED_{ID[symbol]}" : signal ,
            }

            for key , val in trade_data.items() :
                url=f"https://api.tradetron.tech/api?auth-token={token}&key={key}&value={val}"
                # print(url)
                requests.get(url)

            time.sleep(3)

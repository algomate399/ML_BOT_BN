import numpy as np
import os
import pytz
import time
import datetime
import smtplib
from email.mime.text import MIMEText
import requests
from StrategyRep import PredictorEngine
from Params import Strategy_On_params , GetHistory


class MetaApi:
    Symbol_historyUpdates=[]

    def __init__(self):
        self.time_zone = pytz.timezone('Asia/kolkata')
        self.error = None
        self.models = {}
        self.Signals ={}
        self.symbol_list=np.unique([ticker for ticker in Strategy_On_params])
        self.load_Strategy()

    def Refresh_Var(self):
        self.error=None
        self.Signals={}

        # removing redundant file from the database_fx
        for symbol in self.symbol_list:
            file_path=os.path.join('database_fx' , symbol , '{}.csv'.format(symbol))
            if os.path.exists(file_path) :
                os.remove(file_path)

    def load_Strategy(self):
        try:
           for ticker in self.symbol_list:
               Strategy_ = Strategy_On_params[ticker]
               for key in Strategy_:
                   name = key['strategy'] + '_' + ticker
                   self.models[name] = PredictorEngine(name , ticker , key['Components'] , key['interval'])

        except Exception as e :
            self.error='Error:@load_strategy:{}'.format(e)
            print(self.error)

    def UpdateHistory(self) :
        try :
            bars = {}
            for s in self.symbol_list:
                bars[s] = GetHistory(s)
            if bars :
                self.Symbol_historyUpdates=[symbol for symbol in bars]
                for symbol , history in bars.items() :
                    file_path=os.path.join('database_fx' , symbol , symbol)
                    history.to_csv(file_path)
        except Exception as e :
            self.error='Error:@UpdateHistory:{}'.format(e)
            print(self.error)

    def GenerateSignal(self):
        try:
            self.Signals = {}
            Updated_symbol = list(set(self.symbol_list) & set(self.Symbol_historyUpdates))

            for ticker in Updated_symbol:
                sig = 0
                for key , model in self.models.items():
                    if key.split('_')[-1] ==ticker:
                        sig+=model.GetPrediction()
                        time.sleep(5)

                self.Signals[ticker] = sig

        except Exception as e:
            self.error="Error:@GEN_SIGNALS:{}".format(e)
            print(self.error)
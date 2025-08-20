import numpy as np
import os
import pytz
import time
import datetime
from Params import Strategy_On_params , sl_pips , tp_pips
from StrategyRep import PredictorEngine
from ForexApi import ForexApi
from datetime import datetime
import requests
import smtplib
from email.mime.text import MIMEText


class MetaApi:
    Symbol_historyUpdates=[]

    def __init__(self):
        self.time_zone = pytz.timezone('Asia/kolkata')
        self.error = None
        self.models = {}
        self.Signals = {}
        self.symbol_list = np.unique([ticker for ticker in Strategy_On_params])
        self.connector = ForexApi()
        self.load_Strategy()
        self.Refresh_Var()

        # email setups
        self.bot_name='FxMate-GPT(AI DRIVEN MODEL)'
        self.sender_mail='algomate399@gmail.com'
        self.sender_pass='eddx tpyl sggx ryfr'
        self.recipient_mail='tapasguha258@gmail.com'

        #   sending email response :
        msg='Engine refreshed @ :{}'.format(datetime.now(self.time_zone))
        self.send_email_notification(msg)

    def Refresh_Var(self) :
        self.Symbol_historyUpdates=[]
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

    def UpdateHistory(self):
        try:
            bars = self.connector.UpdateHistory(self.symbol_list)
            if bars:
               self.Symbol_historyUpdates = [symbol for symbol in bars]
               for symbol , history in bars.items():
                   file_path = os.path.join('database_fx' , symbol , symbol)
                   history.to_csv(file_path)
        except Exception as e:
            self.error='Error:@UpdateHistory:{}'.format(e)
            print(self.error)

    def GenerateSignals(self):
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

    def Get_sl_tp(self ,symbol , side):
        sl=tp=0
        try:
            var='ask' if side > 0 else 'bid'
            mul=0.01 if ('XAUUSD' == symbol) else (0.001 if "XAGUSD" == symbol else 0.0001)
            price=self.connector.GetLatest_Quotes(symbol , var)
            sl=price+-1 * side * (sl_pips[symbol] * mul)
            tp=price+side * (tp_pips[symbol] * mul)
        except Exception as e:
            self.error='Error:@LTP_SL_TP:{}'.format(e)
            print(self.error)

        return round(sl , ) , round(tp , 6)

    def place_order(self):
        try:
            for symbol  , signal in self.Signals.items():
                if signal:
                    sl , tp = self.Get_sl_tp(symbol , signal)
                    OrderType = 'Buy' if signal > 0 else 'Sell'
                    Volume = 0.01
                    self.connector.OrderSend(symbol , OrderType , Volume , sl , tp)
        except Exception as e:
            self.error='Error:@Place_Order:Signals:Error:{}'.format(e)
            print(self.error)

    def send_email_notification(self ,subject):

        msg_body = (f"Bot:{self.bot_name}\n"
                    f"Subject:{subject}")

        msg = MIMEText(msg_body)
        msg['Subject'] = f'{self.bot_name}:Response as on:'
        msg['From'] = self.sender_mail
        msg['To'] = self.recipient_mail

        try:
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(self.sender_mail,self.sender_pass)
                server.sendmail(self.sender_mail, self.recipient_mail, msg.as_string())

        except Exception as e:
            self.error = f'Error:{e}'
            print(self.error)
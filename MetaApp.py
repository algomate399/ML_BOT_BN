import numpy as np
import os
import pytz
import time
import datetime
from Params import *
from StrategyRep import PredictorEngine
from ct_api import *
from datetime import datetime
import smtplib
from email.mime.text import MIMEText

class MetaApi:
    Symbol_historyUpdates = []

    def __init__(self):
        self.time_zone = pytz.timezone('Asia/kolkata')
        self.unique_ticker = None
        self.error = None
        self.retry_count = 5
        self.models = {}
        self.Signals = {}
        self.api = None
        self.symbol_list = np.unique([ticker for ticker in Strategy_On_params])
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

    async def loadApp(self):
        self.api = CtraderApi(symbol_list=self.symbol_list , sl=sl_pips , tp=tp_pips)
        await self.api.loadApp()

    def Refresh_Var(self) :
        self.Symbol_historyUpdates=[]
        self.error=None
        self.Signals={}

        # removing redundant file from the database_fx
        for symbol in self.symbol_list:
            file_path=os.path.join('database_fx' , symbol , '{}'.format(symbol))
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

    async def UpdateHistory(self):
        for symbol in self.symbol_list:
            u = 0
            while u< self.retry_count:
                try:
                    file_path=os.path.join('database_fx' , symbol , '{}'.format(symbol))
                    history = GetHistory(symbol)
                    history=history[history.index.date != datetime.now(self.time_zone).today().date()]
                    history.to_csv(file_path)
                    self.Symbol_historyUpdates.append(symbol)
                    break
                except Exception as e:
                        u+=1
                        time.sleep(5)
                        if u==self.retry_count:
                            self.error ='Error:@UpdateHistory:{}:{}'.format(symbol , e)
                            print(self.error)

    def GenerateSignals(self) :
        try :
            self.Signals={}
            Updated_symbol=list(set(self.symbol_list) & set(self.Symbol_historyUpdates))

            for ticker in Updated_symbol :
                sig=0
                for key , model in self.models.items() :
                    if key.split('_')[-1] == ticker :
                        sig+=model.GetPrediction()

                self.Signals[ticker]=sig

        except Exception as e :
            self.error="Error:@GEN_SIGNALS:{}".format(e)
            print(self.error)

    def place_order(self):
        for symbol , signal in self.Signals.items():
            try:

                if signal:
                   self.api.place_order(symbol , 0.01 , signal)
        
            except Exception as e:
                   self.error='Error:@Place_Order:Signals:{}.Error:{}'.format(signal , e)
                   print(self.error)

    def close_the_pending_positions(self):
        self.api.api.close_all()
        self.api.api.cancel_all()

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

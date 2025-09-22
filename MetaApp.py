import numpy as np
import os
import pytz
import time
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from StrategyRep import PredictorEngine
from Params import Strategy_On_params


class MetaApi:
    Symbol_historyUpdates=[]

    def __init__(self):
        self.time_zone = pytz.timezone('Asia/kolkata')
        self.error = None
        self.models = {}
        self.symbol_list=np.unique([ticker for ticker in Strategy_On_params])
        self.load_Strategy()

        # email setups
        self.bot_name='FxMate-GPT(AI DRIVEN MODEL)'
        self.sender_mail='algomate399@gmail.com'
        self.sender_pass='eddx tpyl sggx ryfr'
        self.recipient_mail='tapasguha258@gmail.com'

        # sending email response :
        msg='Engine refreshed @ :{}'.format(datetime.now(self.time_zone))
        # self.send_email_notification(msg)

    def Refresh_Var(self):
        self.error=None

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

    async def UpdateHistory(self ,fetcher) :
        try :
            bars = {}
            for s in self.symbol_list:
                bars[s] = await fetcher.GetHistory(s)
            if bars :
                self.Symbol_historyUpdates=[symbol for symbol in bars]
                for symbol , history in bars.items() :
                    file_path=os.path.join('database_fx' , symbol , '{}.csv'.format(symbol))
                    history.to_csv(file_path)
        except Exception as e :
            self.error='Error:@UpdateHistory:{}'.format(e)
            print(self.error)

    def GenerateSignal(self):
        try:
            Signals = {}
            Sl_in_PiP = {}
            Updated_symbol = list(set(self.symbol_list) & set(self.Symbol_historyUpdates))

            for ticker in Updated_symbol:
                SIG = 0
                SL = {}
                for key , model in self.models.items():
                    if key.split('_')[-1] ==ticker:
                        sig  ,  sl = model.GetPrediction()
                        SIG+=sig
                        SL[sig] = sl

                if SIG:
                    Signals[ticker] = SIG
                    Sl_in_PiP[ticker] = SL[1 if SIG > 0 else -1] if SIG else 0

            return Signals , Sl_in_PiP

        except Exception as e:
            self.error="Error:@GEN_SIGNALS:{}".format(e)
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
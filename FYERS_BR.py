from fyers_apiv3 import fyersModel
from fyers_apiv3.FyersWebsocket import data_ws
from datetime import datetime
from time import sleep
import os
import pyotp
import requests
from urllib.parse import parse_qs,urlparse
import base64
import pytz


def getEncodedString(string):
    string = str(string)
    base64_bytes = base64.b64encode(string.encode("ascii"))
    return base64_bytes.decode("ascii")



class HIST_BROKER_():
    ltp = {}
    def __init__(self):
        self.BROKER_APP = None
        self.BROKER_SOCKET = None
        self.access_token = None
        self.Socket = None
        self.client_id = None
        self.symbol_on_subscription = []
        self.Indices = ["NSE:NIFTYBANK-INDEX","NSE:NIFTY50-INDEX",'NSE:FINNIFTY-INDEX']
        self.time_zone = pytz.timezone('Asia/kolkata')
        self.delete_log()

    def login(self):

        redirect_uri = "https://www.google.com/"
        self.client_id='GBF61JC6AF-100'
        secret_key = '03HZE67VQN'
        FY_ID = "XT00158"
        TOTP_KEY = "5MI36QR765HXYCG2JMW5OE5SGPEQUBLC"
        PIN = "2005"

        URL_SEND_LOGIN_OTP = "https://api-t2.fyers.in/vagator/v2/send_login_otp_v2"
        res = requests.post(url=URL_SEND_LOGIN_OTP, json={"fy_id": getEncodedString(FY_ID), "app_id": "2"}).json()
        if datetime.now(self.time_zone).second % 30 > 27: sleep(5)
        URL_VERIFY_OTP = "https://api-t2.fyers.in/vagator/v2/verify_otp"
        res2 = requests.post(url=URL_VERIFY_OTP,
                         json={"request_key": res["request_key"], "otp": pyotp.TOTP(TOTP_KEY).now()}).json()

        ses = requests.Session()
        URL_VERIFY_OTP2 = "https://api-t2.fyers.in/vagator/v2/verify_pin_v2"
        payload2 = {"request_key": res2["request_key"], "identity_type": "pin", "identifier": getEncodedString(PIN)}
        res3 = ses.post(url=URL_VERIFY_OTP2, json=payload2).json()
        ses.headers.update({
        'authorization': f"Bearer {res3['data']['access_token']}"
        })

        TOKENURL = "https://api-t1.fyers.in/api/v3/token"
        payload3 = {"fyers_id": FY_ID,
                "app_id": self.client_id[:-4],
                "redirect_uri": redirect_uri,
                "appType": "100", "code_challenge": "",
                "state": "None", "scope": "", "nonce": "", "response_type": "code", "create_cookie": True}

        res3 = ses.post(url=TOKENURL, json=payload3).json()
        url = res3['Url']
        parsed = urlparse(url)
        auth_code = parse_qs(parsed.query)['auth_code'][0]
        auth_code
        grant_type = "authorization_code"
        response_type = "code"
        session = fyersModel.SessionModel(
        client_id=self.client_id,
        secret_key=secret_key,
        redirect_uri=redirect_uri,
        response_type=response_type,
        grant_type=grant_type
        )

        session.set_token(auth_code)
        response = session.generate_token()
        self.access_token = response['access_token']
        self.BROKER_APP = fyersModel.FyersModel(client_id=self.client_id, is_async=False, token=self.access_token, log_path=os.getcwd())


    def delete_log(self):
        files = ['fyersApi.log','fyersDataSocket.log']
        for file_name in files:
            if os.path.exists(file_name):
                try:
                    os.remove(file_name)
                except Exception as e:
                    print(f'Error deleting log file {e}')
            else:
                pass

    def connect_websocket(self):
        def onmessage(message):
            if 'ltp' in message:
                self.ltp[message['symbol']] = float(message['ltp'])

        def onerror(message):
            print("Error:", message)

        def onclose(message):
            print("Connection closed:", message)

        def onopen():
            data_type = "SymbolUpdate"

            # Subscribe to the specified symbols and data type
            self.Socket.subscribe(symbols=self.Indices, data_type=data_type)
            self.Socket.keep_running()

        # Create a FyersDataSocket instance with the provided parameters
        self.Socket = data_ws.FyersDataSocket(
            access_token=f'{self.client_id}:{self.access_token}',  # Access token in the format "appid:accesstoken"
            log_path="",
            litemode=True,
            write_to_file=False,
            reconnect=True,
            on_connect=onopen,
            on_close=onclose,
            on_error=onerror,
            on_message=onmessage
        )
        self.Socket.connect()

    def subscribe_new_symbol(self, symbols):
        unique_symbols = [s for s in symbols if s not in self.symbol_on_subscription]
        if unique_symbols:
           self.Socket.subscribe(symbols=unique_symbols,data_type="SymbolUpdate")
           for s in unique_symbols:
               if s not in self.symbol_on_subscription:
                   self.symbol_on_subscription.append(s)

    def unsubscribe_symbols(self, symbols):
        symbols_to_unsubscribe = [s for s in symbols if s in self.symbol_on_subscription]
        if symbols_to_unsubscribe:
            self.Socket.unsubscribe(symbols=symbols_to_unsubscribe, data_type='SymbolUpdate')
            for s in symbols_to_unsubscribe:
                 self.Refresh_var(s)

    def get_ltp(self, symbol):
            return self.ltp[symbol]

    def Refresh_var(self,s):
        self.symbol_on_subscription.remove(s)
        self.ltp.pop(s, None)
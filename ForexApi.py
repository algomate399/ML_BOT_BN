import pandas as pd
import requests
import datetime
from pytz import timezone
import time

class ForexApi :
    def __init__(self) :
        self.time_zone = timezone('Asia/kolkata')
        self._BASE_URL_="https://mt5.mtapi.io"
        self.__USER__='95656577'
        self.__PASS__='IdGx%40kN2'
        self.__CONNECTED__=False
        self.__TOKEN__=None
        self.__SUCCESS__=200
        self.retry_count=5
        self.connection_status=False
        self.error=None

    def RefreshVar(self) :
        self.error=None

    def _ADD_SUBLINER(self , directory) :
        __LINE__=''
        if directory == 'connection_status' :
            __LINE__=f"{self._BASE_URL_}/CheckConnect?id={self.__TOKEN__}"

        elif directory == 'history_bars' :
            __LINE__=f"{self._BASE_URL_}/PriceHistory?id={self.__TOKEN__}"

        elif directory == 'OrderSend' :
            __LINE__=f"{self._BASE_URL_}/OrderSend?id={self.__TOKEN__}"

        elif directory == 'Positions' :
            __LINE__=f"{self._BASE_URL_}/OpenedOrders?id={self.__TOKEN__}"

        elif directory == 'ClosePositions' :
            __LINE__=f"{self._BASE_URL_}/OrderClose?id={self.__TOKEN__}"

        elif directory == 'GetQuote' :
            __LINE__=f"{self._BASE_URL_}/GetQuote?id={self.__TOKEN__}"

        return __LINE__

    def Get_CONNECTED(self) :
        connect_url=f"https://mt5.mtapi.io/Connect?user={self.__USER__}&password={self.__PASS__}&host=78.140.180.198&port=443&downloadOrderHistory=true&reconnectOnSymbolUpdate=true"

        for i in range(self.retry_count) :
            resp=requests.get(connect_url , timeout=10)

            if resp.status_code != self.__SUCCESS__ :
                time.sleep(2)
                self.error=resp.text
                continue

            if resp.status_code == self.__SUCCESS__ :
                self.__TOKEN__=resp.text
                self.error=None

            break

    def IS_CONNECTION_ALIVE(self) :

        if self.__TOKEN__:

            # refreshing the variables
            self.RefreshVar()

            url=self._ADD_SUBLINER('connection_status')

            for i in range(self.retry_count) :

                resp=requests.get(url , timeout=10)

                if resp.status_code != self.__SUCCESS__ :
                    time.sleep(2)

                    if self.error is None :
                        self.error=resp.text

                    continue

                if resp.status_code == self.__SUCCESS__ :
                    if resp.text == 'OK' :
                        self.connection_status=True
                        self.error=None

                break

    def process_bars(self , data) :
        df=pd.DataFrame(data)[['time' , 'openPrice' , 'highPrice' , 'lowPrice' , 'closePrice']]

        df['time']=pd.to_datetime(df['time'])

        df.set_index('time' , inplace=True)

        df=df.resample('D').agg({
            'openPrice' : 'first' ,  # First open price of the day
            'highPrice' : 'max' ,  # Maximum high price of the day
            'lowPrice' : 'min' ,  # Minimum low price of the day
            'closePrice' : 'last' ,  # Last close price of the day
        }).dropna()

        return df.rename({'openPrice' : 'open' , 'highPrice' : 'high' , 'lowPrice' : 'low' , 'closePrice' : 'close'} ,
                         axis=1)

    def GetHistoryBars(self , symbol , start_date , end_date) :
        history_bars=pd.DataFrame()

        base_url=self._ADD_SUBLINER('history_bars')

        url=f"{base_url}&symbol={symbol}&timeframe=D&from={start_date}&to={end_date}"

        for i in range(self.retry_count) :
            resp=requests.get(url , timeout=10)

            if resp.status_code != self.__SUCCESS__ :
                time.sleep(3)

                if self.error is None :
                    self.error=resp.text

                continue

            if resp.status_code == self.__SUCCESS__ :
                data=resp.json()
                history_bars=self.process_bars(data)
                self.error=None

            break

        return history_bars

    def UpdateHistory(self , symbol_list , days=365) :
        data = {}

        # setting date range
        end_date=datetime.datetime.now(self.time_zone)
        start_date=end_date-datetime.timedelta(days=days)
        to_date_str=end_date.strftime("%Y-%m-%d")
        from_date_str=start_date.strftime("%Y-%m-%d")

        for symbol in symbol_list :
            bars=self.GetHistoryBars(symbol , from_date_str , to_date_str)
            if not bars.empty :
                data[symbol]=bars

        return data

    def OrderSend(self , Symbol , Ordertype , Volume , sl , tp) :

        base_url=self._ADD_SUBLINER('OrderSend')
        url=f"{base_url}&symbol={Symbol}&operation={Ordertype}&volume={Volume}&stoploss={sl}&takeprofit={tp}"

        for i in range(self.retry_count) :
            resp=requests.get(url , timeout=10)

            if resp.status_code != self.__SUCCESS__ :
                time.sleep(3)

                if self.error is None :
                    self.error=resp.text

                continue

            if resp.status_code == self.__SUCCESS__ :
                self.error=None

            break

    def GetPositions(self , days=2) :
        Positions=[]
        base_url=self._ADD_SUBLINER('Positions')

        for i in range(self.retry_count) :
            resp=requests.get(base_url , timeout=10)

            if resp.status_code != self.__SUCCESS__ :
                time.sleep(3)

                if self.error is None :
                    self.error=resp.text

                continue

            if resp.status_code == self.__SUCCESS__ :
                Positions=resp.json()
                self.error=None

            break

        return Positions

    def close_all_positions(self , symbol_list) :
        Positions=self.GetPositions()
        base_url=self._ADD_SUBLINER('ClosePositions')

        if Positions :
            for pos in Positions :
                if pos['symbol'] in symbol_list:
                    for i in range(self.retry_count) :
                        url=f"{base_url}&ticket={pos['ticket']}"
                        resp=requests.get(url , timeout=10)

                        if resp.status_code != self.__SUCCESS__ :
                            time.sleep(3)

                            if self.error is None :
                                self.error=resp.text

                            continue

                        if resp.status_code == self.__SUCCESS__ :
                            self.error=None

                        break

    def GetLatest_Quotes(self , symbol , var) :
        quotes=0.0
        base_url=self._ADD_SUBLINER('GetQuote')
        url=f'{base_url}&symbol={symbol}'

        for i in range(self.retry_count) :
            resp=requests.get(url , timeout=10)

            if resp.status_code != self.__SUCCESS__ :
                time.sleep(3)

                if self.error is None :
                    self.error=resp.text

                continue

            if resp.status_code == self.__SUCCESS__ :
                quotes=resp.json()[var]
                self.error=None

            break

        return quotes
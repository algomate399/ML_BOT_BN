from datetime import datetime
from OrderMng import OrderMng
import numpy as np
import schedule
from database import GetOpenPosition,get_expiry
from OrderParam import OrderParam
import re
# Class for handling Strategy flow
class AlgoTrader_GPT:
    time_zone = None
    Predictors = []
    LIVE_FEED = None

    def __init__(self, mode,ticker, model_type):
        self.symbol = ticker
        self.model_type = model_type
        self.spot = 0
        self.ACT_CIR = 0
        self.spr = None
        self.STR_MTM = 0
        self.param = {}
        self.overnight_flag = False
        self.trade_flag = True
        self.processed_flag = False
        self.instrument_under_strategy = []
        self.index = 'NIFTY' if self.symbol == 'NSE:NIFTY50-INDEX' else ('BANKNIFTY' if ticker == 'NSE:NIFTYBANK-INDEX' else 'FINNIFTY')
        self.strike_interval = {'NSE:NIFTYBANK-INDEX': 100, 'NSE:NIFTY50-INDEX': 50, 'NSE:FINNIFTY-INDEX': 50}
        self.market_open = datetime.strptime('09:15:00', "%H:%M:%S").time()
        self.market_close = datetime.strptime('15:30:00', "%H:%M:%S").time()
        self.scheduler = schedule.Scheduler()
        self.position = 0
        OrderMng.LIVE_FEED = self.LIVE_FEED
        self.OrderManger = OrderMng(self.index, mode,self.model_type,self)
        self.expiry = get_expiry(self.index)

    def Is_Valid_time(self):
        valid_time = False
        current_time = datetime.now(self.time_zone).time()
        if (current_time >= self.market_open) and (current_time < self.market_close):
            valid_time = True
        return valid_time


    def IsExpiry(self):
        expiry = datetime.strptime(self.expiry[0], '%d%b%y')
        return datetime.now(self.time_zone).date() == expiry.date()

    def get_instrument(self, option_type, step, expiry_idx):
        # calculating option strike price
        interval = self.strike_interval[self.symbol]
        self.spot = self.LIVE_FEED.get_ltp(self.symbol) if not self.spot else self.spot
        strike = lambda: (round(self.spot / interval)) * interval
        ATM = strike()
        stk = ATM + interval * step
        instrument = f'{self.index}{self.expiry[expiry_idx]}{option_type[0]}{stk}'
        # appending into the list for future use
        self.instrument_under_strategy.append(instrument)

        return instrument

    def Get_Strike(self, instrument):
        ex = [e for e in self.expiry if e in instrument][-1]
        stk = instrument.replace(self.index, '').replace(ex, '')
        strike = re.findall('[0-9]+', stk)[0]
        # opt = re.findall('[A-Za-z]+', stk)[0]
        return int(strike)

    def Open_position(self,Signals):
        signal = 1 if Signals > 0 else -1
        if not self.instrument_under_strategy:
            self.param = {}
            for key, value in OrderParam(Signals,self.index, self.IsExpiry()).items():
                instrument = self.get_instrument(value['opt'], value['step'], value['expiry'])
                self.param[instrument] = {'Instrument': instrument, 'Transtype': value['transtype'],
                                          'Qty': value['Qty'],'signal':signal,'spread':value['spread']}

            # subscribing for instrument
            instrument_to_subscribe = [instrument for instrument in self.instrument_under_strategy if instrument not in self.LIVE_FEED.token.values()]
            if instrument_to_subscribe:
                self.LIVE_FEED.subscribe_new_symbol(instrument_to_subscribe)

        # checking the  feed has been started for all instruments subscribe above then taking position
        if all([s in self.LIVE_FEED.ltp.keys() for s in self.instrument_under_strategy]):
            for instrument in self.instrument_under_strategy:
                success = self.OrderManger.Add_position(**self.param[instrument])
                if not success:
                    print(f'Unable to place order for {instrument} please check with broker terminal')
                    break
                else:
                    self.position = signal

            # once the order is placed , this function will be de-scheduled
            self.scheduler.clear()
            self.spot = 0
            self.instrument_under_strategy = []
        else:
            print(f'Socket is not Opened yet,re-iterating the function')

    def squaring_of_all_position_AT_ONCE(self):
        success = False
        # function ensure instrument will SELL trans_type will be executed first then hedge position
        sequence = {k: v for k, v in
                    sorted(self.OrderManger.Transtype.items(),
                           key=lambda item: (item[1] == 'BUY', item[1] == 'SELL'))}

        # ensuring every position is squared off if not break the loop else set open position to zero
        for instrument in sequence.keys():
            if not self.OrderManger.close_position(instrument, abs(self.OrderManger.net_qty[instrument])):
                success = False
                break
            else:
                success = True

        if success:
            self.position = self.position if self.OrderManger.net_qty else 0
            if not self.position:
                self.ACT_CIR = 0
        return success

    def Validate_OvernightPosition(self):
        if self.position:
            self.squaring_of_all_position_AT_ONCE()
            self.overnight_flag = True

    def Exit_position_on_real_time(self):
        time_cond = datetime.now(self.time_zone).time() > datetime.strptime('15:15:00', "%H:%M:%S").time()
        cond = time_cond if self.model_type == 'short' else time_cond and self.IsExpiry()
        if cond:
            if self.position:
                self.squaring_of_all_position_AT_ONCE()
            self.trade_flag = False

    def MonitorTrade(self):
        if self.position and self.overnight_flag:
            if not self.ACT_CIR:
                strike = []
                OpenPos = GetOpenPosition(self.model_type,self.index)
                if not OpenPos.empty:
                    signal = list(set(OpenPos['Signal'].values))[-1]
                    self.spr = list(set(OpenPos['spread'].values))[-1]
                    for instrument in OpenPos['Instrument'].values:
                        strike.append(self.Get_Strike(instrument))
                    # only valid for bull call or put spread strategy
                    if self.spr == 'DEBIT':
                        range_ = 100
                        self.ACT_CIR = np.max(strike) - range_ if signal > 0 else np.min(strike) + range_
                    elif self.spr == 'CREDIT':
                        range_ = 100
                        self.ACT_CIR = np.min(strike) + range_ if signal > 0 else np.max(strike)-range_
                else:
                    pass

            else:
                spot = self.LIVE_FEED.get_ltp(self.symbol)
                cond_1 = (self.ACT_CIR < spot and self.position > 0) | (self.ACT_CIR > spot and self.position < 0)
                cond_2 = (self.ACT_CIR > spot and self.position > 0) | (self.ACT_CIR < spot and self.position < 0)
                if (cond_1 and self.spr == 'DEBIT') | (cond_2 and self.spr == 'CREDIT'):
                    self.squaring_of_all_position_AT_ONCE()
                    self.processed_flag = False

    def Generate_Signals(self):
        signals = []
        for predictor in self.Predictors:
            if predictor.model_type == self.model_type and predictor.symbol == self.symbol:
                 signals.append(predictor.GetSignal())

        return sum(signals)

    def On_tick(self):
        # updating the overnight position
        if self.Is_Valid_time():
            if not self.overnight_flag:
                self.Validate_OvernightPosition()
                if not self.scheduler.jobs:
                    self.scheduler.every(5).seconds.do(self.OrderManger.Update_OpenPosition)
            else:
                if not self.position and self.trade_flag and not self.processed_flag and not self.scheduler.jobs:
                    Signals = -1 * self.Generate_Signals() if self.model_type == 'short' else self.Generate_Signals()
                    if Signals:
                        self.scheduler.every(5).seconds.do(self.Open_position,Signals)
                    self.processed_flag = True

        self.MonitorTrade()
        self.STR_MTM = round(self.OrderManger.Live_MTM(),2) if self.position else round(self.OrderManger.CumMtm,2)
        # checking the scheduled task
        self.scheduler.run_pending()
        self.Exit_position_on_real_time()
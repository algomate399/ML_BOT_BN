def OrderParam(strategy_name, signal, index, is_expiry=False):
    QTY = 50 if index =='NIFTY' else 15
    p1 = p2 = spread = None
    if strategy_name == 'TREND_EMA':
        if signal == 1:

            if is_expiry:
                # credit spread
                p1 = {'opt': 'PE', 'step': -8, 'transtype': 'BUY', 'Qty': QTY, 'expiry': 0 , 'spread':'CREDIT'}
                p2 = {'opt': 'PE', 'step': -4, 'transtype': 'SELL', 'Qty': QTY, 'expiry': 0 , 'spread':'CREDIT'}
            else:
                # debit spread
                p1 = {'opt': 'CE', 'step': 0, 'transtype': 'BUY', 'Qty': QTY, 'expiry': 0 , 'spread':'DEBIT'}
                p2 = {'opt': 'CE', 'step': 4, 'transtype': 'SELL', 'Qty': QTY, 'expiry': 0 , 'spread':'DEBIT'}

        elif signal == -1:
            if is_expiry:
                # credit spread
                p1 = {'opt': 'CE', 'step': 8, 'transtype': 'BUY', 'Qty': QTY, 'expiry': 0 , 'spread':'CREDIT'}
                p2 = {'opt': 'CE', 'step': 4, 'transtype': 'SELL', 'Qty': QTY, 'expiry': 0 ,'spread':'CREDIT'}
            else:
                # debit spread
                p1 = {'opt': 'PE', 'step': 0, 'transtype': 'BUY', 'Qty': QTY, 'expiry': 0, 'spread':'DEBIT'}
                p2 = {'opt': 'PE', 'step': -4, 'transtype': 'SELL', 'Qty': QTY, 'expiry': 0,'spread':'DEBIT'}

    elif strategy_name == 'SharpeRev':
        if signal == 1:

            if is_expiry:
                # credit spread
                p1 = {'opt': 'PE', 'step': -8, 'transtype': 'BUY', 'Qty': QTY, 'expiry': 0 , 'spread':'CREDIT'}
                p2 = {'opt': 'PE', 'step': -4, 'transtype': 'SELL', 'Qty': QTY, 'expiry': 0 , 'spread':'CREDIT'}
            else:
                # debit spread
                p1 = {'opt': 'CE', 'step': 0, 'transtype': 'BUY', 'Qty': QTY, 'expiry': 0 , 'spread':'DEBIT'}
                p2 = {'opt': 'CE', 'step': 4, 'transtype': 'SELL', 'Qty': QTY, 'expiry': 0 , 'spread':'DEBIT'}

        elif signal == -1:
            if is_expiry:
                # credit spread
                p1 = {'opt': 'CE', 'step': 8, 'transtype': 'BUY', 'Qty': QTY, 'expiry': 0 , 'spread':'CREDIT'}
                p2 = {'opt': 'CE', 'step': 4, 'transtype': 'SELL', 'Qty': QTY, 'expiry': 0 ,'spread':'CREDIT'}
            else:
                # debit spread
                p1 = {'opt': 'PE', 'step': 0, 'transtype': 'BUY', 'Qty': QTY, 'expiry': 0, 'spread':'DEBIT'}
                p2 = {'opt': 'PE', 'step': -4, 'transtype': 'SELL', 'Qty': QTY, 'expiry': 0,'spread':'DEBIT'}


    elif strategy_name == 'Volatility_BRK':
        if signal == 1:

            if is_expiry:
                # credit spread
                p1 = {'opt': 'PE', 'step': -8, 'transtype': 'BUY', 'Qty': QTY, 'expiry': 0, 'spread': 'CREDIT'}
                p2 = {'opt': 'PE', 'step': -4, 'transtype': 'SELL', 'Qty': QTY, 'expiry': 0, 'spread': 'CREDIT'}
            else:
                # debit spread
                p1 = {'opt': 'CE', 'step': 0, 'transtype': 'BUY', 'Qty': QTY, 'expiry': 0, 'spread': 'DEBIT'}
                p2 = {'opt': 'CE', 'step': 4, 'transtype': 'SELL', 'Qty': QTY, 'expiry': 0, 'spread': 'DEBIT'}

        elif signal == -1:
            if is_expiry:
                # credit spread
                p1 = {'opt': 'CE', 'step': 8, 'transtype': 'BUY', 'Qty': QTY, 'expiry': 0, 'spread': 'CREDIT'}
                p2 = {'opt': 'CE', 'step': 4, 'transtype': 'SELL', 'Qty': QTY, 'expiry': 0, 'spread': 'CREDIT'}
            else:
                # debit spread
                p1 = {'opt': 'PE', 'step': 0, 'transtype': 'BUY', 'Qty': QTY, 'expiry': 0, 'spread': 'DEBIT'}
                p2 = {'opt': 'PE', 'step': -4, 'transtype': 'SELL', 'Qty': QTY, 'expiry': 0, 'spread': 'DEBIT'}

    return {'p1': p1, 'p2': p2}


def get_params(strategy_name):
    param_list = None
    if strategy_name == 'SharpeRev':
        param_list = [{'lags': 5,'lookback': 25,'normal_window': 10,'q_dn': 0.35,'q_up': 1.0,'window': 5},
                     {'lags': 5,'lookback': 5,'normal_window': 23,'q_dn': 0.05,'q_up': 0.85,'window': 15},
                     {'lags': 0,'lookback': 9,'normal_window': 62,'q_dn': 0.05,'q_up': 0.85,'window': 5},
                     {'lags': 5,'lookback': 5,'normal_window': 84,'q_dn': 0.35,'q_up': 1.0,'window': 5},
                     {'lags': 5,'lookback': 5,'normal_window': 100,'q_dn': 0.05,'q_up': 0.85,'window': 5},
                     {'lags': 4,'lookback': 24,'normal_window': 11,'q_dn': 0.15014140644139562,'q_up': 0.9922558895402418,'window': 14}]

    elif strategy_name == 'TREND_EMA':
        param_list = [{'lags': 5, 'lookback_1': 5, 'lookback_2': 25, 'normal_window': 10, 'window': 30},
                        {'lags': 5, 'lookback_1': 5, 'lookback_2': 10, 'normal_window': 10, 'window': 5},
                        {'lags': 5, 'lookback_1': 8, 'lookback_2': 15, 'normal_window': 125, 'window': 16},
                        {'lags': 3, 'lookback_1': 6, 'lookback_2': 10, 'normal_window': 122, 'window': 21},
                        {'lags': 0, 'lookback_1': 8, 'lookback_2': 10, 'normal_window': 150, 'window': 30},
                        {'lags': 5, 'lookback_1': 8, 'lookback_2': 10, 'normal_window': 52, 'window': 30}]

    elif strategy_name == 'Volatility_BRK':
        param_list = [{'band_width': 1.5, 'lags': 5, 'lookback': 60, 'normal_window': 150},
                     {'band_width': 1.5, 'lags': 5, 'lookback': 60, 'normal_window': 10},
                     {'band_width': 1.5, 'lags': 5, 'lookback': 60, 'normal_window': 49},
                     {'band_width': 1.5, 'lags': 0, 'lookback': 5, 'normal_window': 135},
                     {'band_width': 1.5, 'lags': 0, 'lookback': 30, 'normal_window': 150}]
    return param_list


def get_ensemble_n(strategy_name):
    return len(get_params(strategy_name))
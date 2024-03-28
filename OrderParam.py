def OrderParam( Signals, index, is_expiry=False):
    PositionMultiplier = abs(Signals)
    QTY = 50 * PositionMultiplier if index =='NIFTY' else 15*PositionMultiplier
    p1 = p2 = spread = None

    if Signals > 0:
        if is_expiry:
            # credit spread
            p1 = {'opt': 'PE', 'step': -6, 'transtype': 'BUY', 'Qty': QTY, 'expiry': 0, 'spread':'CREDIT'}
            p2 = {'opt': 'PE', 'step': -3, 'transtype': 'SELL', 'Qty': QTY, 'expiry': 0, 'spread':'CREDIT'}
        else:
            # debit spread
            p1 = {'opt': 'CE', 'step': 0, 'transtype': 'BUY', 'Qty': QTY, 'expiry': 0, 'spread':'DEBIT'}
            p2 = {'opt': 'CE', 'step': 4, 'transtype': 'SELL', 'Qty': QTY, 'expiry': 0, 'spread':'DEBIT'}

    elif Signals < 0:
        if is_expiry:
            # credit spread
            p1 = {'opt': 'CE', 'step': 6, 'transtype': 'BUY', 'Qty': QTY, 'expiry': 0, 'spread':'CREDIT'}
            p2 = {'opt': 'CE', 'step': 3, 'transtype': 'SELL', 'Qty': QTY, 'expiry': 0,'spread':'CREDIT'}
        else:
            # debit spread
            p1 = {'opt': 'PE', 'step': 0, 'transtype': 'BUY', 'Qty': QTY, 'expiry': 0, 'spread':'DEBIT'}
            p2 = {'opt': 'PE', 'step': -4, 'transtype': 'SELL', 'Qty': QTY, 'expiry': 0,'spread':'DEBIT'}

    return {'p1': p1, 'p2': p2}


def get_params(strategy_name, model_type):
    param_list = None
    if strategy_name == 'SharpeRev':
        if model_type == 'long':
            param_list = [{'lags': 5,'lookback': 25,'normal_window': 10,'q_dn': 0.35,'q_up': 1.0,'window': 5},
                         {'lags': 5,'lookback': 5,'normal_window': 23,'q_dn': 0.05,'q_up': 0.85,'window': 15},
                         {'lags': 0,'lookback': 9,'normal_window': 62,'q_dn': 0.05,'q_up': 0.85,'window': 5},
                         {'lags': 5,'lookback': 5,'normal_window': 84,'q_dn': 0.35,'q_up': 1.0,'window': 5},
                         {'lags': 5,'lookback': 5,'normal_window': 100,'q_dn': 0.05,'q_up': 0.85,'window': 5},
                         {'lags': 4,'lookback': 24,'normal_window': 11,'q_dn': 0.15014140644139562,'q_up': 0.9922558895402418,'window': 14}]

        else:
            param_list = [{'lags': 5, 'lookback': 14, 'normal_window': 100, 'q_dn': 0.35, 'q_up': 0.85, 'window': 5},
                          {'lags': 0, 'lookback': 5, 'normal_window': 43, 'q_dn': 0.35, 'q_up': 1.0, 'window': 13},
                          {'lags': 5, 'lookback': 5, 'normal_window': 88, 'q_dn': 0.05, 'q_up': 0.85, 'window': 15},
                          {'lags': 5, 'lookback': 25, 'normal_window': 94, 'q_dn': 0.05, 'q_up': 1.0, 'window': 5},
                          {'lags': 5, 'lookback': 11, 'normal_window': 27, 'q_dn': 0.05, 'q_up': 1.0, 'window': 12},
                          {'lags': 5, 'lookback': 14, 'normal_window': 61, 'q_dn': 0.35, 'q_up': 1.0, 'window': 5}]

    elif strategy_name == 'TREND_EMA':
        if model_type == 'long':
            param_list = [{'lags': 5, 'lookback_1': 5, 'lookback_2': 25, 'normal_window': 10, 'window': 30},
                            {'lags': 5, 'lookback_1': 5, 'lookback_2': 10, 'normal_window': 10, 'window': 5},
                            {'lags': 5, 'lookback_1': 8, 'lookback_2': 15, 'normal_window': 125, 'window': 16},
                            {'lags': 3, 'lookback_1': 6, 'lookback_2': 10, 'normal_window': 122, 'window': 21},
                            {'lags': 0, 'lookback_1': 8, 'lookback_2': 10, 'normal_window': 150, 'window': 30},
                            {'lags': 5, 'lookback_1': 8, 'lookback_2': 10, 'normal_window': 52, 'window': 30}]
        else:
            param_list = [{'lags': 5, 'lookback_1': 8, 'lookback_2': 10, 'normal_window': 150, 'window': 30},
                          {'lags': 0, 'lookback_1': 5, 'lookback_2': 25, 'normal_window': 10, 'window': 19},
                          {'lags': 5, 'lookback_1': 5, 'lookback_2': 25, 'normal_window': 150, 'window': 5}]

    elif strategy_name == 'Volatility_BRK':
        if model_type == 'long':
            param_list = [{'band_width': 1.5, 'lags': 5, 'lookback': 60, 'normal_window': 150},
                         {'band_width': 1.5, 'lags': 5, 'lookback': 60, 'normal_window': 10},
                         {'band_width': 1.5, 'lags': 5, 'lookback': 60, 'normal_window': 49},
                         {'band_width': 1.5, 'lags': 0, 'lookback': 5, 'normal_window': 135},
                         {'band_width': 1.5, 'lags': 0, 'lookback': 30, 'normal_window': 150}]
        else:
            param_list = [{'band_width': 1.5, 'lags': 5, 'lookback': 60, 'normal_window': 122},
                          {'band_width': 0.05, 'lags': 5, 'lookback': 5, 'normal_window': 10}]

    elif strategy_name == '3EMA':
        if model_type == 'long':
            param_list = [{'lags': 5,  'lookback_1': 3, 'lookback_2': 18, 'lookback_3': 21,  'normal_window': 123, 'window_1': 7, 'window_2': 21},
                          {'lags': 0, 'lookback_1': 3, 'lookback_2': 18, 'lookback_3': 21,'normal_window': 42,  'window_1': 7, 'window_2': 19}]
        else:
            param_list = [{'lags': 5,'lookback_1': 9, 'lookback_2': 11, 'lookback_3': 55,'normal_window': 67,'window_1': 7, 'window_2': 21},
                          {'lags': 5,'lookback_1': 9, 'lookback_2': 11, 'lookback_3': 30,'normal_window': 150,'window_1': 7, 'window_2': 21}]

    elif strategy_name == 'SPREAD':
         if model_type == 'long':
            param_list = [{'dn_q': 0.17989029361812062, 'lags': 0,  'lookback': 7,  'normal_window': 148,  'up_q': 0.6880853102870929},
                            {'dn_q': 0.1, 'lags': 5,  'lookback': 8,  'normal_window': 150,  'up_q': 0.6},
                            {'dn_q': 0.1, 'lags': 0,  'lookback': 8,  'normal_window': 129,  'up_q': 0.6},
                            {'dn_q': 0.3, 'lags': 5,  'lookback': 5,  'normal_window': 127,  'up_q': 0.6},
                            {'dn_q': 0.16403142490389894, 'lags': 4,  'lookback': 7,  'normal_window': 53, 'up_q': 0.8188527449350995},
                            {'dn_q': 0.1, 'lags': 5,  'lookback': 8, 'normal_window': 57, 'up_q': 1.0}]
         else:
            param_list = [{'dn_q': 0.1, 'lags': 5,  'lookback': 5, 'normal_window': 50,  'up_q': 1.0},
                            {'dn_q': 0.1, 'lags': 5,  'lookback': 5,  'normal_window': 95,  'up_q': 1.0},
                            {'dn_q': 0.3, 'lags': 5,  'lookback': 5,  'normal_window': 122,  'up_q': 1.0}]

    elif strategy_name == 'MEAN_REVERT':
        if model_type == 'long':
            param_list = [{'lags': 5, 'lookback_1': 5, 'lookback_2': 55,  'normal_window': 112,  'window': 8},
                        {'lags': 0,  'lookback_1': 5, 'lookback_2': 13,  'normal_window': 73,  'window': 8},
                        {'lags': 0,  'lookback_1': 8, 'lookback_2': 55,  'normal_window': 150, 'window': 8},
                        {'lags': 0,  'lookback_1': 8, 'lookback_2': 13,  'normal_window': 112,  'window': 21},
                        {'lags': 0,  'lookback_1': 8, 'lookback_2': 55, 'normal_window': 150,  'window': 21},
                        {'lags': 5,  'lookback_1': 5, 'lookback_2': 55,  'normal_window': 126,  'window': 8},
                        {'lags': 5,  'lookback_1': 5, 'lookback_2': 30,  'normal_window': 50,  'window': 13}]
        else:
            param_list = [{'lags': 3, 'lookback_1': 7, 'lookback_2': 13,  'normal_window': 72,  'window': 8},
                          {'lags': 0,  'lookback_1': 5, 'lookback_2': 23,  'normal_window': 150,  'window': 8},
                          {'lags': 0,  'lookback_1': 5, 'lookback_2': 13, 'normal_window': 138, 'window': 8}]

    return param_list


def get_ensemble_n(strategy_name,model_type):
    return len(get_params(strategy_name, model_type))
import os
import json


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


def get_ensemble_n(strategy_name,model_type):
    file_name = f'{strategy_name}_params_1'
    path = os.path.join('TRAINED_ML',strategy_name, model_type , file_name)
    with open(path, 'r') as f:
        params = json.load(f)
    return params,len(params)
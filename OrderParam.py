import os
import json


def OrderParam( Signal,lot_size):
    PositionMultiplier = 1
    QTY = lot_size * PositionMultiplier
    p1 = p2 = spread = None

    if Signal > 0:
            p1 = {'opt': 'PE', 'step': -3, 'transtype': 'BUY', 'Qty': QTY, 'expiry': 0, 'spread':'CREDIT'}
            p2 = {'opt': 'PE', 'step': 0, 'transtype': 'SELL', 'Qty': QTY, 'expiry': 0, 'spread':'CREDIT'}
    elif Signal < 0:
            p1 = {'opt': 'CE', 'step': 3, 'transtype': 'BUY', 'Qty': QTY, 'expiry': 0, 'spread':'CREDIT'}
            p2 = {'opt': 'CE', 'step': 0, 'transtype': 'SELL', 'Qty': QTY, 'expiry': 0,'spread':'CREDIT'}

    return {'p1': p1, 'p2': p2}


def get_ensemble_n(strategy_name,model_type):
    file_name = f'{strategy_name}_params_1'
    path = os.path.join('TRAINED_ML',strategy_name, model_type,file_name)
    with open(path, 'r') as f:
        params = json.load(f)
    return params,len(params)
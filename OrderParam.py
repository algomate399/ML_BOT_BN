def OrderParam(strategy_name, signal, is_expiry=False):
    p1 = p2 = spread = None
    if strategy_name == 'TREND_EMA':
        if signal == 1:

            if is_expiry:
                # credit spread
                p1 = {'opt': 'PE', 'step': -8, 'transtype': 'BUY', 'Qty': 15, 'expiry': 0}
                p2 = {'opt': 'PE', 'step': -5, 'transtype': 'SELL', 'Qty': 15, 'expiry': 0}
                spread = 'CREDIT'
            else:
                # debit spread
                p1 = {'opt': 'CE', 'step': 0, 'transtype': 'BUY', 'Qty': 15, 'expiry': 0}
                p2 = {'opt': 'CE', 'step': 4, 'transtype': 'SELL', 'Qty': 15, 'expiry': 0}
                spread = 'DEBIT'

        elif signal == -1:
            if is_expiry:
                # debit spread
                p1 = {'opt': 'CE', 'step': 8, 'transtype': 'BUY', 'Qty': 15, 'expiry': 0}
                p2 = {'opt': 'CE', 'step': 5, 'transtype': 'SELL', 'Qty': 15, 'expiry': 0}
                spread = 'CREDIT'
            else:
                # credit spread
                p1 = {'opt': 'PE', 'step': 0, 'transtype': 'BUY', 'Qty': 15, 'expiry': 0}
                p2 = {'opt': 'PE', 'step': -4, 'transtype': 'SELL', 'Qty': 15, 'expiry': 0}
                spread = 'DEBIT'

    elif strategy_name == 'SharpeRev':
        if signal == 1:
            if is_expiry:
                # credit spread
                p1 = {'opt': 'PE', 'step': -8, 'transtype': 'BUY', 'Qty': 15, 'expiry': 0}
                p2 = {'opt': 'PE', 'step': -5, 'transtype': 'SELL', 'Qty': 15, 'expiry': 0}
                spread = 'CREDIT'
            else:
                # debit spread
                p1 = {'opt': 'CE', 'step': 0, 'transtype': 'BUY', 'Qty': 15, 'expiry': 0}
                p2 = {'opt': 'CE', 'step': 4, 'transtype': 'SELL', 'Qty': 15, 'expiry': 0}
                spread = 'DEBIT'

        elif signal == -1:
            if is_expiry:
                # credit spread
                p1 = {'opt': 'CE', 'step': 8, 'transtype': 'BUY', 'Qty': 15, 'expiry': 0}
                p2 = {'opt': 'CE', 'step': 5, 'transtype': 'SELL', 'Qty': 15, 'expiry': 0}
                spread = 'CREDIT'
            else:
                #  debit  spread
                p1 = {'opt': 'PE', 'step': 0, 'transtype': 'BUY', 'Qty': 15, 'expiry': 0}
                p2 = {'opt': 'PE', 'step': -4, 'transtype': 'SELL', 'Qty': 15, 'expiry': 0}
                spread = 'DEBIT'

    elif strategy_name == 'MOM_BURST':
        if signal == 1:

            if is_expiry:
                # credit spread
                p1 = {'opt': 'PE', 'step': -8, 'transtype': 'BUY', 'Qty': 15, 'expiry': 0}
                p2 = {'opt': 'PE', 'step': -5, 'transtype': 'SELL', 'Qty': 15, 'expiry': 0}
                spread = 'CREDIT'
            else:
                # debit spread
                p1 = {'opt': 'CE', 'step': 0, 'transtype': 'BUY', 'Qty': 15, 'expiry': 0}
                p2 = {'opt': 'CE', 'step': 4, 'transtype': 'SELL', 'Qty': 15, 'expiry': 0}
                spread = 'DEBIT'

        elif signal == -1:
            if is_expiry:
                # credit spread
                p1 = {'opt': 'CE', 'step': 8, 'transtype': 'BUY', 'Qty': 15, 'expiry': 0}
                p2 = {'opt': 'CE', 'step': 5, 'transtype': 'SELL', 'Qty': 15, 'expiry': 0}
                spread = 'CREDIT'
            else:
                # debit spread
                p1 = {'opt': 'PE', 'step': 0, 'transtype': 'BUY', 'Qty': 15, 'expiry': 0}
                p2 = {'opt': 'PE', 'step': -4, 'transtype': 'SELL', 'Qty': 15, 'expiry': 0}
                spread = 'DEBIT'

    return {'p1': p1, 'p2': p2, 'spread':spread}
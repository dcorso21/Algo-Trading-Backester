from local_functions.main import global_vars as gl


def create_sells(qty, exe_price):

    current = gl.current()

    ticker = current['ticker']
    timestamp = gl.common_ana.get_timestamp(
        current['minute'], current['second'])
    exe_price = round(current['close'], 3)
    cash_value = round(qty * exe_price, 2)

    columns = {'ticker': [ticker],
               'send_time': [timestamp],
               'buy_or_sell': ['SELL'],
               'cash': [cash_value],
               'qty': [qty],
               'exe_price': [exe_price]}

    sells = gl.pd.DataFrame(columns)
    return sells


def create_buys(cash_value, exe_price):

    current = gl.current()

    ticker = current['ticker']
    timestamp = gl.common_ana.get_timestamp(
        current['minute'], current['second'])

    qty = gl.common_ana.cash_to_shares(cash_value, exe_price)
    cash_value = round(qty * exe_price, 2)

    columns = {'ticker': [ticker],
               'send_time': [timestamp],
               'buy_or_sell': ['BUY'],
               'cash': [cash_value],
               'qty': [qty],
               'exe_price': [exe_price]
               }

    buys = gl.pd.DataFrame(columns)
    return buys


def size_in():
    '''
    Looks at exposure and chart to decide how much to put in for a trade. 

    '''
    pass
    # return cash_value

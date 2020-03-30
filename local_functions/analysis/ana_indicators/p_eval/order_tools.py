from local_functions.main import global_vars as gl


def create_sells(qty, exe_price):
    '''
    # Create Sells
    Creates A one-row DataFrame sell order

    Returns the Sell Order DF. 

    ## Parameters: {
    qty: amount of shares to sell. 
    exe_price: price to sell at. 
    }
    '''

    current = gl.current

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
    '''
    # Create Sells
    Creates A one-row DataFrame buy order

    Returns the Buy Order DF. 

    ## Parameters: {

    cash_value: buy amount (will be converted to shares with round down). 

    exe_price: price to buy at. 

    }
    '''

    current = gl.current

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

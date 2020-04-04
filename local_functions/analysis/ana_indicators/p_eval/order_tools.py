from local_functions.main import global_vars as gl


def create_sells(qty, exe_price, cancel_spec):
    '''
    # Create Sells
    Creates A one-row DataFrame sell order

    Returns the Sell Order DF. 

    ## Parameters: {
    qty: amount of shares to sell. 

    exe_price: price to sell at. 

    cancel_spec: specification of how to cancel the order if need be. 

    }
    '''
    current = gl.current
    ticker = current['ticker']
    timestamp = gl.common_ana.get_timestamp(
        current['minute'], current['second'])
    cash_value = round(qty * exe_price, 2)

    columns = {'ticker': [ticker],
               'send_time': [timestamp],
               'buy_or_sell': ['SELL'],
               'cash': [cash_value],
               'qty': [qty],
               'exe_price': [exe_price],
               'cancel_spec': [cancel_spec]}

    sells = gl.pd.DataFrame(columns)
    return sells


def create_buys(cash_value, exe_price, cancel_spec):
    '''
    # Create Buys
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
               'exe_price': [exe_price],
               'cancel_spec': [cancel_spec]}

    buys = gl.pd.DataFrame(columns)
    return buys


def size_in():
    '''
    Looks at exposure and chart to decide how much to put in for a trade. 

    '''
    pass
    # return cash_value

# Cancellation Dictionaty


def sell_to_breakeven():
    exe_price = gl.common_ana.get_average()
    qty = gl.current_positions.qty.sum()
    sells = create_sells(qty, exe_price, cancel_specs['standard'])
    return sells


def extrapolate_exe_price():
    current = gl.current
    current_vola = gl.volas['current']
    sec_vola = current_vola / (current['second']+1)
    vola_offset = sec_vola * 3
    offset = (vola_offset * .01) * current['close']

    # Determine if the candle is red or green,
    # And if the price is above or below the average.
    candle = 'green'
    if current['open'] > current['close']:
        candle = 'red'

    if candle == 'red':
        offset = (current_vola * .01) * current['close']
        exe_price = current['close'] - offset
    else:
        exe_price = current['close'] + offset

    return exe_price


cancel_specs = {
    'standard': r'p:%5,t:7'
}


def bid_price():
    current_price = gl.current['close']
    bid = current_price - .01
    return bid


def ask_price():
    current_price = gl.current['close']
    ask = current_price + .01
    return ask

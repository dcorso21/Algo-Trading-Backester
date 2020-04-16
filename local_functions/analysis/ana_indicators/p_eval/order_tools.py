from local_functions.main import global_vars as gl


cancel_specs = {
    'standard': r'p:%5,t:7'
}

# Order Creation
def smart_order(order_type, cash_value, exe_price, cancel_spec):

    if order_type == 'buy':
        create_orders = create_buys
    else:
        create_orders = create_sells

    chunk = 5000

    if cash_value > chunk:
        divs = cash_value / chunk

    full_order_len = cash_value // chunk

    qs = {'time': 0, 'order_fill': 'x', 'order_cancel': 'x'}

    't:{},f:{},c:{}'.format(qs['time'], qs['order_fill'], qs['order_cancel'])

    order_id = 'x'

    orders = gl.pd.DataFrame()
    for _ in range(full_order_len):
        order = create_orders(chunk, exe_price, cancel_spec, queue_spec)
        order_id = order.at[0, 'order_id']
        orders = orders.append(order, sort=False)

    remainder = cash_value % chunk
    if remainder != 0:
        order = create_orders(remainder, exe_price, cancel_spec, queue_spec)
        orders = orders.append(order, sort=False)

    return orders


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


def create_buys(cash_value, exe_price, cancel_spec, queue_spec):
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
    order_id = gl.order_count + 1

    ticker = current['ticker']
    timestamp = gl.common_ana.get_timestamp(
        current['minute'], current['second'])

    qty = gl.common_ana.cash_to_shares(cash_value, exe_price)
    cash_value = round(qty * exe_price, 2)

    columns = {'ticker': [ticker],
               'order_id': [order_id],
               'send_time': [timestamp],
               'buy_or_sell': ['BUY'],
               'cash': [cash_value],
               'qty': [qty],
               'exe_price': [exe_price],
               'cancel_spec': [cancel_spec],
               'queue_spec': [queue_spec],
               }

    buys = gl.pd.DataFrame(columns)
    return buys


def sell_to_breakeven():
    exe_price = gl.common_ana.get_average()
    qty = gl.current_positions.qty.sum()
    sells = create_sells(qty, exe_price, cancel_specs['standard'])
    return sells


# Price Methods
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
        offset = (current_vola * .01) * current['close']
        exe_price = current['close'] - offset
        return exe_price
    # if candle green...
    exe_price = current['close'] + offset
    return exe_price


def bid_price():
    current_price = gl.current['close']
    bid = current_price - .01
    return bid


def ask_price():
    current_price = gl.current['close']
    ask = current_price + .01
    return ask

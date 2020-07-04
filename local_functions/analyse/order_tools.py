from local_functions.main import global_vars as gl


def cancel_spec_time():
    return gl.configure.master['misc']['cancel_spec_time']


''' ----- Specification Dictionaries ----- '''

cancel_specs = {
    'standard': r'p:%5/5,t:7',
    'target': r'p:${},t:60'
}

renew_spec = {
    'once': 1,
    'standard': 3,
    'persistant': 5
}

''' ----- Order Functions ----- '''


def create_orders(buy_or_sell, cash_or_qty, price_method,
                  auto_renew=0, cancel_spec='standard',
                  queue_spec='nan', parse=False):
    # region Docstring
    '''
    # Create Orders
    Creates an order and splits it into multiple chunks if cash size is too big.
    (only if parse parameter is used) 

    Returns a Dataframe of orders. 

    ## Parameters: {
    ####    `buy_or_sell` : string - 'BUY' or 'SELL'
    ####    `cash_or_qty`: integer. If it is a sell order, put in qty, if buy, put in cash. 
    ####    `price method`: function name. Name way to get execution price. Methods found in `get_exe_price` function
    ####    `auto_renew`: bool - if true, the order will make itself again if cancelled. 
    ####    `cancel_spec`: all cancel specifications are found in the order_tools sheet.  
    ####    `queue_spec`: examples include 'time:4' or 'fill' 
    ####    `parse`: bool - whether or not to break up orders into more manageable chunks.  
    ## }

    ## Process:
    Most of this process is about parsing out orders based on `queue specs`. If `parse` is False, then 
    simply return one order with the `fill_out_order` function. 

    ### Parse Clause:
    If no parsing, then simply return order spec immediately. 
    ### 1) Define chunk size in cash and make convert to shares if order is a sell. 
    '''
    # endregion Docstring
    # Parse Clause:
    if parse == False:
        return fill_out_order(buy_or_sell, cash_or_qty, price_method, auto_renew, cancel_spec, queue_spec)

    # 1) Define chunk size in cash and make convert to shares if order is a sell.
    chunk = 5000
    # convert chunk to shares if order is sell.
    if buy_or_sell == 'SELL':
        chunk = (chunk / gl.current['close'])

    # If the chunk is greater than the order, don't bother parsing.
    if cash_or_qty <= chunk:
        return fill_out_order(buy_or_sell, cash_or_qty, price_method, auto_renew, cancel_spec, queue_spec)
    else:
        # Create first order
        first_order = fill_out_order(
            buy_or_sell, chunk, price_method, auto_renew, cancel_spec, queue_spec)

        # Divs is number of orders not including a remainder.
        divs = (cash_or_qty // chunk)-1
        cashes = [chunk]*divs
        # add the remainder to divs.
        if (cash_or_qty % chunk) != 0:
            cashes = cashes + [cash_or_qty % chunk]

        # cashes is a list of capital/share sizes to make orders with.
        if len(cashes) == 0:
            return first_order

        orders = gl.pd.DataFrame()
        orders = orders.append(first_order, sort=False)

        # Create parses based on fill
        if parse == 'fill':
            for cash in cashes:
                q_spec = f'fill:{gl.order_count}'
                order = fill_out_order(
                    buy_or_sell, cash, price_method, auto_renew, cancel_spec, q_spec)
                orders = orders.append(order, sort=False)
                return orders

        # Create parses based on time
        if parse[0:4] == 'time':
            for num, cash in enumerate(cashes, start=1):
                q_spec = 'time:{}'.format(int(parse.split(':')[1]) * num)
                order = fill_out_order(
                    buy_or_sell, cash, price_method, auto_renew, cancel_spec, q_spec)
                orders = orders.append(order, sort=False)
                return orders


def fill_out_order(buy_or_sell, cash_or_qty, price_method, auto_renew, cancel_spec, queue_spec):
    '''
    ## Fill Out Order
    Convert order specifications into a one-row dataframe. 
    '''
    gl.order_count += 1
    order_id = gl.order_count

    order = {
        'order_id': [order_id],
        'trigger': [gl.sys._getframe(2).f_code.co_name],
        'buy_or_sell': [buy_or_sell],
        'cash_or_qty': [cash_or_qty],
        'price_method': [price_method],
        'auto_renew': [auto_renew],
        'cancel_spec': [cancel_spec],
        'queue_spec': [queue_spec],
    }

    order = gl.pd.DataFrame(order)
    gl.order_specs = gl.order_specs.append(order, sort=False)

    return order


def format_orders(orders):
    '''
    # Format Orders

    Converts order specifications into actual orders. 
    Used after queuing so that the price method is current. 
    '''

    orders = orders.reset_index(drop=True)

    formatted = gl.pd.DataFrame()

    for row in orders.index:
        row = orders.iloc[row]
        info = dict(row)
        order_id, trigger, buy_or_sell, cash_or_qty, p_method, auto_renew, cancel_spec, queue_spec = row

        exe_price = get_exe_price(p_method)
        if ':' not in cancel_spec:
            cancel_spec = get_cancel_spec(cancel_spec, exe_price)
        timestamp = gl.common.get_current_timestamp()
        if buy_or_sell == 'BUY':
            qty = int(cash_or_qty/exe_price)
            cash = round(qty * exe_price, 2)

        if buy_or_sell == 'SELL':
            qty = cash_or_qty
            cash = round(qty * exe_price, 2)

        row = {'ticker': [gl.current['ticker']],
               'order_id': [order_id],
               'send_time': [timestamp],
               'buy_or_sell': [buy_or_sell],
               'cash': [cash],
               'qty': [qty],
               'exe_price': [exe_price],
               'auto_renew': [auto_renew],
               'cancel_spec': [cancel_spec],
               }

        order = gl.pd.DataFrame(row)
        formatted = formatted.append(order, sort=False)
    return formatted


def get_exe_price(method):
    '''
    # Get Execution Price

    master function for retrieving an execution price for any given order. 
    '''

    def current_price():
        return gl.current['close']

    def extrapolate():
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

    def low_placement():
        # if len(gl.mom_frame) != 0:
        #     cur_trend = gl.mom_frame.iloc[-1]
        #     if cur_trend['trend'] == 'uptrend':
        #         if gl.common.candle_is_green():
        #             return current_price()
        #         else:
        #             return extrapolate()
        # get low from last two minutes.
        nearby_low = gl.current_frame.tail(2).low.min()
        dif = abs(gl.current_price() - nearby_low)
        dif = dif / 5
        price = round(nearby_low + dif, 2)
        return price

    def bid_price():
        current_price = gl.current['close']
        bid = current_price - .01
        return bid

    def ask_price():
        current_price = gl.current['close']
        ask = current_price + .01
        return ask

    price_methods = {
        'bid': bid_price,
        'ask': ask_price,
        'extrapolate': extrapolate,
        'current': current_price,
        'low_placement': low_placement,
    }
    # if instead of a method, a price is passed, simply return the price.
    if type(method) != str:
        return method
    return price_methods[method]()


def position_sizer():

    sup_res_frame = gl.sup_res_frame
    mom_frame = gl.mom_frame
    volas = gl.volas
    volumes = gl.volumes
    current = gl.current

    avg = gl.common.current_average()
    exposure = gl.pl_ex['last_ex']

    avail_cap = gl.account.get_available_capital()
    safe_cap = volumes['safe_capital_limit']
    vol_adj_cap = avail_cap * volas['scaler']

    avail_left = avail_cap - exposure
    safe_left = avail_left
    vol_adj_left = vol_adj_cap - exposure

    if safe_cap < avail_cap:
        safe_left = safe_cap - exposure


def make_cancel_spec(ptype: str, p_upper: float, p_lower: float, seconds: int) -> str:
    # region Docstring
    '''
    # Make Cancel Specification
    formats the relevent data into a cancel spec compliant string. 

    #### Returns string of cancel specification for order usage.

    ## Parameters:{
    ####    `ptype`: string, '$' for cash or '%' for percent
    ####    `p_upper`: float, upper bound in price before cancellation
    ####    `p_lower`: float, lower bound in price before cancellation
    ####    `seconds`: int, number of seconds before cancellation
    ## }
    '''
    # endregion Docstring
    return f'p:{ptype}{p_upper}/{p_lower},t:{seconds}'


def cancel_avg_down(pmeth):

    pmeth_price = gl.order_tools.get_exe_price(pmeth)
    spacer = gl.volas['mean']*.01*pmeth_price

    p_upper = max([pmeth_price, gl.current_price()]) + spacer
    p_lower = min([pmeth_price, gl.current_price()]) - spacer
    cancel_spec = make_cancel_spec(ptype='$',
                                   p_upper=p_upper,
                                   p_lower=p_lower,
                                   seconds=cancel_spec_time())
    return cancel_spec


def extrap_average(inv_dol: float, inv_avg: float, new_dol: float, new_price: float):
    extrap_average = ((inv_dol*inv_avg) +
                      (new_dol*new_price))/(inv_dol+new_dol)
    return extrap_average


def get_cancel_spec(method, exe_price):

    def standard_spec():
        higher_price = max([gl.current_price(), exe_price])
        lower_price = min([gl.current_price(), exe_price])
        spacer = gl.volas['mean']*.01*lower_price
        upper = higher_price + spacer
        lower = lower_price - spacer
        spec = make_cancel_spec(ptype='$',
                                p_upper=upper,
                                p_lower=lower,
                                seconds=cancel_spec_time())
        return spec

    def just_abv_avg():
        higher_price = max([gl.current_price(), exe_price])
        lower_price = gl.common.current_average()
        spacer = gl.volas['mean']*.01*lower_price
        upper = higher_price + spacer
        spec = make_cancel_spec(ptype='$',
                                p_upper=upper,
                                p_lower=lower_price,
                                seconds=cancel_spec_time())
        return spec

    def linger20():
        higher_price = max([gl.current_price(), exe_price])
        lower_price = min([gl.current_price(), exe_price])
        spacer = gl.volas['mean']*.01*lower_price
        upper = higher_price + spacer
        lower = lower_price - spacer
        spec = make_cancel_spec(ptype='$',
                                p_upper=upper,
                                p_lower=lower,
                                seconds=20)
        return spec

    methods = {
        'standard': standard_spec,
        'just_abv_avg': standard_spec,
        'linger20': linger20
    }
    return methods[method]()

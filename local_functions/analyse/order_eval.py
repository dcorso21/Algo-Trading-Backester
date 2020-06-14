from local_functions.main import global_vars as gl


def build_orders():
    # region Docstring
    '''
    # Build Orders
    Evaluates Position Data and creates orders for execution

    #### Returns dataframe or empty list

    '''
    # endregion Docstring
    # If there are cancelled orders qualified for refresh,
    # deal with them first
    refreshed = check_auto_refresh()
    if len(refreshed) != 0:
        return refreshed

    # Skip Clause:
    if bad_trade_conds():
        return []

    # if no positions, enter now.
    if len(gl.current_positions) == 0:
        return starting_position()

    # run through all approved sell conditions
    sells = sell_conditions()
    if len(sells) != 0:
        return sells

    # Check to see if a new evaluation is necessary.
    if new_eval_triggered() == False:
        return []

    gl.last_order_check = [gl.current['minute'], gl.current['second']]

    if above_average():
        return order_above_avg()
    else:
        return order_below_avg()


def order_below_avg():
    # region Docstring
    '''
    # Order Below Average
    Decides whether or not to place an order in the case that the price is below the current average.

    # Returns sell orders df or empty list.

    '''
    # endregion Docstring

    max_dur = 10

    acct_size = gl.account.get_available_capital()
    amount_invested = gl.current_positions.cash.sum()
    cur_inv_perc = amount_invested/acct_size
    cp = gl.current_positions
    cf = gl.current_frame.reset_index(drop=True)
    start_ind = cf[cf.time.str.startswith(
        cp.exe_time.to_list()[-1][0:5])].index.values[0]
    # print(cf)
    # print(cf[cf.time == gl.current['minute']])
    cur_ind = cf[cf.time == gl.current['minute']].index.tolist()[0]
    cur_dur = cur_ind-start_ind

    if cur_dur < 2:
        return []

    # first minutes, protect average based on vola and num of minutes only
    if len(gl.mom_frame) == 0:
        # if the current price is less than the average - avg_vola
        if gl.current['close'] < (gl.common.get_average()*(1-(gl.volas['mean']*.01))):
            trend_vola = gl.common.get_volatility([gl.current_frame.high.max()], [
                                                  gl.current_frame.low.min()])[0]

            target_perc = calc_target_perc(
                cur_dur, max_dur, trend_vola)

            if target_perc < cur_inv_perc*1.03:
                return []
            dol_to_inv = (target_perc*acct_size) - amount_invested
            extrap_average = ((amount_invested*gl.common.get_average()) +
                              (dol_to_inv*gl.current['close']))/(dol_to_inv+amount_invested)

            target_average = gl.current['close']*(1 + (gl.volas['mean']*.01))

            if extrap_average > target_average:
                # Potentially sell off or exit
                return order_rebalance(target_average, target_perc)

            buy_or_sell = 'BUY'
            pmeth = 'current'
            cash = dol_to_inv
            cancel_spec = gl.order_tools.make_cancel_spec(ptype='%',
                                                          p_upper=gl.volas['mean'],
                                                          p_lower=gl.volas['mean'],
                                                          seconds=30)

            buy = gl.order_tools.create_orders(buy_or_sell='BUY',
                                               cash_or_qty=cash,
                                               price_method=pmeth,
                                               cancel_spec=cancel_spec)

            gl.log_funcs.log(
                f'buying to average down. Target Perc: {target_perc}')
            return buy
        return []

    current_trend = dict(gl.mom_frame.iloc[-1])
    target_perc = calc_target_perc(
        cur_dur, max_dur, current_trend['volatility'])

    if target_perc < cur_inv_perc*1.03:
        return []
    dol_to_inv = (target_perc*acct_size) - amount_invested
    extrap_average = ((amount_invested*gl.common.get_average()) +
                      (dol_to_inv*gl.current['close']))/(dol_to_inv+amount_invested)

    target_average = gl.current['close']*(1 + (gl.volas['mean']*.01))
    if extrap_average > target_average:
        # Potentially sell off or exit
        return order_rebalance(target_average, target_perc)

    buy_or_sell = 'BUY'
    pmeth = 'current'
    cash = dol_to_inv
    cancel_spec = gl.order_tools.make_cancel_spec(ptype='%',
                                                  p_upper=gl.volas['mean'],
                                                  p_lower=gl.volas['mean'],
                                                  seconds=60)

    gl.log_funcs.log(f'buying to average down. Target Perc: {target_perc}')
    return gl.order_tools.create_orders(buy_or_sell='BUY', cash_or_qty=cash, price_method=pmeth, cancel_spec=cancel_spec)


def calc_target_perc(cur_dur, max_dur, trend_vola):

    # PERC TO INV BASED ON Trend Length
    perc_to_inv = (cur_dur**2/max_dur**2)

    # PERC TO INV BASED ON Volatility
    presumptive_vola = max_dur*gl.volas['mean']
    extrap_vola = (trend_vola/cur_dur)*max_dur
    # take the average of the two estimates.
    extrap_vola = (extrap_vola+presumptive_vola)/2

    vola_perc = trend_vola**2 / extrap_vola**2

    target_perc = max([perc_to_inv, vola_perc])
    return target_perc


def order_rebalance(target_average, target_perc):
    cp = gl.current_positions
    cp['avg'] = cp.qty*cp.exe_price
    options = gl.pd.DataFrame()

    for orders in range(1, len(cp)+1):
        s = cp.tail(orders)
        avg_price = s.avg.sum()/s.qty.sum()
        ret = (gl.current['close'] - avg_price) / avg_price
        unreal = ret*s.cash.sum()
        freed_up = unreal + s.cash.sum()
        available_cap = gl.account.get_available_capital()-cp.cash.sum()+freed_up

        rem_p = cp.head(len(cp)-orders)
        dol_to_inv = target_perc*available_cap-rem_p.cash.sum()

        extrap_average = gl.order_tools.extrap_average(rem_p.cash.sum(),
                                                       rem_p.avg.sum(),
                                                       dol_to_inv,
                                                       gl.current['close'])

        if target_average < extrap_average:
            continue

        else:
            row = {
                'orders': [orders],
                'unreal': [unreal],
                'dol_to_inv': [dol_to_inv],
            }
            row = gl.pd.DataFrame(row)
            options = options.append(row, sort=False)

    if len(options) == 0:
        # sell all
        qty = cp.qty.sum()
        cancel_spec = gl.order_tools.make_cancel_spec(ptype='%',
                                                      p_upper=gl.volas['mean'],
                                                      p_lower=gl.volas['mean'],
                                                      seconds=7)

        return gl.order_tools.create_orders('SELL', qty, 'current', cancel_spec=cancel_spec)

    ind = options[options.unreal == options.unreal.max()].index.tolist()[0]
    option = dict(options.iloc[ind])

    # Buy
    cash = option['dol_to_inv']
    pmeth = 'current'
    cancel_spec = gl.order_tools.make_cancel_spec(ptype='%',
                                                  p_upper=gl.volas['mean'],
                                                  p_lower=gl.volas['mean'],
                                                  seconds=7)

    order = gl.order_tools.create_orders(buy_or_sell='BUY',
                                         cash_or_qty=cash,
                                         price_method='current',
                                         cancel_spec=cancel_spec)

    # Sell
    qty = cp.tail(int(option['orders'])).qty.sum()
    pmeth = 'current'

    cancel_spec = gl.order_tools.make_cancel_spec(ptype='%',
                                                  p_upper=gl.volas['mean'],
                                                  p_lower=gl.volas['mean'],
                                                  seconds=7)
    orders = order.append(
        gl.order_tools.create_orders(buy_or_sell='SELL',
                                     cash_or_qty=qty,
                                     price_method=pmeth,
                                     cancel_spec=cancel_spec)
    )
    gl.log_funcs.log('rebalancing orders')
    return orders


def order_above_avg():

    def assess_safe_percent():
        # region Docstring
        '''
        # Assess Safe Percent
        Dials back the return to shoot for based on amount invested
        
        #### Returns percentage. 
        '''
        # endregion Docstring
        trans_threshold = gl.account.get_available_capital() / 3
        inc = .05*gl.account.get_available_capital()
        safe_perc = 1

        if gl.pl_ex['last_ex'] >= trans_threshold:
            over = gl.pl_ex['last_ex'] - trans_threshold
            divs = over / inc
            safe_perc = 1 - divs*.05
        return safe_perc

    exp_perc_return = (gl.volas['mean'] + gl.common.find_bounce_factor())*.01
    target_percent_return = exp_perc_return * assess_safe_percent()
    exp_cash_return = (exp_perc_return)*gl.pl_ex['last_ex']
    target_cash_return = target_percent_return*gl.pl_ex['last_ex']

    ex_price = gl.current['close'] * (1+target_percent_return)
    qty = gl.current_positions.qty.sum()
    upper_cancel = ex_price*(1+target_percent_return)
    cancel_spec = gl.order_tools.make_cancel_spec(ptype='%',
                                                p_upper=upper_cancel,
                                                p_lower=gl.common.get_average(),
                                                seconds=30)

    sells = gl.order_tools.create_orders(buy_or_sell='SELL',
                                        cash_or_qty=qty,
                                        price_method=ex_price,
                                    cancel_spec=cancel_spec)
    return sells


def starting_position():
    # region Docstring
    '''
    # Starting Position
    Creates buy order with one percent of available capital.  

    Returns buys DataFrame.

    # Parameters:{
    # All Parametes are controlled in `local_functions.main.configure`
    # }

    '''
    # endregion Docstring
    if gl.chart_response == True:
        cash = gl.account.get_available_capital() * .01
        pmeth = 'ask'
        buys = gl.order_tools.create_orders('BUY', cash, pmeth)
        gl.log_funcs.log('---> Sending Starting Position.')
        return buys
    return gl.pd.DataFrame()


def check_auto_refresh():
    # region Docstring
    '''
    # check_auto_refresh
    Checks to see if there are cancelled orders that can be autorefreshed.

    # Process:

    # 1) Retrieves cancelled order ids.
    - These orders will be dropped from the cancelled_orders frame to
    avoid repetition.

    # 2) Retrieves cash or qty values based on order type.
    # 3) Decrease auto-renew value by one for new orders.
    # 4) Return Renewed Orders

    '''
    # endregion Docstring
    cancelled = gl.cancelled_orders
    if len(cancelled) != 0:
        cancelled = cancelled[cancelled.status == 'successfully cancelled']

    if len(cancelled) == 0:
        return []

    # 1) Retrieves cancelled order ids.
    need_renew = cancelled[cancelled['auto_renew'] > 0]
    refresh_ids = need_renew.order_id.to_list()

    if len(refresh_ids) == 0:
        return []

    # ~ is used to negate statement. So cancelled orders are orders that are NOT being refreshed
    gl.cancelled_orders = cancelled[~cancelled.order_id.isin(refresh_ids)]

    need_renew = need_renew.reset_index(drop=True)
    need_renew = need_renew.sort_values(by='order_id')

    cash_or_qty = []
    for index in range(len(need_renew)):
        if need_renew.at[index, 'buy_or_sell'] == 'BUY':
            cash_or_qty.append(need_renew.at[index, 'cash'])
        else:
            cash_or_qty.append(need_renew.at[index, 'qty'])

    o_specs = gl.order_specs
    refresh_df = gl.pd.DataFrame()
    for order_id in need_renew.order_id:
        row = o_specs[o_specs.order_id == order_id].head(1)
        refresh_df = refresh_df.append(row, sort=False)

    # refresh_df = gl.order_specs[gl.order_specs.order_id.isin(refresh_ids)]
    refresh_df = refresh_df.reset_index(drop=True)
    refresh_df = refresh_df.sort_values(by='order_id')

    # 2) Retrieves cash or qty values based on order type.

    # 3) Decrease auto-renew value by one for new orders.
    refresh_df['auto_renew'] = need_renew['auto_renew'] - 1
    refresh_df['cash_or_qty'] = cash_or_qty

    gl.log_funcs.log('refreshing order(s): {}'.format(
        refresh_df.order_id.to_list()))

    # 4) Return Renewed Orders
    return refresh_df


def bad_trade_conds():
    # region Docstring
    '''
    # Check for Bad Trade Conditions
    Checks to see if certain conditions are met

    Returns a True/False Value. TRUE means the conditions are bad for trading (this second)

    # Conditions:
    # 1) If there are Open Orders --> return True

    # 2) if there are NO Current Positions AND the chart response is Bad (False) ---> return True
    '''
    # endregion Docstring

    if len(gl.open_orders) != 0:
        return True

    if (len(gl.current_positions) == 0) and (gl.chart_response == False):
        return True

    return False


def sell_conditions():
    # region Docstring
    '''
    # Sell Conditions

    #### Returns sell orders if conditions are met. 
    '''
    # endregion Docstring
    s_params = gl.configure.master['sell_conditions']

    def dollar_risk_check():
        # region Docstring
        '''
        # Dollar Risk Check
        ## Sell Condition 
        Checks to see if the unreal and real add up to the risk amount noted in conditions. 
        '''
        # endregion Docstring
        d_risk = gl.pl_ex['unreal'] + gl.pl_ex['unreal']
        if d_risk <= gl.configure.misc['dollar_risk']:
            everything = gl.current_positions.qty.sum()
            exe_price = 'current'
            sells = gl.order_tools.create_orders(
                'SELL', everything, exe_price, auto_renew=5)
            gl.log_funcs.log('----> dollar risk triggered, selling all.')
            return sells
        return []

    def percentage_gain():
        # region Docstring
        '''
        # Percentage_Gain
        A Sell Condition function that will create a sell order based on a percentage gain of `current_positions` overall.  

        Returns a DataFrame of Sell Orders. 
        '''
        # endregion Docstring
        avg = gl.common.get_average()
        perc = s_params['percentage_gain']['perc_gain']
        if gl.current['close'] >= (avg * (1 + .01 * perc)):
            # sell all
            everything = gl.current_positions.qty.sum()
            exe_price = 'bid'
            sells = gl.order_tools.create_orders('SELL', everything, exe_price)
            gl.log_funcs.log('----> over 3 perc gain triggered.')
            return sells
        sells = gl.pd.DataFrame()
        return sells

    def target_unreal():
        # region Docstring
        '''
        # Target_Unreal
        ## Sell Condition 
        Looks at current unreal PL and if it gets over a certain amount, creates sell order(s). 

        Returns DataFrame of Sell Orders. 
        '''
        # endregion Docstring
        target_unreal_amount = s_params['target_unreal']['target_unreal_amount']
        unreal = gl.pl_ex['unreal']
        if unreal >= target_unreal_amount:
            # sell all
            qty = gl.current_positions.qty.sum()
            exe_price = 'bid'
            sells = gl.order_tools.create_orders('SELL', qty, exe_price)
            gl.log_funcs.log(f'----> unreal hits trigger: {unreal}')
            return sells
        return []

    def exposure_over_account_limit():
        # region Docstring
        '''
        # exposure_over_account_limit
        # Sell Condition 
        Looks at current exposure and if it gets over the account limit, creates sell order(s). 

        Returns DataFrame of Sell Orders. 

        # Parameters:{
        # All Parametes are controlled in `local_functions.main.configure`
        # }

        '''
        # endregion Docstring
        available_capital = gl.account.get_available_capital()
        exposure = gl.pl_ex['last_ex']
        if exposure > available_capital:
            qty = int(gl.current_positions.qty.sum()/2)
            exe_price = 'bid'
            sells = gl.order_tools.create_orders('SELL', qty, exe_price)
            gl.log_funcs.log(f'----> over-exposed ({exposure}) sell half.')
            return sells
        return []

    def timed_exit():
        # region Docstring
        '''
        # Timed Exit
        # Sell Condition
        If the current minute is 11:00:00, then sell EVERYTHING. 

        Returns a Sells DataFrame

        # Parameters:{
        # All Parametes are controlled in `local_functions.main.configure`
        # }
        '''
        # endregion Docstring
        minute_off = s_params['timed_exit']['minute_offset']
        exit_time = gl.configure.misc['hard_stop']
        exit_time = gl.pd.to_datetime(exit_time)
        exit_time = (
            exit_time - gl.datetime.timedelta(minutes=minute_off)).timestamp()

        current_time = gl.current['minute']
        current_time = gl.pd.to_datetime(current_time).timestamp()

        if (current_time >= exit_time) or (gl.sell_out == True):
            qty = gl.current_positions.qty.sum()
            pmethod = 'bid'
            sells = gl.order_tools.create_orders(
                'SELL', qty, pmethod, auto_renew=5)

            gl.log_funcs.log('Sell to Stop...')
            gl.buy_lock = True
            gl.sell_out = True
        else:
            sells = gl.pd.DataFrame()
        return sells

    def sell_at_breakeven():
        if outlook_score() < 50:
            ex_price = gl.common.get_average()
            qty = gl.current_positions.qty.sum()
            upper_cancel = ex_price*(1+gl.volas['mean'])
            lower_cancel = ex_price*(1-gl.volas['mean'])
            cancel_spec = gl.order_tools.make_cancel_spec(ptype='%',
                                                        p_upper=upper_cancel,
                                                        p_lower=lower_cancel,
                                                        seconds=30)

            sells = gl.order_tools.create_orders(buy_or_sell='SELL',
                                                cash_or_qty=qty,
                                                price_method=ex_price,
                                                cancel_spec=cancel_spec)
            return sells
        return []
    up_conds = {
        'percentage_gain': percentage_gain,
        'target_unreal': target_unreal,
    }
    down_conds = {
        'dollar_risk_check': dollar_risk_check,
    }
    universal_conds = {
        'exposure_over_account_limit': exposure_over_account_limit,
        'timed_exit': timed_exit,
    }

    relevant_conds = universal_conds
    additional_conds = down_conds
    if gl.current['close'] > gl.common.get_average():
        additional_conds = up_conds

    for cond in additional_conds:
        relevant_conds[cond] = additional_conds[cond]

    approved_conds = gl.configure.sell_conditions

    for condition in approved_conds:
        if condition not in relevant_conds:
            continue
        sells = relevant_conds[condition]()
        if len(sells) != 0:
            gl.log_funcs.log_sent_orders(sells, 'SELL')
            break
    return sells


def new_eval_triggered():
    cp = gl.current_positions
    last_price = cp.exe_price.values[0]
    upper_bound = last_price*(1+(gl.volas['mean']*.01))
    lower_bound = last_price*(1-(gl.volas['mean']*.01))
    if gl.current['close'] > upper_bound:
        gl.log_funcs.log(msg='order eval triggered by price drop')
        return True
    elif gl.current['close'] < lower_bound:
        gl.log_funcs.log(msg='order eval triggered by price rise')
        return True

    # last_trade_time = cp.exe_time.values[0]
    last_check_time = gl.common.get_timestamp(*gl.last_order_check)
    current_time = gl.common.get_timestamp(
        gl.current['minute'], gl.current['second'])
    current_time = gl.pd.to_datetime(current_time).timestamp()
    last_trade_time = gl.pd.to_datetime(last_check_time).timestamp()
    since_last_trade = current_time - last_trade_time
    if since_last_trade > 30:
        return True
    return False


def above_average() -> bool:
    if gl.current['close'] > gl.common.get_average():
        return True
    return False


def outlook_score():
    score = 0
    deduct = 0

    # Based on current duration of investment,
    score +=1
    inv_duration = gl.common.investment_duration()
    if inv_duration > 10:
        deduct -= 1

    # Based on current trend
    score +=1
    current_trend = dict(gl.mom_frame.iloc[-1])
    if (current_trend['duration'] > 10) and (current_trend['trend'] == 'downtrend'):
        deduct -= 1

    # proximity to average.
    avg = gl.common.get_average()
    perc_from_avg = ((gl.current['close'] - avg)/avg)*100

    score +=1
    vola = gl.volas['mean']
    if len(gl.current_frame) >= 10:
        vola = gl.volas['ten_min']
    if perc_from_avg < (-1*vola):
        deduct -= 1

    score +=1
    cur_ret = gl.common.daily_return()
    if cur_ret < 0:
        deduct -= 1

    score +=1
    bounce_factor = gl.common.find_bounce_factor()
    if bounce_factor < 0:
        deduct -= 1

    return ((score + deduct)/score)*100


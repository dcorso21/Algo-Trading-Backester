from local_functions.main import global_vars as gl


def build_orders():
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


    if strat_exceptions():
        return []
    if above_average():
        return look_to_profit()
    else:
        return look_to_avg_down()


'''-------------------- Strategies --------------------'''

def strat_exceptions():
    st_conds = {
        'pos_sec_mom': gl.sec_mom > 0,
        'neg_sec_mom': gl.sec_mom < 0,
    }

    for s in strat_vars['strat_conds']:
        if st_conds[s]:
            return True

    return False


'''-------------------- Order Makers --------------------'''


def starting_position():
    order = gl.strategy['starting_position']
    buys = gl.order_tools.create_orders(**order)
    gl.log_funcs.log('>>> Sending Starting Position.')
    return buys


def look_to_avg_down():
    # region Docstring
    '''
    # Order Below Average
    Decides whether or not to place an order in the case that the price is below the current average.

    # Returns sell orders df or empty list.

    '''
    # endregion Docstring
    return look_to_rebalance()

    acct_size = gl.account.get_available_capital()
    amount_invested = gl.current_positions.cash.sum()
    cur_dur = gl.common.investment_duration()

    # first minutes, protect average based on vola and num of minutes only
    if len(gl.mom_frame) == 0:
        trend_vola = gl.common.get_volatility([gl.current_frame.high.max()], [
            gl.current_frame.low.min()])[0]
    else:
        current_trend = dict(gl.mom_frame.iloc[-1])
        trend_vola = current_trend['volatility']

    dol_to_inv = calc_dol_to_inv(cur_dur,
                                 strat_vars['max_dur'],
                                 trend_vola)

    if dol_to_inv == 0:
        return []

    elif dol_to_inv == 'rebalance':
        gl.log_funcs.log(msg='special circumstances, rebalancing now.')
        return look_to_rebalance()

    # Price Extrap
    extrap_average = ((amount_invested*gl.common.current_average()) +
                      (dol_to_inv*gl.current['close']))/(dol_to_inv+amount_invested)

    if extrap_avg_too_far_away(extrap_average):
        gl.log_funcs.log(msg='Average too far away, redirecting')
        return look_to_rebalance()

    target_perc = ((cash + amount_invested)/acct_size)*100
    gl.log_funcs.log(f'>>> Average Down Triggered: Target Perc: {target_perc}')
    return gl.order_tools.create_orders(buy_or_sell='BUY',
                                        cash_or_qty=dol_to_inv,
                                        price_method='low_placement',
                                        cancel_spec='standard')


def look_to_profit():
    amount_invested = gl.current_positions.cash.sum()
    acct_size = gl.account.get_available_capital()

    target_perc_ret = target_perc_return()

    if gl.common.current_return() < target_perc_ret:
        return []

    if amount_invested < .05 * acct_size and gl.common.investment_duration() < 1:
        if gl.common.current_return() <= target_perc_ret*1.5:
            gl.log_funcs.log(msg='Not enough invested to sell, holding.')
            return []

    qty = gl.current_positions.qty.sum()
    sells = gl.order_tools.create_orders(buy_or_sell='SELL',
                                         cash_or_qty=qty,
                                         price_method='bid',
                                         cancel_spec='just_abv_avg')

    gl.log_funcs.log('>>> Selling Above Average')
    return sells


def look_to_rebalance():
    target_average = target_avg()
    if str(target_average) == 'nan':
        return []
    amt_inv = gl.common.current_exposure()
    inv_dur = gl.common.investment_duration()
    avg = gl.common.current_average()
    acct_size = gl.account.get_available_capital()
    available_cap = acct_size - amt_inv

    dol_to_inv = amt_inv*(avg - target_average) / \
        (target_average - gl.current_price())

    if dol_to_inv <= acct_size * .01:
        return []

    elif dol_to_inv > available_cap:
        cap_to_sell = dol_to_inv - available_cap
        shares_to_sell = cap_to_sell / gl.order_tools.get_exe_price('ask')
        if shares_to_sell > gl.current_positions.qty.sum():
            return panic_out()
        gl.log_funcs.log('>>> Selling to Rebalance.')
        order = gl.order_tools.create_orders(buy_or_sell='SELL',
                                             cash_or_qty=shares_to_sell,
                                             price_method='ask')
        return order

    order = gl.order_tools.create_orders(buy_or_sell='BUY',
                                         cash_or_qty=dol_to_inv,
                                         price_method='low_placement')
    gl.log_funcs.log('>>> Closing Gap on Average.')
    return order


def sell_conditions():
    s_params = gl.configure.master['sell_conditions']

    def dollar_risk_check():
        d_risk = gl.pl_ex['unreal'] + gl.pl_ex['unreal']
        if d_risk <= gl.configure.misc['dollar_risk']:
            everything = gl.current_positions.qty.sum()
            pmeth = 'current'
            sells = gl.order_tools.create_orders(buy_or_sell='SELL',
                                                 cash_or_qty=everything,
                                                 price_method=pmeth)
            gl.log_funcs.log('>>> Dollar Risk Sell Triggered')
            return sells
        return []

    def percentage_gain():
        avg = gl.common.current_average()
        perc = s_params['percentage_gain']['perc_gain']
        target_price = avg * (1 + (.01 * perc))
        if gl.current_price() >= target_price:
            everything = gl.current_positions.qty.sum()
            exe_price = 'bid'
            sells = gl.order_tools.create_orders('SELL', everything, exe_price)
            gl.log_funcs.log('>>> Percentage Gain Sell Triggered')
            return sells
        return []

    def target_unreal():
        target_unreal_amount = s_params['target_unreal']['target_unreal_amount']
        unreal = gl.pl_ex['unreal']
        if unreal >= target_unreal_amount:
            if gl.common.investment_duration() < 5:
                return
            qty = gl.current_positions.qty.sum()
            exe_price = 'bid'
            sells = gl.order_tools.create_orders(
                'SELL', qty, exe_price, auto_renew=3)
            gl.log_funcs.log(f'>>> Target Unreal Sell Triggered')
            return sells
        return []

    def exposure_over_account_limit():
        available_capital = gl.account.get_available_capital()
        exposure = gl.common.current_exposure()
        if exposure > available_capital:
            qty = int(gl.current_positions.qty.sum()/2)
            exe_price = 'bid'
            sells = gl.order_tools.create_orders('SELL', qty, exe_price)
            gl.log_funcs.log(f'>>> Over-Exposure Sell Triggered')
            return sells
        return []

    def timed_exit():
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
                'SELL', qty, pmethod)

            gl.log_funcs.log('Sell to Stop...')
            gl.buy_lock = True
            gl.sell_out = True
            return sells
        return []

    def bad_differentials():
        if gl.volumes['differential'] == 'nan':
            return []
        if gl.volumes['differential'] <= -.50:
            gl.log_funcs.log('>>> Steep Volume Dropoff, redirect to sell')
            gl.buy_lock = True
            gl.sell_out = True
            return panic_out()
        elif gl.volas['differential'] <= -.50:
            gl.log_funcs.log('>>> Steep Volatility Dropoff, redirect to sell')
            gl.buy_lock = True
            gl.sell_out = True
            return panic_out()
        else:
            return []

    def out_of_steam():
        if gl.common.dur_since_last_trade() < 1:
            return []
        if gl.common.bounce_factor() < 0:
            if gl.volumes['minimum'] < gl.config['misc']['minimum_volume']:
                gl.log_funcs.log(
                    '>>> Out of Steam, bad volume and bounce factor, redirect to sell')
                return panic_out()
        return []

    def four_red_candles():
        cf = gl.current_frame.tail(7)
        cf = cf.drop(cf.index.values[-1])
        cf['red_candle'] = 0
        cf.loc[(cf.open.values > cf.close.values), 'red_candle'] = 1
        four_red = cf.rolling(4).red_candle.sum().max()
        if four_red >= 4:
            four_red = True

        if four_red == True:
            # See if the price is still going down
            if gl.current['low'] > gl.current_frame.tail(2).low.values[0]:
                gl.log_funcs.log(
                    '>>> Four red candles in a row, waiting to see what happens')
                return []
            else:
                gl.log_funcs.log(
                    '>>> Four red candles in a row. Reroute to sell')
                qty = gl.current_positions.qty.sum()
                ex_price = gl.common.current_average()
                if not above_average():
                    ex_price = 'bid'
                elif gl.current_price() > gl.common.current_average()*(1+gl.volas['mean']*.01):
                    ex_price = 'current'
                sells = gl.order_tools.create_orders(buy_or_sell='SELL',
                                                     cash_or_qty=qty,
                                                     price_method=ex_price)
                return sells
        return []

    def breakeven():
        # If the outlook doesn't look good, and if the price is close to the average
        spacer = gl.volas['mean']*.01*.3*gl.current_price()
        if outlook_score() < 50 and abs(gl.current_price()-gl.common.current_average()) <= spacer:
            ex_price = gl.common.current_average()
            qty = gl.current_positions.qty.sum()
            sells = gl.order_tools.create_orders(buy_or_sell='SELL',
                                                 cash_or_qty=qty,
                                                 price_method=ex_price)
            gl.log_funcs.log(
                f'>>> Breakeven Sell Triggered: outlook score: {outlook_score()}')
            return sells
        return []

    def quit_early():
        if outlook_score() == 0:
            gl.log_funcs.log(
                msg='>>> Quit Early Triggered, redirect to panic out')
            return panic_out()
        return []

    up_conds = {
        'percentage_gain': percentage_gain,
        'target_unreal': target_unreal,
        'breakeven': breakeven,
    }
    down_conds = {
        'dollar_risk_check': dollar_risk_check,
        'breakeven': breakeven,
        'out_of_steam': out_of_steam,
    }
    universal_conds = {
        'four_red_candles': four_red_candles,
        'bad_differentials': bad_differentials,
        'exposure_over_account_limit': exposure_over_account_limit,
        'timed_exit': timed_exit,
        'quit_early': quit_early,
    }

    relevant_conds = universal_conds
    additional_conds = down_conds
    if gl.current_price() > gl.common.current_average():
        additional_conds = up_conds

    for cond in additional_conds:
        relevant_conds[cond] = additional_conds[cond]

    approved_conds = gl.configure.sell_conditions

    for condition in approved_conds:
        if condition not in relevant_conds.keys():
            continue
        sells = relevant_conds[condition]()
        if len(sells) != 0:
            break
    return sells


'''-------------------- Other --------------------'''


def target_perc_return():
    # Bounce Factor is weighted as 1/3 of volatility
    exp_perc_return = (gl.volas['mean']*.80 +
                       gl.common.bounce_factor()*.33)*1*.01
    target_percent_ret = exp_perc_return * safe_percent()
    return target_percent_ret


def extrap_avg_too_far_away(extrap_average):
    target_average = target_avg()
    spacer_vola = max(
        [gl.volas['mean'], gl.volas['current'], gl.volas['five_min']])
    spacer = (spacer_vola)*.01*gl.current_price()
    return extrap_average > (target_average+spacer)


def panic_out():
    pmeth = 'bid'
    qty = gl.current_positions.qty.sum()
    order = gl.order_tools.create_orders(buy_or_sell='SELL',
                                         cash_or_qty=qty,
                                         price_method=pmeth
                                         )
    gl.log_funcs.log(msg='>>> Panic Out Sell Triggered')
    return order


def try_for_low(dol_to_inv):
    order = gl.order_tools.create_orders(buy_or_sell='BUY',
                                         cash_or_qty=dol_to_inv,
                                         price_method='low_placement',
                                         cancel_spec='linger20')
    return order


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


def new_eval_triggered():
    # If there is only a starting position, then keep on the lookout.
    # if len(gl.current_positions) == 1:
    #     reset_last_order_check()
    #     return True

    # If there hasn't been an order check yet, then it will be a str
    # Then reset last order check
    last_price = gl.last_order_check[-1]
    if type(last_price) == str:
        reset_last_order_check()
        return True

    # upper_bound = last_price*(1+(gl.volas['mean']*.01))
    lower_bound = last_price*(1-(gl.volas['mean']*.01))

    if gl.current_price() < lower_bound:
        gl.log_funcs.log(msg='order eval triggered by price swing')
        reset_last_order_check()
        return True

    minute, second, _ = gl.last_order_check
    last_check_time = gl.common.get_timestamp(minute, second, integer=True)
    current_time = gl.common.get_current_timestamp(integer=True)
    since_last_trade = current_time - last_check_time

    if since_last_trade > gl.config['misc']['buy_clock_countdown_amount']:
        reset_last_order_check()
        return True

    return False


def reset_last_order_check():
    gl.last_order_check = [gl.current['minute'],
                           gl.current['second'],
                           gl.current_price()
                           ]


def above_average() -> bool:
    if gl.current_price() > gl.common.current_average():
        return True
    return False


def outlook_score():
    score = 0
    deduct = 0

    if fail_flags():
        return 0

    # Based on current duration of investment,
    score += 1
    inv_duration = gl.common.investment_duration()
    if inv_duration > 10:
        deduct -= 1

    # Based on current trend
    score += 1
    if len(gl.mom_frame) != 0:
        current_trend = dict(gl.mom_frame.iloc[-1])
        if (current_trend['duration'] > 10) and (current_trend['trend'] == 'downtrend'):
            deduct -= 1

    # proximity to average.
    avg = gl.common.current_average()
    perc_from_avg = ((gl.current['close'] - avg)/avg)*100

    score += 1
    vola = gl.volas['mean']
    if len(gl.current_frame) >= 10:
        vola = gl.volas['ten_min']
    if perc_from_avg < (-1*vola):
        deduct -= 1

    score += 1
    cur_ret = gl.common.daily_return()
    if cur_ret < 0:
        deduct -= 1

    score += 1
    bounce_factor = gl.common.bounce_factor()
    if bounce_factor < 0:
        deduct -= 1

    final_score = ((score + deduct)/score)*100
    return final_score


def fail_flags():
     # If volume has depleted significantly, then get out
    if gl.volumes['fail_check'] == True:
        return True
    return False


def calc_dol_to_inv(cur_dur, max_dur, trend_vola):
    # Check to see if the exposure is on track.
    # To do this, see what the exposure would have been 2 mins ago.
    low_est = 0
    if cur_dur > 3:
        low_est = calc_dol_to_inv(cur_dur - 2, max_dur, trend_vola)
        if low_est == 'rebalance':
            return 'rebalance'

    amount_invested = gl.common.current_exposure()
    if amount_invested < low_est:
        return 'rebalance'
    acct_size = gl.account.get_available_capital()
    max_possible = round(acct_size - amount_invested, 2)

    exp = 1.7

    # PERC TO INV BASED ON Trend Length
    perc_to_inv = (cur_dur**exp/max_dur**exp)

    # PERC TO INV BASED ON Volatility
    presumptive_vola = max_dur*gl.volas['mean']
    extrap_vola = (trend_vola/cur_dur)*max_dur

    # take the average of the two estimates.
    extrap_vola = (extrap_vola+presumptive_vola)/2

    vola_perc = trend_vola**exp / extrap_vola**exp
    target_perc = max([perc_to_inv, vola_perc])

    dol_to_inv = (target_perc*acct_size) - amount_invested
    dol_to_inv = min([dol_to_inv, max_possible])

    minimum_dol_amount = max([.05 * amount_invested, acct_size*.01])
    if dol_to_inv < minimum_dol_amount:
        return 0
    return dol_to_inv


def target_avg():
    price = gl.current_price()
    return price + ((.01*gl.volas['mean'])/10)*price


@ gl.log_funcs.tracker
def safe_percent():
    # region Docstring
    '''
    # Assess Safe Percent
    Dials back the return to shoot for based on amount invested
    #### Returns percentage. 
    '''
    # endregion Docstring

    trans_threshold = gl.account.get_available_capital() / 3
    inv_dur = gl.common.investment_duration()
    inc = .05*gl.account.get_available_capital()
    safe_perc = 1

    if gl.pl_ex['last_ex'] >= trans_threshold:
        over = gl.pl_ex['last_ex'] - trans_threshold
        divs = over / inc
        safe_perc = 1 - divs*.05
    if inv_dur > 3:
        if inv_dur > strat_vars['max_dur']:
            return 0
        safe_perc = safe_perc * (1 - (inv_dur/strat_vars['max_dur']))

    return safe_perc

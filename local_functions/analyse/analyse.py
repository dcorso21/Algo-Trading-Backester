from local_functions.main import global_vars as gl


def analyse():
    # Skip Clause ---
    if gl.buy_lock == True:
        if len(gl.current_positions) == 0:
            gl.loop_feedback = False
            return []

    # 1) Analyse Daily Chart - Only when there has been an update...
    if (str(gl.current) != str(gl.last)) | (gl.current['second'] == 59):
        gl.update_docs.update_files()
        # only necessary to evaluate if there are no current positions.
        if len(gl.current_positions) == 0:
            day_eval()

    # 2) Build Orders
    set_strategy_mode()
    orders = gl.order_eval.build_orders()
    gl.log_funcs.log_sent_orders(orders)

    return orders


def set_strategy_mode():
    new_strategy_mode = False
    if len(gl.current_frame) <= 5:
        mode = 'market_open_chaos'
    else:
        if str(gl.close_sup_res[0]) == 'nan':
            mode = 'free_fall'
        elif str(gl.close_sup_res[1]) == 'nan':
            mode = 'breakout_to_new_highs'
        else:
            mode = 'consolidate'
    if mode != gl.strategy_mode:
        gl.log_funcs.log(f'New Trade Mode: {mode}')
        new_strategy_mode = True
    gl.strategy_mode = mode

    if new_strategy_mode:
        strategy_modes = {
            'market_open_chaos': market_open_chaos,
            'consolidate': consolidate,
            'breakout_to_new_highs': breakout_to_new_highs,
            'free_fall': free_fall,
        }
        strategy_modes[gl.strategy_mode]()


'''----- Day Analysis -----'''


def day_eval():
    if good_time_to_stop():
        gl.common.stop_trading()
        return

    strat_eval()

def strat_eval():
    def bounce_found():
        if sequential_candles('red', 4, 4):
            if gl.current['open'] < gl.current_price():
                return True
        return False

    strategies = [bounce_found]
    strategy_names = {
        'bounce_found': bounce_found
    }
    for s in strategies:
        if s():
            gl.strategy = strategy_names[s]
            gl.chart_response = True
            return


def pricing_evaluations(method):
    def closer_to_low_than_open():
        df = gl.current_frame
        day_open = df.open.to_list()[0]
        low = df.low.min()
        c_price = gl.current_price()

        # If the price is less than open...
        if c_price < day_open:
            # If the price is closer to the low than the high price.
            if (day_open - c_price) > (c_price - low):
                # gl.logging.info('chart looks good via ana_first_mins')
                return True
        return False

    def volatile_downtrend():
        mom_frame = gl.mom_frame
        if len(mom_frame) == 0:
            return False
        last_index = mom_frame.index.to_list()[-1]
        trend = mom_frame.at[last_index, 'trend']
        vola = mom_frame.at[last_index, 'volatility']
        if (trend == 'downtrend') and (vola > 5): 
            # gl.logging.info('chart looks good via vola_downtrend')
            return True
        return False

    def bottom_of_candle():
        current = gl.current
        if current['second'] >= 30:
            if (current['close'] - current['low']) < (current['high'] - current['close']):
                return True
            return False

        df = gl.current_frame.tail(2)
        low = df.low.min()
        high = df.high.max()
        # If the distance from the price to the high is greater than the distance from the price to the low.
        # In other words, if price is closer to low than high.
        if (current['close'] - low) < (high - current['close']):
            return True
        return False

    methods = {
        'closer_to_low_than_open': closer_to_low_than_open,
        'volatile_downtrend': volatile_downtrend,
        'bottom_of_candle': bottom_of_candle,
    }

    return methods[method]()

def sequential_candles(color, num_candles, min_period, exponential=False, include_current=False):
    cf = gl.current_frame.tail(min_period)
    if not include_current:
        cf = cf.drop(cf.index.values[-1])
        if len(cf) == 0:
            return False 
    cf['seq'] = 0
    if color == 'red':
        cf.loc[(cf.open.values > cf.close.values), 'seq'] = 1
    else:
       cf.loc[(cf.open.values < cf.close.values), 'seq'] = 1
    max_seq = cf.rolling(num_candles).red_candle.sum().max()
    if max_seq >= num_candles:
        return True
    return False

def day_volume_analysis_methods(method):
    dvol_min = gl.config['misc']['minimum_volume']

    def worth_trading():
        current_frame = gl.current_frame
        current_frame['dvol'] = current_frame.close.values * \
            current_frame.volume.values

        dvol = current_frame.dvol.astype(float).tolist()
        # don't want to base this on current minute.
        del dvol[-1]

        if min(dvol) >= dvol_min:
            return True
        return False

    def early_exrap():
        sec = gl.current['second']
        cur_dvol = gl.current_frame.volume.values[-1]*gl.current['close']
        extrap = (cur_dvol/(sec+1))*60
        if extrap >= dvol_min:
            return True
        return False

    methods = {
        'worth_trading': worth_trading,
        'early_extrap': early_exrap
    }

    return methods[method]()


def good_time_to_stop():
    # Rule out trading if unnacceptable amount is already lost.
    if gl.pl_ex['real'] <= gl.configure.misc['dollar_risk']:
        # gl.common.stop_trading()
        gl.log_funcs.log('dollar risk hit: trading stopped')
        return True

    # Rule Out trading if not enough Volume
    if gl.config['misc']['volume_check']:
        if len(gl.current_frame) < 2:
            if not day_volume_analysis_methods('early_extrap'):
                return False
        else:
            if not day_volume_analysis_methods('worth_trading'):
                # gl.common.stop_trading()
                gl.log_funcs.log('insufficient volume: trading stopped')
                return True

    if gl.common.mins_left() <= gl.config['misc']['lookahead_mins']:
        # gl.common.stop_trading()
        gl.log_funcs.log('insufficient time: trading stopped')
        return True
    return False

'''----- Year Analysis -----'''

from local_functions.main import global_vars as gl


def get_volatility(high_list, low_list, convert=False) -> list:
    # region Docstring
    '''
    ## Get Volatility
    Takes high and low lists and makes a list of volatilities based on the highs and lows. 

    returns numpy array of volatilities. 
    '''
    # endregion Docstring
    if convert:
        def convert_high(high):
            if type(high) == list:
                return max(high)
            return high
        def convert_low(low):
            if type(low) == list:
                return min(low)
            return low
        high_list = [convert_high(high) for high in high_list]
        low_list = [convert_low(low) for low in low_list]
    highs = gl.np.array(high_list)
    lows = gl.np.array(low_list)
    vola = gl.np.around((((highs - lows) / lows)*100), decimals=1)
    return vola


def red_green():
    # region Docstring
    '''
    ## Red Green Analysis
    Makes a list with a value for each candle to represent if it was red or green.

    Returns red/green list.   
    '''
    # endregion Docstring

    cf = gl.current_frame   # copy frame
    # create a new column for r/g values with doji as the default.
    cf['r_g'] = 'doji'
    cf.loc[(cf['open'].values < cf['close'].values),
           'r_g'] = 'green'   # define which rows are green
    cf.loc[(cf['open'].values > cf['close'].values),
           'r_g'] = 'red'     # define which rows are red
    return cf.r_g.tolist()  # returns list.


def center_point():
    cf = gl.current_frame   # copy frame
    cf['center'] = cf.high.values - cf.low.values
    return cf.center


def cash_to_shares(cash, price):
    # region Docstring
    '''
    # Cash to Shares
    Takes cash amount and execution price and calculates how many shares to buy. 

    returns share quantity. 
    '''
    # endregion Docstring

    share_quantity = (int(cash/price))
    return share_quantity


def get_timestamp(minute, second, integer=False):
    # region Docstring
    '''
    ## Get TimeStamp
    Takes a minute string and a second integer and creates a timestamp down to the second. 

    Returns a string in the format '%H:%M:%S'

    ### Parameters: {

    minute: string value in the '%H:%M:%S' format

    second: integer value to offset the minute value by. 

    }
    '''
    # endregion Docstring

    from datetime import datetime, timedelta
    time = datetime.strptime(minute, '%H:%M:%S')
    time = time+timedelta(seconds=second)
    time = time.strftime('%H:%M:%S')
    if integer:
        return gl.pd.to_datetime(time).timestamp()
    return time


def get_current_timestamp(integer=False):
    if integer:
        return get_timestamp(gl.current['minute'], gl.current['second'], integer=integer)
    return make_timestamp(gl.current['minute'], gl.current['second'])


def make_timestamp(minute: str, second: int):
    sec = str(second)
    if len(sec) == 1:
        sec = f'0{sec}'
    return minute[:6]+sec


def current_average(new_avg=False):
    # region Docstring
    '''
    ## Get Average
    Returns the average price of `current_positions`. 
    '''
    # endregion Docstring
    if new_avg:
        df = gl.current_positions
        if len(df) == 0:
            gl.log_funcs.record_tracking('average', 'nan')
            return
        avg = df.cash.sum() / df.qty.sum()
        gl.log_funcs.record_tracking('average', avg)
        return
    else:
        tf = gl.tracker
        avg = tf[tf['variable'] == 'average'].value.values[-1]
        return avg


def get_max_vola(volas, min_vola, max_vola):
    # region Docstring
    '''
    # Get Max Volatility
    Takes dictionary of numbers and gives back highest value within range. 

    Returns volatility. 

    ## Parameters:{
    ####    `volas`: dictionary of volatilities
    ####    `min_vola`: minimum set volatility to accept
    ####    `max`: max set volatility to accept
    ## }
    '''
    # endregion Docstring
    volas_list = list(volas.values())
    # get rid of nan values to use max func...
    volas_cleaned = [x for x in volas_list if str(x) != 'nan']
    # volas_cleaned = list(map(int, volas_cleaned))
    volas_cleaned.append(min_vola)
    vola = max(volas_cleaned)
    if vola > max_vola:
        vola = max_vola

    return vola


def get_inverse_perc(percentage_drop):
    # region Docstring
    '''
    ## Get Inverse Percentage
    Returns the value of 100 - percentage drop. 

    Example: if you pass 5 percent, the resulting value will be .95 (100 - 5)

    This is useful so that you can see if the average has dropped by a certain percentage.

    ### Properties: {

    percentage_drop: percentage as an integer or float. 

    }
    '''
    # endregion Docstring

    drop_percent = (100 - percentage_drop)*.01

    return drop_percent


def update_pl(real='skip', unreal='skip'):
    # region Docstring
    '''
    ## Update Profit/Loss
    Updates the value of Profit Loss in the global pl_ex dictionary. 

    ### Parameters:{

    real: float value to add to pl_ex['real']. 
    If you want to use the function without updating, then pass 'skip'. The value defaults to this. 

    unreal: float value to replace the pl_ex['unreal']. 
    If you want to use the function without updating, then pass 'skip'. The value defaults to this. 

    }
    '''
    # endregion Docstring

    pl_ex = {}
    time = get_current_timestamp()
    log = False
    if real != 'skip':
        pl_ex['real'] = gl.pl_ex['real'] + real
        log = True

        if pl_ex['real'] > gl.pl_ex['max_real']:
            pl_ex['max_real'] = pl_ex['real']

        if pl_ex['real'] < gl.pl_ex['min_real']:
            pl_ex['min_real'] = pl_ex['real']

    if unreal != 'skip':
        pl_ex['unreal'] = unreal

        if pl_ex['unreal'] > gl.pl_ex['max_unreal']:
            pl_ex['max_unreal'] = pl_ex['unreal']

        if pl_ex['unreal'] < gl.pl_ex['min_unreal']:
            pl_ex['min_unreal'] = pl_ex['unreal']

    for entry in pl_ex.keys():
        row = {'variable': entry, 'value': pl_ex[entry], 'time': time}
        row = gl.pd.DataFrame(row, index=[len(gl.pl_ex_frame)])
        gl.pl_ex_frame = gl.pl_ex_frame.append(row, sort=False)
        gl.pl_ex[entry] = pl_ex[entry]

    if log:
        gl.log_funcs.log(
            'Realized PL updated: {} Unreal : {}'.format(gl.pl_ex['real'], gl.pl_ex['unreal']))


def update_ex():
    # region Docstring
    '''
    ## Update Exposure

    Updates Exposure values in the global pl_ex dictionary. 
    '''
    # endregion Docstring
    ex = current_exposure()
    time = get_current_timestamp()
    pl_ex = {}
    pl_ex['last_ex'] = ex
    if ex > gl.pl_ex['max_ex']:
        pl_ex['max_ex'] = ex

    for entry in pl_ex.keys():
        row = {'variable': entry, 'value': pl_ex[entry], 'time': time}
        row = gl.pd.DataFrame(row, index=[len(gl.pl_ex_frame)])
        gl.pl_ex_frame = gl.pl_ex_frame.append(row, sort=False)
        gl.pl_ex[entry] = pl_ex[entry]

    gl.log_funcs.log(msg=f'Current Exposure: {ex}')


def all_rows(df):
    '''Shows a dataframe without cutting off all rows... Enter a DF.'''
    with gl.pd.option_context('display.max_rows', None, 'display.max_columns', None):
        # if gl.isnotebook:
        #     display(df)
        # else:
        print(df)


@ gl.log_funcs.tracker
def bounce_factor():
    # region Docstring
    '''
    # Find Bounce Factor
    Finds a number on a non-set scale w 

    #### Returns ex

    ## Parameters:{
    ####    `param`:
    ## }
    '''
    # endregion Docstring
    if len(gl.mom_frame) == 0:
        dr = daily_return()/gl.volas['mean']
        return dr
    ups = gl.mom_frame[gl.mom_frame['trend'] == 'uptrend'].volatility.mean()
    if str(ups) == 'nan':
        ups = 0
    downs = gl.mom_frame[gl.mom_frame['trend']
                         == 'downtrend'].volatility.mean()
    bounce_factor = ups/gl.volas['mean'] - downs/gl.volas['mean']
    return bounce_factor


# @ gl.log_funcs.tracker
def mins_left():
    hard_stop = gl.config['misc']['hard_stop']
    hard_stop = gl.pd.to_datetime(hard_stop).timestamp()
    current_time = gl.common.get_current_timestamp(integer=True)
    secs_to_go = hard_stop - current_time
    mins_to_go = secs_to_go / 60
    return mins_to_go


@ gl.log_funcs.tracker
def investment_duration():
    started = gl.current_positions.exe_time.values[0]
    start_time = gl.pd.to_datetime(started).timestamp()
    current_time = get_current_timestamp(integer=True)
    duration = get_duration(start_time, current_time)
    return duration


def get_duration(start, end, convert_to_timestamp=False):
    if convert_to_timestamp:
        start = gl.pd.to_datetime(start).timestamp()
        end = gl.pd.to_datetime(end).timestamp()
    seconds = end - start
    duration = seconds/60
    return duration


def dur_since_last_trade():
    last_trade_time = gl.current_positions.exe_time.values[-1]
    last_trade_stamp = gl.pd.to_datetime(last_trade_time).timestamp()
    current_time = gl.common.get_current_timestamp(integer=True)
    seconds = current_time - last_trade_stamp
    duration = seconds/60
    return duration


@ gl.log_funcs.tracker
def daily_return():
    open_price = gl.current_frame.open.values[0]
    current_price = gl.current['close']
    ret = (current_price - open_price)/open_price
    ret = ret * 100
    return ret


def candle_is_green():
    if gl.current['close'] > gl.current['open']:
        return True
    return False


def current_trend():
    if len(gl.mom_frame) == 0:
        return None
    else:
        return dict(gl.mom_frame.iloc[-1])


@ gl.log_funcs.tracker
def current_return():
    avg = current_average()
    dif = gl.current_price() - avg
    ret = (dif / avg)*100
    return ret


def current_exposure():
    return gl.current_positions.cash.sum()


def stop_trading():
    gl.chart_response = False
    gl.buy_lock = True


def actively_trading():
    if len(gl.current_positions) != 0:
        return True
    return False
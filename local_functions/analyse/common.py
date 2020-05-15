from local_functions.main import global_vars as gl


def get_volatility(high_list, low_list):
    # region Docstring
    '''
    ## Get Volatility
    Takes high and low lists and makes a list of volatilities based on the highs and lows. 

    returns numpy array of volatilities. 
    '''
    # endregion Docstring
    highs = gl.np.array(high_list)
    lows = gl.np.array(low_list)
    vola = gl.np.around((((highs - lows) / lows)*100),decimals=1)
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


def get_timestamp(minute, second):
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
    return time.strftime('%H:%M:%S')


def get_average():
    # region Docstring
    '''
    ## Get Average
    Returns the average price of `current_positions`. 
    '''
    # endregion Docstring

    df = gl.current_positions
    avg = df.cash.sum() / df.qty.sum()
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

    pl_ex = gl.pl_ex
    log = False
    if real != 'skip':
        pl_ex['real'] += real

        if pl_ex['real'] > pl_ex['max_real']:
            pl_ex['max_real'] = pl_ex['real']

        if pl_ex['real'] < pl_ex['min_real']:
            pl_ex['min_real'] = pl_ex['real']
        log = True

    if unreal != 'skip':
        pl_ex['unreal'] = unreal

        if pl_ex['unreal'] > pl_ex['max_unreal']:
            pl_ex['max_unreal'] = pl_ex['unreal']

        if pl_ex['unreal'] < pl_ex['min_unreal']:
            pl_ex['min_unreal'] = pl_ex['unreal']

    if log:
        gl.log_funcs.log(
            'Realized PL updated: {} Unreal : {}'.format(pl_ex['real'], pl_ex['unreal']))
    gl.pl_ex = pl_ex


def update_ex():
    # region Docstring
    '''
    ## Update Exposure

    Updates Exposure values in the global pl_ex dictionary. 
    '''
    # endregion Docstring

    ex = gl.current_positions.cash.sum()
    pl_ex = gl.pl_ex
    pl_ex['last_ex'] = ex
    if ex > pl_ex['max_ex']:
        pl_ex['max_ex'] = ex

    gl.pl_ex = pl_ex


def all_rows(df):
    '''Shows a dataframe without cutting off all rows... Enter a DF.'''
    with gl.pd.option_context('display.max_rows', None, 'display.max_columns', None):
        display(df)

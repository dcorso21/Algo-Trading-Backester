from local_functions.main import global_vars as gl


def get_volatility(high_list, low_list):
    '''
    ## Get Volatility
    Takes high and low lists and makes a list of volatilities based on the highs and lows. 

    returns list of volatilities. 
    '''

    vola = []
    for high, low in zip(high_list, low_list):
        vola.append(round(((high - low)/low)*100, 1))
    return vola


def red_green():
    '''
    ## Red Green Analysis
    Makes a list with a value for each candle to represent if it was red or green.

    Returns red/green list.   
    '''

    current_frame = gl.current_frame

    r_g = []
    for o, c in zip(current_frame.open, current_frame.close):

        val = 'doji'
        if o < c:
            val = 'green'
        elif o > c:
            val = 'red'

        r_g.append(val)

    return r_g


# def open_to_price(current_frame, price):
#     open_price = list(current_frame[current_frame.time == '09:31:00'].open)[0]
#     return get_volatility([open_price], [price])


def cash_to_shares(cash, price):
    '''
    ## Cash to Shares
    Takes cash amount and execution price and calculates how many shares to buy. 

    returns share quantity. 
    '''
    share_quantity = (int(cash/price))
    return share_quantity


def get_timestamp(minute, second):
    '''
    ## Get TimeStamp
    Takes a minute string and a second integer and creates a timestamp down to the second. 

    Returns a string in the format '%H:%M:%S'

    ### Parameters: {

    minute: string value in the '%H:%M:%S' format

    second: integer value to offset the minute value by. 

    }
    '''

    from datetime import datetime, timedelta
    time = datetime.strptime(minute, '%H:%M:%S')
    time = time+timedelta(seconds=second)
    return time.strftime('%H:%M:%S')


def get_average():
    '''
    ### Get Average
    Returns the average price of Current Positions. 
    '''
    df = gl.current_positions
    avg = df.cash.sum() / df.qty.sum()
    return avg


def get_max_vola(volas, min_vola):
    '''
    ## Get Max Volatility
    Finds the max value in the global 'volas' dictionary.   

    Returns the max value. 

    ### Details:
    1. Usually, this could be accomplished easily by calling max(volas), but because
    this dictionary in the beginning is populated with 'nan' values, it has to filter those out. 

    2. You can specify a minimum volatility with the min_vola argument. 
    It will be added to the list, making it the minimum 'max' value. 


    ### Properties:{

    volas: volatility dictionary

    min_vola: integer or float to create a minimum volatility to be returned. 

    }

    '''

    volas_list = list(volas.values())
    # get rid of nan values to use max func...
    volas_cleaned = [x for x in volas_list if str(x) != 'nan']
    # volas_cleaned = list(map(int, volas_cleaned))
    volas_cleaned.append(min_vola)
    max_vola = max(volas_cleaned)

    return max_vola


def get_inverse_perc(percentage_drop):
    '''
    ## Get Inverse Percentage
    Returns the value of 100 - percentage drop. 

    Example: if you pass 5 percent, the resulting value will be .95 (100 - 5)

    This is useful so that you can see if the average has dropped by a certain percentage.

    ### Properties: {

    percentage_drop: percentage as an integer or float. 

    }
    '''

    drop_percent = (100 - percentage_drop)*.01

    return drop_percent


def update_pl(real='skip', unreal='skip'):
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

    pl_ex = gl.pl_ex
    log = False
    if real != 'skip':
        pl_ex['real'] += real
        log = True

    if unreal != 'skip':
        pl_ex['unreal'] = unreal

    if log:
        gl.logging.info(
            'CA: realized PL updated: {} unreal : {}'.format(pl_ex['real'], pl_ex['unreal']))
    gl.pl_ex = pl_ex


def update_ex():
    '''
    ## Update Exposure

    Updates Exposure values in the global pl_ex dictionary. 
    '''
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

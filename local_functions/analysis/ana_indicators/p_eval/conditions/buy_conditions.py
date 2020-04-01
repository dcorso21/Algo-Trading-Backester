from local_functions.main import global_vars as gl


##################################################
##################################################
# START POSITION...


def starting_position():
    '''
    ## Starting Position
    Creates buy order with one percent of available capital at current price. 

    Returns buys DataFrame. 
    '''
    cash = gl.account.get_available_capital() * .01
    cancel_spec = gl.o_tools.cancel_specs['standard']
    buys = gl.o_tools.create_buys(
        cash, gl.current['close'], cancel_spec)
    return buys

##################################################
##################################################
# SIZE IN...


def drop_below_average():
    '''
    ## Drop Below Average
    ### Buy Condition
    Checks to see if the current price is a certain amount below the average price of your current positions. 

    Returns buys DataFrame

    ### Details:
    The drop amount is taken from the volas module with the function: `get_max_vola()`
    '''

    current = gl.current
    max_vola = gl.common_ana.get_max_vola(gl.volas, 4)
    drop_perc = gl.common_ana.get_inverse_perc(max_vola)
    avg = gl.common_ana.get_average()

    if current['close'] < (avg * drop_perc):
        cash = gl.pl_ex['last_ex']
        exe_price = current['close']
        cancel_spec = gl.o_tools.cancel_specs['standard']
        buys = gl.o_tools.create_buys(
            cash, exe_price, cancel_spec)
        return buys

    return gl.pd.DataFrame()

from local_functions.main import global_vars as gl


def buy_eval():
    '''

    DECIDES WHETHER OR NOT TO TRADE. IF CONDITIONS ARE TRUE, THE LOOP IS BROKEN. 

    '''
    if bad_buy_conditions() == True:
        buys = gl.pd.DataFrame()
        return buys

    # STARTING POSITION
    if len(gl.current_positions()) == 0:
        return gl.b_conds.starting_position()

    loop = True
    while loop:

        # 1. returns True if the current price is below average by a certain percentage.
        buys, loop = gl.b_conds.drop_below_average()

        loop = False

    return buys


def bad_buy_conditions():

    # DONT RUN THE CODE IF THESE CONDITIONS ARE MET.
    # 1. if chart looks bad.
    cond1 = (gl.chart_response == False)
    # AND!
    # 2. if NOT already in ...
    cond2 = (len(gl.current_positions()) != 0)
    # OR
    # if there are orders still awaiting fill.
    cond3 = (len(gl.open_orders()) != 0)

    # Returns true or false...
    return ((cond1 and cond2) or cond3)

from local_functions.main import global_vars as gl


def buy_eval():
    '''

    DECIDES WHETHER OR NOT TO TRADE. IF CONDITIONS ARE TRUE, THE LOOP IS BROKEN. 

    '''
    if bad_buy_conditions() == True:
        buys = gl.pd.DataFrame()
        return buys

    # STARTING POSITION
    if len(gl.current_positions) == 0:
        return gl.b_conds.starting_position()

    buy_conds = [
        gl.b_conds.drop_below_average
    ]

    for func in buy_conds:
        buys = func()
        if len(buys) != 0:
            break

    return buys

    return buys


def bad_buy_conditions():

    # DONT RUN THE CODE IF THESE CONDITIONS ARE MET.
    # 1. if chart looks bad.
    cond1 = (gl.chart_response == False)
    # AND!
    # 2. if NOT already in ...
    cond2 = (len(gl.current_positions) != 0)

    # Returns true or false...
    return (cond1 and cond2)

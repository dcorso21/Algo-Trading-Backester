from local_functions.main import global_vars as gl


##################################################
##################################################
# START POSITION...


def starting_position():
    cash = gl.account.get_available_capital() * .01
    buys = gl.o_tools.create_buys(
        cash, gl.current()['close'])
    return buys

##################################################
##################################################
# SIZE IN...


def drop_below_average():
    current = gl.current()
    max_vola = gl.common_ana.get_max_vola(gl.volas(), gl.current())
    drop_below_average = gl.common_ana.get_inverse_perc(max_vola)
    avg = gl.common_ana.get_average()

    if current['close'] < (avg * drop_below_average):
        loop = False
        cash = gl.common_ana.get_exposure()
        exe_price = current['close']
        buys = gl.o_tools.create_buys(cash, exe_price)
    else:
        loop = True
        buys = gl.pd.DataFrame()

    return buys, loop

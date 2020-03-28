from local_functions.main import global_vars as gl


# 3 % gain... sell all
def three_perc_gain():
    avg = gl.common_ana.get_average()
    if gl.current['close'] > (avg * 1.03):
        # sell all
        everything = gl.current_positions.qty.sum()
        sells = gl.o_tools.create_sells(everything, gl.current['close'])
        loop = False
    else:
        sells = gl.pd.DataFrame()
        loop = True
    return sells, loop


def target_unreal(target_int):
    if gl.pl_ex['unreal'] > target_int:
        # sell all
        everything = gl.current_positions.qty.sum()
        exe_price = gl.current['close']
        sells = gl.o_tools.create_sells(everything, exe_price)
        loop = False
    else:
        sells = gl.pd.DataFrame()
        loop = True
    return sells, loop


# if exposure is over 30K... sell half
def exposure_over_account_limit():
    available_capital = gl.account.get_available_capital()
    exposure = gl.pl_ex['last_ex']
    if exposure > available_capital:
        half = int(gl.current_positions.qty.sum()/2)
        exe_price = gl.current['close']
        sells = gl.o_tools.create_sells(half, exe_price)
        loop = False
    else:
        sells = gl.pd.DataFrame()
        loop = True
    return sells, loop


def eleven_oclock_exit():
    current = gl.current

    if (current['minute'] == '11:00:00'):
        everything = gl.current_positions.qty.sum()
        exe_price = current['close']
        sells = gl.o_tools.create_sells(everything, exe_price)
        gl.logging.info('PS: Sell to Stop...')
        gl.loop_feedback = False
        loop = False
    else:
        sells = gl.pd.DataFrame()
        loop = True
    return sells, loop

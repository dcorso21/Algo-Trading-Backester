from local_functions.main import global_vars as gl


# 3 % gain... sell all
def three_perc_gain():
    avg = gl.common_ana.get_average()
    if gl.current['close'] > (avg * 1.03):
        # sell all
        everything = gl.current_positions.qty.sum()
        sells = gl.o_tools.create_sells(everything, gl.current['close'])
        gl.logging.info('----> over 3 perc gain triggered. ')
        return sells
    sells = gl.pd.DataFrame()
    return sells


def target_unreal():
    target_int = 20
    unreal = gl.pl_ex['unreal']
    if unreal > target_int:
        # sell all
        everything = gl.current_positions.qty.sum()
        exe_price = gl.current['close']
        sells = gl.o_tools.create_sells(everything, exe_price)
        gl.logging.info(f'----> unreal hits trigger: {unreal}')
        return sells

    sells = gl.pd.DataFrame()
    return sells


# if exposure is over 30K... sell half
def exposure_over_account_limit():
    available_capital = gl.account.get_available_capital()
    exposure = gl.pl_ex['last_ex']
    if exposure > available_capital:
        half = int(gl.current_positions.qty.sum()/2)
        exe_price = gl.current['close']
        sells = gl.o_tools.create_sells(half, exe_price)
        gl.logging.info('----> over-exposed sell half.')
    else:
        sells = gl.pd.DataFrame()
    return sells


def eleven_oclock_exit():
    current = gl.current

    if (current['minute'] == '11:00:00'):
        everything = gl.current_positions.qty.sum()
        exe_price = current['close']
        sells = gl.o_tools.create_sells(everything, exe_price)
        gl.logging.info('PS: Sell to Stop...')
        gl.loop_feedback = False
    else:
        sells = gl.pd.DataFrame()
    return sells

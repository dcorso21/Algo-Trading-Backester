from local_functions.main import global_vars as gl


def get_volatility(high_list, low_list):
    vola = []
    for high, low in zip(high_list, low_list):
        vola.append(round(((high - low)/low)*100, 1))
    return vola


def red_green():

    current_frame = gl.current_frame

    r_g = []
    for o, c in zip(current_frame.open, current_frame.close):

        val = 0
        if o < c:
            val = 1
        elif o > c:
            val = 2
        red_or_green = {0: 'doji',
                        1: 'green',
                        2: 'red'}

        r_g.append(red_or_green[val])

    return r_g


def open_to_price(current_frame, price):
    open_price = list(current_frame[current_frame.time == '09:31:00'].open)[0]
    return get_volatility([open_price], [price])


def cash_to_shares(cash, price):

    return (int(cash/price))


def get_timestamp(minute, second):

    from datetime import datetime, timedelta
    time = datetime.strptime(minute, '%H:%M:%S')
    time = time+timedelta(seconds=second)
    return time.strftime('%H:%M:%S')


def get_average():

    df = gl.current_positions()
    avg = df.cash.sum() / df.qty.sum()
    return avg


def get_exposure():

    df = gl.current_positions()
    ex = df.cash.sum()

    return ex


def get_max_vola(volas, current):

    volas_list = list(volas.values())
    # get rid of nan values to use max func...
    volas_cleaned = [x for x in volas_list if str(x) != 'nan']

    if len(volas_cleaned) != 0:
        max_vola = max(list(map(int, volas_cleaned)))
    else:
        max_vola = False

    if max_vola == False:
        current_vola = (
            (current['high'] - current['low'])/current['low'])
        max_vola = current_vola

    return max_vola


def get_inverse_perc(percentage_drop):

    drop_percent = (100 - percentage_drop)*.01

    return drop_percent


def update_pl(real, unreal):

    pl_ex = gl.pl_ex()

    if real != 'skip':
        pl_ex['real'] += real

    if unreal != 'skip':
        pl_ex['unreal'] += unreal

    real = pl_ex['real']
    unreal = pl_ex['unreal']

    gl.save_dict_to_csv(pl_ex, gl.filepath['pl_ex'])

    gl.logging.info(
        'TF: realized PL updated: {} unreal : {}'.format(real, unreal))
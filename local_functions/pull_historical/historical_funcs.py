
'''
DO NOT DELETE OR REPLACE THESE IMPORTS. 
This sheet is a special case... 
'''
import pandas as pd
import random
import datetime


def get_mkt_data(name):
    '''
    # Get Market Data
    Retrieves info from quantopian csv data. Selectively chooses which rows to use and formats.

    Returns DataFrame

    ## Parameters:{

    `name`: filename of csv in main folder. This file should be made from the 'traded tickers' sheet in quantopian. 

    }'''

    #filename = 'quantopian_data/'+str(date)+'-QuantData.csv'

    # read data, only choose the rows listed in iloc.
    # the capital T at the end is to transpose the data - switch rows with columns.
    m = pd.read_csv(name, header=None).T

    # These become the column names.
    columns = {0: 'ticker',
               1: 'time',
               2: 'close',
               3: 'high',
               4: 'low',
               5: 'open',
               6: 'volume'}
    m = m.rename(columns=columns)
    m.drop(m.tail(1).index, inplace=True)
    m = complete_data(m)

    m['open'] = m.open.astype(float)
    m['high'] = m.high.astype(float)
    m['low'] = m.low.astype(float)
    m['close'] = m.close.astype(float)
    m['volume'] = m.volume.astype(float).astype(int)

    # Re-Order
    m = m[['ticker', 'time', 'open', 'high', 'low', 'close', 'volume']]

    return m


def make_new_minute(ticker, new_min, close_price):
    '''
    # Make New Minute
    Referenced by the `complete_data` function to append a row to the `sim_df` df. 
    '''
    new_row = {'ticker': [ticker],
               'time': [new_min],
               'open': [close_price],
               'high': [close_price],
               'low': [close_price],
               'close': [close_price],
               'volume': [0]
               }
    new_row = pd.DataFrame(new_row)
    return new_row


def complete_data(mkt_data):
    '''
    # Complete Data
    Fills in gaps in the `sim_df` variable. 
    '''
    m = mkt_data
    ticker = m.at[0, 'ticker']

    # If the last value is NOT @ 4pm... , make that row.
    if m.time.to_list()[-1] != '16:00:00':
        price = m.close.to_list()[-1]
        last_row = make_new_minute(ticker, '16:00:00', price)
        m = m.append(last_row, sort=False)

    last_min = pd.to_datetime('09:30:00')
    m['time'] = m.time.apply(lambda x: pd.to_datetime(x))

    added_df = pd.DataFrame()
    for minute, close_price in zip(m.time, m.close):
        duration = int((minute - last_min).seconds / 60)

        if duration == 1:
            last_min = minute
            continue

        for delta in range(1, duration):
            new_min = (last_min +
                       datetime.timedelta(minutes=delta))  #
            new_row = make_new_minute(ticker, new_min, close_price)
            added_df = added_df.append(new_row, sort=False)

        last_min = minute

    m = m.append(added_df, sort=False)
    m = m.sort_values(by='time')
    m = m.reset_index(drop=True)
    m['time'] = m.time.apply(lambda x: x.strftime('%H:%M:%S'))
    return m


def create_second_data(sim_df, index, mode='mixed'):
    '''
    # Create Second Data
    Creates second data based on minute row of `sim_df`

    '''
    row = list(sim_df.iloc[index])

    # ticker = row[0]
    # minute = row[1]
    o = float(row[2])
    h = float(row[3])
    l = float(row[4])
    c = float(row[5])
    v = round(float(row[6]), 1)

    prices, volumes = create_second_data_2(o, h, l, c, v, mode)
    return prices, volumes  # , ticker, minute


def create_second_data_2(o, h, l, c, v, mode):
    '''
    Continuation of `create_second_data` function. 
    '''

    volumes = []
    vol = 0
    for x in range(0, 60):
        if x == 59:
            volumes.append(v)
        else:
            vol += int(round(v/60, 1))
            volumes.append(vol)

    if mode == 'mixed':
        prices = mixed_second_data(o, h, l, c, v)
    elif mode == 'random':
        prices = random_second_data(o, h, l, c, v)
    elif mode == 'momentum':
        prices = momentum_second_data(o, h, l, c)

    return prices, volumes


def momentum_second_data(o, h, l, c):
    prices = []
    prices.append(o)

    hl_order = {}
    hl = [1, 2]

    if c > o:
        momentum = 'up'

    elif c < o:
        momentum = 'down'

    else:
        momentum = 'doji'

    if momentum == 'down':
        hl_order['high'] = hl[1]
        hl_order['low'] = hl[0]
    elif momentum == 'up':
        hl_order['high'] = hl[0]
        hl_order['low'] = hl[1]
    elif momentum == 'doji':
        random.shuffle(hl)
        hl_order['high'] = hl[0]
        hl_order['low'] = hl[1]

    if hl_order['high'] == 1:
        val_one = h
        val_two = l
    else:
        val_one = l
        val_two = h

    # pick a number between 1 and 5
    chances = random.randint(0, 6)
    if chances == 5:
        # pick a number between 1 and 58.
        chunk_one = random.randint(5, 50)
    else:
        # pick a number between 10 and 39...
        chunk_one = random.randint(10, 40)

    prices = append_chunk(o, val_one, prices, chunk_one)

    chunk_two = random.randint(5, 60 - len(prices))

    prices = append_chunk(val_one, val_two, prices, chunk_two)

    chunk_three = 60 - len(prices) - 1

    prices = append_chunk(val_two, c, prices, chunk_three)

    return prices


def random_second_data(o, h, l, c, v):

    prices = []
    prices.append(o)

    for x in range(0, 56):
        prices.append(round(random.uniform(l, h), 3))

    # insert high and low randomly
    prices.insert(random.randint(2, int(len(prices))-1), h)
    prices.insert(random.randint(2, int(len(prices))-1), l)
    prices.append(c)

    return prices


def mixed_second_data(o, h, l, c, v):
    prices = []
    prices.append(o)

    rand_chance = random.randint(0, 10)

    # 90% of the time, it acts with momentum.
    if rand_chance != 9:

        hl_order = randomize_hl()

        if hl_order['high'] == 1:
            val_one = h
            val_two = l
        else:
            val_one = l
            val_two = h

        # pick a number between 1 and 5
        chances = random.randint(0, 6)
        if chances == 5:
            # pick a number between 1 and 58.
            chunk_one = random.randint(5, 50)
        else:
            # pick a number between 10 and 39...
            chunk_one = random.randint(10, 40)

        prices = append_chunk(o, val_one, prices, chunk_one)

        chunk_two = random.randint(5, 60 - len(prices))

        prices = append_chunk(val_one, val_two, prices, chunk_two)

        chunk_three = 60 - len(prices) - 1

        prices = append_chunk(val_two, c, prices, chunk_three)

    # 10% of the time, it will be completely random.
    else:
        # create random price values for 56 of the 60 seconds between high and low
        for x in range(0, 56):
            prices.append(round(random.uniform(l, h), 3))

        # insert high and low randomly
        prices.insert(random.randint(2, int(len(prices))-1), h)
        prices.insert(random.randint(2, int(len(prices))-1), l)
        prices.append(c)

    return prices


def append_chunk(first_value, last_value, main_list, middle_length):

    chunk_list = []
    for x in range(0, middle_length):
        chunk_list.append(round(random.uniform(first_value, last_value), 3))

    chunk_list = sorted(chunk_list)
    if first_value > last_value:
        chunk_list.reverse()

    for x in chunk_list:
        main_list.append(x)

    main_list.append(last_value)
    return main_list


def randomize_hl():
    o, h, l, c = 1, 2, .5, 1

    hl_order = {}

    # a one in four chance of acting this way... Otherwise, opposite...
    chances = [1, 2, 3, 4]
    random.shuffle(chances)

    if chances[0] != 4:
        hl = [1, 2]
    else:
        hl = [2, 1]

    if c > o:
        momentum = 'up'

    elif c < o:
        momentum = 'down'

    else:
        momentum = 'doji'

    if momentum == 'down':
        hl_order['high'] = hl[1]
        hl_order['low'] = hl[0]
    elif momentum == 'up':
        hl_order['high'] = hl[0]
        hl_order['low'] = hl[1]
    elif momentum == 'doji':
        random.shuffle(hl)
        hl_order['high'] = hl[0]
        hl_order['low'] = hl[1]

    return hl_order

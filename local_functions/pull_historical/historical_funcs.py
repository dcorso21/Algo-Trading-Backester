from local_functions.main import global_vars as gl


def create_second_data(index, mode='mixed'):

    row = list(gl.sim_df.iloc[index])

    o = float(row[5])
    h = float(row[3])
    l = float(row[4])
    c = float(row[2])
    v = round(float(row[6]), 1)
    ticker = row[0]
    minute = row[1]

    prices, volumes = create_second_data_2(o, h, l, c, v, mode)
    return prices, volumes, ticker, minute


def create_second_data_2(o, h, l, c, v, mode):

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
        prices = momentum_second_data(o, h, l, c, v)

    return prices, volumes


def momentum_second_data(o, h, l, c, v):
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
        gl.random.shuffle(hl)
        hl_order['high'] = hl[0]
        hl_order['low'] = hl[1]

    if hl_order['high'] == 1:
        val_one = h
        val_two = l
    else:
        val_one = l
        val_two = h

    # pick a number between 1 and 5
    chances = gl.random.randint(0, 6)
    if chances == 5:
        # pick a number between 1 and 58.
        chunk_one = gl.random.randint(5, 50)
    else:
        # pick a number between 10 and 39...
        chunk_one = gl.random.randint(10, 40)

    prices = append_chunk(o, val_one, prices, chunk_one)

    chunk_two = gl.random.randint(5, 60 - len(prices))

    prices = append_chunk(val_one, val_two, prices, chunk_two)

    chunk_three = 60 - len(prices) - 1

    prices = append_chunk(val_two, c, prices, chunk_three)

    return prices


def random_second_data(o, h, l, c, v):

    prices = []
    prices.append(o)

    for x in range(0, 56):
        prices.append(round(gl.random.uniform(l, h), 3))

    # insert high and low randomly
    prices.insert(gl.random.randint(2, int(len(prices))-1), h)
    prices.insert(gl.random.randint(2, int(len(prices))-1), l)
    prices.append(c)

    return prices


def mixed_second_data(o, h, l, c, v):
    prices = []
    prices.append(o)

    rand_chance = gl.random.randint(0, 10)

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
        chances = gl.random.randint(0, 6)
        if chances == 5:
            # pick a number between 1 and 58.
            chunk_one = gl.random.randint(5, 50)
        else:
            # pick a number between 10 and 39...
            chunk_one = gl.random.randint(10, 40)

        prices = append_chunk(o, val_one, prices, chunk_one)

        chunk_two = gl.random.randint(5, 60 - len(prices))

        prices = append_chunk(val_one, val_two, prices, chunk_two)

        chunk_three = 60 - len(prices) - 1

        prices = append_chunk(val_two, c, prices, chunk_three)

    # 10% of the time, it will be completely random.
    else:
        # create random price values for 56 of the 60 seconds between high and low
        for x in range(0, 56):
            prices.append(round(gl.random.uniform(l, h), 3))

        # insert high and low randomly
        prices.insert(gl.random.randint(2, int(len(prices))-1), h)
        prices.insert(gl.random.randint(2, int(len(prices))-1), l)
        prices.append(c)

    return prices


def append_chunk(first_value, last_value, main_list, middle_length):

    chunk_list = []
    for x in range(0, middle_length):
        chunk_list.append(round(gl.random.uniform(first_value, last_value), 3))

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
    gl.random.shuffle(chances)

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
        gl.random.shuffle(hl)
        hl_order['high'] = hl[0]
        hl_order['low'] = hl[1]

    return hl_order


def complete_data(df):
    '''Function:
    This looks at each minute of each stock in a market data df
    and ensures it accounts for each minute the market is open. 

    Inputs:
    {
    df: a dataframe of market data with one or more stocks present. 
    }

    How it works:
    If a minute is missing, the row is created by using the last known minute's close value
    Volume is left at 0 to make sure you can see that the minute was constructed artifically.  
    '''

    # creates a list of stocks without repeats.
    stocklist = df.ticker
    stocklist = list(dict.fromkeys(stocklist))

    # Goes stock by stock.
    for x in stocklist:
        m = df[df.ticker == x]
        m = m.sort_values(by='time')
        dfx = gl.pd.DataFrame()
        tickers = []
        t = []
        o = []
        h = []
        l = []
        cl = []
        v = []

        # Sets a default value for minute - being the minute before the beginning.
        minute = gl.pd.to_datetime('09:30:00')

        # Sets a default value for last close — only to be used if the first minutes are missing.
        lclose = m.close.astype(float).mean()

        # Determines if a gap occurs.
        for a, b in zip(m.time, m.close):
            a = gl.pd.to_datetime(a)
            if a != minute + gl.datetime.timedelta(minutes=1):
                # If there is a gap, determine how long it is.
                # Then define the var reps as a range with the length of missing minutes to be filled.
                for y in range(1, 390):
                    if a == minute + gl.datetime.timedelta(minutes=y):
                        break
                reps = [range(0, y)]
                for z in reps:

                    # redefine the minute to the next minute.
                    minute = gl.pd.to_datetime(
                        (minute + gl.datetime.timedelta(minutes=1))).time().strftime('%H:%M:%S')

                    # append the values for that minute.
                    tickers.append(x)
                    t.append(minute)
                    o.append(lclose)
                    h.append(lclose)
                    l.append(lclose)
                    cl.append(lclose)
                    v.append(0)

                    # convert minute to datetime.
                    # -- For some reason I need this...
                    minute = gl.pd.to_datetime(minute)

                    # if it is the last repitition, add another minute so the for loop can
                    # continue on to fill other gaps.
                    if z == reps[-1]:
                        minute = gl.pd.to_datetime(
                            (minute + gl.datetime.timedelta(minutes=1))).time().strftime('%H:%M:%S')
                        minute = gl.pd.to_datetime(minute)

            # Save last close for future gaps.
            lclose = b
            minute = a
        dfx['ticker'] = tickers
        dfx['time'] = t
        dfx['open'] = o
        dfx['high'] = h
        dfx['low'] = l
        dfx['close'] = cl
        dfx['volume'] = v

        # When this appends, it doesn't reorder the info by time,
        # that will be done by other functions used in conjunction with this function.
        df = df.append(dfx, sort=False)
        df = df.sort_values(by='time')
    return df


def get_mkt_data(name):
    '''Function:
    Retrieves info from quantopian csv data. Selectively chooses which rows to use and formats.

    Inputs:
    {
    date: a string in the "yyyy-mm-dd" format. Date must be of a day with available market info
    in the "quantopian_data" folder.
    }'''

    #filename = 'quantopian_data/'+str(date)+'-QuantData.csv'

    # read data, only choose the rows listed in iloc.
    # the capital T at the end is to transpose the data - switch rows with columns.
    m = gl.pd.read_csv(name, header=None).T

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

    return complete_data(m)

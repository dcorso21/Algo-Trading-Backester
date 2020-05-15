from local_functions.main import global_vars as gl


def daily_chart(ticker):
    ticker = ticker.upper()

    now = gl.datetime.datetime.now()
    unix_now = str(int(now.timestamp()))+'000'
    client_id = gl.account.client_id
    url = f'https://api.tdameritrade.com/v1/marketdata/{ticker}/pricehistory'

    params = {

        'apikey': client_id,
        'periodType': 'day',
        'period': '1',
        'frequencyType': 'minute',
        'frequency': '1',
        'endDate': unix_now,
        # 'startDate': '1585797785000',
        'needExtendedHoursData': 'false',

    }

    content = gl.requests.get(url=url, params=params)
    data = content.json()

    df = gl.pd.DataFrame(data['candles'])

    def to_dt(timestamp):
        return gl.datetime.datetime.fromtimestamp(timestamp / 1000)

    dates = []
    times = []
    for entry in df.datetime:
        date, time = to_dt(entry).strftime(r'%m/%d/%Y,%H:%M:%S').split(',')
        dates.append(date)
        times.append(time)

    df['time'] = times
    df['date'] = dates
    df['ticker'] = [ticker for _ in range(len(df))]
    df.drop(columns='datetime')

    end_index = df[df.time == '16:00:00'].index.to_list()
    if len(end_index) != 0:
        end = end_index[0]
        df = df.iloc[:end]

    return df


def yearly_chart(ticker):
    ticker = ticker.upper()
    now = gl.datetime.datetime.now()
    end = str(int(now.timestamp()))+'000'
    start = now - gl.datetime.timedelta(days=366)
    start = str(int(start.timestamp()))+'000'

    client_id = gl.account.client_id
    url = f'https://api.tdameritrade.com/v1/marketdata/{ticker}/pricehistory'

    params = {

        'apikey': client_id,
        'periodType': 'year',
        'period': '1',
        'frequencyType': 'daily',
        'frequency': '1',
        'endDate': end,
        # 'startDate': start,
        'needExtendedHoursData': 'false',

    }

    content = gl.requests.get(url=url, params=params)
    data = content.json()

    df = gl.pd.DataFrame(data['candles'])

    def to_dt(timestamp):
        return gl.datetime.datetime.fromtimestamp(timestamp / 1000)

    df['date'] = df.datetime.apply(lambda x: to_dt(x).strftime(r'%m/%d/%Y'))

    df['ticker'] = [ticker for _ in range(len(df))]
    df.drop(columns='datetime')

    return df


def show_plot(period='day', ticker='MSFT'):

    if period == 'day':
        df = daily_chart(ticker)
    if period == 'year':
        df = yearly_chart(ticker)

    gl.candles.show_candlestick_chart(df)

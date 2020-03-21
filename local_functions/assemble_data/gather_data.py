#import analyse as ana
import pandas as pd
import json


def update_candle(price,volume, ticker, minute, second, daily_df):
    '''Inputs--
    prices: list of prices simulating real time updates from the historical_funcs: create_second_data.'''
    
    if second == 0:
        o,h,l,c = price,price,price,price
    else:
        json_file = open('temp_assets/current_ohlcvs.json')
        prev = json.load(json_file)
        
        o,h,l,c = prev['open'], prev['high'], prev['low'], prev['close']
        
        if price > h:
            h = price
        if price < l:
            l = price
    c = price
    v = volume

    current = {'open':o,
               'high':h,
               'low':l,
               'close':c,
               'volume':v,
               'second':second,
               'minute': minute}
    
    
    json_file = json.dumps(current)
    f = open('temp_assets/current_ohlcvs.json','w')
    f.write(json_file)
    f.close()

    current_frame = add_new_minute(current, ticker, minute, daily_df)
    #current_frame.to_csv('temp_assets/current_frame.csv')
                
    return current, current_frame


def add_new_minute(current, ticker, minute, daily_df):
    
    new_minute = {'time': [minute],
                  'ticker':[ticker],
                 'open':[current['open']],
                 'high':[current['high']],
                 'low':[current['low']],
                 'close':[current['close']],
                 'volume':[current['volume']]
                 }
    dfx = pd.DataFrame(new_minute)

    return daily_df.append(dfx, sort = False)


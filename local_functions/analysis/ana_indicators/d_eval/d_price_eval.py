import pandas as pd
import logging
import json

def pricing_eval(current,current_frame):
    binary = False
    if red_green(current_frame)[-1] == 'red':
        binary = True

    return binary

def get_resistances(current, cent_range = 10):

    # volas = pull_json('temp_assets/analysis/volas.json') 

    df = pd.read_csv('temp_assets/analysis/daily_eval.csv')

    highs = df[df.high >= current['close']].high.to_list()

    highs = list(dict.fromkeys(highs))

    resistances = set()

    for high in highs:
        added = False

        if len(resistances) == 0:
            resistances.add(high)

        else:
            for resistance in resistances:

                added = eval_resistance(high, resistance, resistances, cent_range)

                if added == True:
                    break

            if added == False:
                resistances.add(high)

    return list(resistances)
        

def eval_resistance(high, resistance, resistance_set, cent_range):

    cents = (cent_range*.01)/2

    if (high > resistance - cents) and (high < resistance + cents):
        
        added = True
        if high > resistance:

            resistance_set.discard(resistance)
            resistance_set.add(high)
    
    else:
        added = False
    
    return added

def get_supports(current, cent_range = 6):

    # volas = pull_json('temp_assets/analysis/volas.json') 

    df = pd.read_csv('temp_assets/analysis/daily_eval.csv')

    lows = df[df.low <= current['close']].low.to_list()

    lows = list(dict.fromkeys(lows))

    supports = set()

    for low in lows:
        added = False

        if len(supports) == 0:
            supports.add(low)

        else:
            for support in supports:

                added = eval_support(low, support, supports, cent_range)

                if added == True:
                    break

            if added == False:
                supports.add(low)

    return list(supports)
        

def eval_support(low,support, support_set, cent_range):

    cents = (cent_range*.01)/2

    if (low > support - cents) and (low < support + cents):
        
        added = True
        if low < support:

            support_set.discard(support)
            support_set.add(low)
    
    else:
        added = False
    
    return added


def find_uptrends(current_frame):
    
    df = current_frame
    dfx = pd.DataFrame()
    count = 0
    
    for o,h,l,c,m in zip(df.open.astype(float), df.high.astype(float), df.low.astype(float), df.close.astype(float), df.time):
        
        # if green candle:
        if o <= c:
            count += 1
            if count == 1:
                start_min = {'open':o,
                            'high':h,
                            'low':l,
                            'close':c,
                            'time':m}
        else:
            count = 0
            
        #
        if count > 1:
            if (h < last_min['high']) and (l <= last_min['low']):
                count = 0

        last_min = {'open':o,
                    'high':h,
                    'low':l,
                    'close':c,
                    'time':m}
        
        
        if count >= 3:
            
            volatility = ((last_min['high'] - start_min['low'])/start_min['low'] )*100
            
            row = {'pattern':['uptrend'],
                   'start_min':[start_min['time']],
                   'end_min':[last_min['time']],
                   'duration':[count],
                   'volatility': [round(volatility,2)]}
            row = pd.DataFrame(row)
            dfx = dfx.append(row)
    
    
    slim_df = pd.DataFrame()
    
    time_list = dfx.start_min
    time_list = list(dict.fromkeys(time_list))
    
    for time in time_list:
        dfz = dfx[dfx.start_min == time]
        slim_df = slim_df.append(dfz.tail(1))
        
    return slim_df 
        
    
def find_downtrends(current_frame):
    
    df = current_frame
    dfx = pd.DataFrame()
    count = 0
    
    for o,h,l,c,m in zip(df.open.astype(float), df.high.astype(float), df.low.astype(float), df.close.astype(float), df.time):        
        # if red candle:
        if o >= c:
            count += 1
            if count == 1:
                start_min = {'open':o,
                            'high':h,
                            'low':l,
                            'close':c,
                            'time':m}
        else:
            count = 0
            
        #
        if count > 1:
            if (h > last_min['high']) and (l >= last_min['low']):
                count = 0

        last_min = {'open':o,
                    'high':h,
                    'low':l,
                    'close':c,
                    'time':m}
        
        if count >= 3:
            
            volatility = ((last_min['high'] - start_min['low'])/start_min['low'] )*100
            
            row = {'pattern':['downtrend'],
                   'start_min':[start_min['time']],
                   'end_min':[last_min['time']],
                   'duration':[count],
                   'volatility': [round(volatility,2)]}
            row = pd.DataFrame(row)
            dfx = dfx.append(row)
    
    
    slim_df = pd.DataFrame()
    
    time_list = dfx.start_min
    time_list = list(dict.fromkeys(time_list))
    
    for time in time_list:
        dfz = dfx[dfx.start_min == time]
        slim_df = slim_df.append(dfz.tail(1))
        
    return slim_df 
    
def red_green(current_frame):
    r_g = []
    for o, c in zip(current_frame.open,current_frame.close):
        
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


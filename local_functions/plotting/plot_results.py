import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.offline

from pathlib import Path
import os
import json

from local_functions.data_management import historical_funcs as hist


def add_box_scatter_cross(fig, row, column, x_values, y_values, labels, colors):
    # region Docstring
    '''
    # Add Box Scatter Cross
    Add a custom  scatter plot with box and whisker plots breakdowns included.

    Returns given figure (`fig`) with new subplot added.

    # Parameters:{
    # `fig`: plotly subplot figure
    # `row`: int, row to insert graph in subplot grid
    # `column`: int, row to insert graph in subplot grid
    # `x_values`: list, x values for scatter
    # `y_values`: list, y values for scatter
    # `labels`: list, labels for each scatter point
    # `colors`: list, colors for each scatter point
    # }
    '''
    # endregion Docstring

    x = x_values
    y = y_values

    # define positions for box charts so they avoid the scatter.
    x_off = [min(x) - (max(x) - min(x))*.05]*len(y)
    y_off = [min(y) - (max(y) - min(y))*.05]*len(x)
    x_width = abs((max(x) - min(x))*.03)
    y_width = abs((max(y) - min(y))*.05)

    vert_box = go.Box(y=y,
                      x=x_off,
                      orientation='v',
                      text=y,
                      boxmean=True,
                      boxpoints=False,
                      width=x_width,
                      opacity=.5,
                      marker_color=colors,
                      showlegend=False
                      )

    hor_box = go.Box(x=x,
                     orientation='h',
                     y=y_off,
                     text=x,
                     boxmean=True,
                     boxpoints=False,
                     width=y_width,
                     opacity=.5,
                     marker_color=colors,
                     showlegend=False
                     )

    # create a scatter plot
    scatter = go.Scatter(x=x,
                         y=y,
                         mode='markers',
                         marker_color=colors,
                         text=labels,
                         showlegend=False
                         )

    # append figures to subplot
    fig.append_trace(vert_box, row, column)
    fig.append_trace(hor_box, row, column)
    fig.append_trace(scatter, row, column)

    return fig


def new_line_plot(x_values, y_values, text, color='blue',
                  visible=True, start_with_zero=True,
                  name=None):
    # region Docstring
    '''
    # New Line Plot
    Creates a plotly scatter trace to be appended to a figure

    Returns Trace.

    # Parameters:{
    # `x_values`: list, x values for scatter
    # `y_values`: list, y values for scatter
    # `text`: list, labels for each point
    # }
    '''
    # endregion Docstring

    if start_with_zero:
        x_values = list(x_values)
        x_values.append(len(x_values))

        zero = [0]
        zero.extend(list(y_values))
        y_values = zero

        text = [''].extend(text)

    line_plot = go.Scatter(x=x_values,
                           y=y_values,
                           mode='lines+markers',
                           text=text,
                           line_color=color,
                           visible=visible,
                           name=name
                           )
    return line_plot


def new_box_plot(x_values, labels, jitter):
    # region Docstring
    '''
    # New Box Plot
    Creates a plotly Box trace to be appended to a figure

    Returns Trace.

    ### Parameters:{
    #### `x_values`: list, x values for scatter
    #### `labels`: list, text for hover of each point
    #### `jitter`: how much the scatter beside the box plot will be spread out.
    #### }
    '''
    # endregion Docstring
    box_plot = go.Box(x=x_values,
                      boxpoints='all',
                      jitter=jitter,
                      pointpos=-1.8,
                      text=labels,
                      boxmean=True
                      )

    return box_plot


def new_scatter_plot(x_values, y_values, text):
    # region Docstring
    '''
    # New Scatter Plot
    Creates a plotly scatter trace to be appended to a figure

    Returns Trace.

    # Parameters:{
    # `x_values`: list, x values for scatter
    # `y_values`: list, y values for scatter
    # `text`: list, labels for each point
    # }
    '''
    # endregion Docstring
    scatter_plot = go.Scatter(x=x_values,
                              y=y_values,
                              mode='markers',
                              text=text
                              )
    return scatter_plot


def plot_batch_overview(batch_frame):
    # region Docstring
    '''
    # Plot Batch Overview
    Creates a Plotly subplots figure shown on the batch index

    ### Returns HTML of chart to be inserted in batch index.

    ### Parameters:{
    #### `batch_frame`: df of batch overview.
    ### }
    '''
    # endregion Docstring

    fig = make_subplots(rows=3, cols=3,
                        specs=[[{'colspan': 3, 'rowspan': 2}, None, None],
                               [None, None, None],
                               [{}, {}, {}],
                               ],
                        subplot_titles=("Profit Over Time",
                                        "Profit/Loss x Exposure",
                                        "Min Unreal x Max Unreal",
                                        "PL x Volatility",
                                        )
                        )

    not_traded = batch_frame[batch_frame.min_unreal == 0]
    not_traded = not_traded[not_traded.max_unreal == 0]
    traded = batch_frame.drop(not_traded.index.tolist())
    resolved = traded[traded.unreal_pl == 0]
    unresolved = traded.drop(resolved.index.tolist())

    unres_color, not_color, res_color = get_colors(num_of_colors=3,
                                                   hue_start_value=289,
                                                   cut_div=4)
    res_color = '#209C81'

    if len(resolved) != 0:
        resolved_progress = new_line_plot(
            x_values=list(range(len(resolved))),
            y_values=resolved.real_pl.cumsum(),
            text=resolved.tick_date,
            color=res_color,
            name='Resolved Profit')
        fig.append_trace(resolved_progress, row=1, col=1)

        fig = add_box_scatter_cross(
            fig, 3, 1, resolved.real_pl, resolved.max_ex, resolved.tick_date, res_color)
        fig = add_box_scatter_cross(
            fig, 3, 2, resolved.min_unreal, resolved.max_unreal, resolved.tick_date, res_color)
        fig = add_box_scatter_cross(
            fig, 3, 3, resolved.real_pl, resolved.avg_vola, resolved.tick_date, res_color)

    if len(unresolved) != 0:
        unresolved_progress = new_line_plot(
            x_values=list(range(len(unresolved))),
            y_values=unresolved.real_pl.cumsum(),
            text=unresolved.tick_date,
            color=unres_color,
            name='Unresolved Profit')
        fig.append_trace(unresolved_progress, row=1, col=1)

        fig.append_trace(go.Scatter(x=unresolved.real_pl, y=unresolved.max_ex,
                                    text=unresolved.tick_date, mode='markers', marker_color=unres_color), row=3, col=1)
        fig.append_trace(go.Scatter(x=unresolved.min_unreal, y=unresolved.max_unreal,
                                    text=unresolved.tick_date, mode='markers', marker_color=unres_color), row=3, col=2)
        fig.append_trace(go.Scatter(x=unresolved.real_pl, y=unresolved.avg_vola,
                                    text=unresolved.tick_date, mode='markers', marker_color=unres_color), row=3, col=3)

    if len(not_traded) != 0:
        fig.append_trace(go.Scatter(x=not_traded.real_pl, y=not_traded.max_ex,
                                    text=not_traded.tick_date, mode='markers', marker_color=not_color), row=3, col=1)
        fig.append_trace(go.Scatter(x=not_traded.min_unreal, y=not_traded.max_unreal,
                                    text=not_traded.tick_date, mode='markers', marker_color=not_color), row=3, col=2)
        fig.append_trace(go.Scatter(x=not_traded.real_pl, y=not_traded.avg_vola,
                                    text=not_traded.tick_date, mode='markers', marker_color=not_color), row=3, col=3)

    fig.update_layout(
        template='plotly_dark',
        # title_text="Batch Results",
        height=1200,
        showlegend=False
    )

    # fig.show()
    # fig.to_html(str(batch_path / "overview.html"))
    html = fig.to_html(include_plotlyjs='cdn', full_html=False)
    return html


def get_orders(filled_orders) -> 'df':
    # region Docstring
    '''
    # Get Orders
    Convert `filled_orders` global variables to a df that is used in the trading charts. 

    ### Returns dataframe of orders 

    ## Parameters:{
    ####    `filled_orders`: global variable df
    ## }

    '''
    # endregion Docstring
    # convert it to a df that will be easier to plot
    df = convert_orders(filled_orders)
    # add on several columns , calculating pl and average
    df = update_orders(df)
    # add other columns for plotting...
    o = append_o_notes(df)
    return o


def expand_mkt_data(m, o):
    # region Docstring
    '''
    # Expand Market Data
    Expands upon the market data which adds the following:
    - average 
    - position
    - PL real
    - PL Unreal

    #### Returns DataFrame of Market Data

    ## Parameters:{
    ####    `m`: market data df
    ####    `o`: orders data df
    ## }
    '''
    # endregion Docstring
    # these functions are pretty self explanatory...
    m = append_avg(m, o)
    m = append_position(m, o)
    m = append_PL(m, o)
    m = append_PLs(m)
    return m


def plot_results(current_frame, filled_orders, batch_path, directory, csv_name):
    # region Docstring
    '''
    # Plot Results
    All in one function for creating daily chart html.  

    ## Parameters:{
    ####    `current_frame`: global variable df,
    ####    `filled_orders`: global variable df,
    ####    `batch_path`: global variable defined batch path
    ####    `directory`: global variable defined directory
    ####    `csv_name`: name of file traded
    ## }
    '''
    # endregion Docstring
    o = get_orders(filled_orders)
    m = expand_mkt_data(current_frame, o)
    e_frame = max_exposures(o, m)

    get_trading_charts(o, m, e_frame, 'Today', 1000, batch_path=batch_path,
                       html_path=directory, plot=False, csv_name=csv_name)


def max_exposures(orders, mkt_data):
    '''
    # Max Exposures
    Takes `orders` df and `mkt_data` df and finds the max exposure per minute.

    Returns `exposure_frame` - two columns with time and exposure.

    # Process:

    # 1) Create a list of minutes.

    # 2) For each minute, go through each order in minute
    - If there are no orders in the given minute, append last known exposure and continue.
    - If there are no orders active, exposure is 0...

    # 3) After each minute is complete, find the max exposure from that minute and append it to the Exposures list.

    # 4) Create the e_frame and return it.

    '''
    buys = pd.DataFrame()
    exposures = []
    last_ex_in_min = 0

    # 1) Create a list of minutes.
    minutes = sorted(list(set(mkt_data.time)))

    for minute in minutes:
        minute_max = []
        df = orders[orders.time == minute]
        if len(df) == 0:
            exposures.append(last_ex_in_min)
            continue

        minute_max.append(df.dol_inv.max())
        minute_max.append(last_ex_in_min)
        last_ex_in_min = df.dol_inv.tolist()[-1]
        exposures.append(max(minute_max))

    e = pd.DataFrame({'exposure': exposures, 'time': minutes})
    return e


def convert_orders(df):
    type2 = []
    qty_list = []
    for order, qty in zip(df.buy_or_sell, df.qty):
        if order == 'BUY':
            type2.append('TO OPEN')
            qty_list.append(qty)
        else:
            type2.append('TO CLOSE')
            qty_list.append(qty*-1)

    df['type2'] = type2
    df['quantity'] = qty_list

    df = df.rename(columns={'buy_or_sell': 'buyorsell',
                            'exe_price': 'avgprice', 'exe_time': 'time'})
    columns = ['time', 'buyorsell', 'quantity', 'type2', 'ticker', 'avgprice']
    df = df[columns]
    return df


def update_orders(orders):
    '''Takes the default orders dataframe and adds some crucial rows.

    Rows added are: "rolling shares", "rolling average", "dollars invested" and "rolling P/L".

    In addition, this function will round the time of each order row to the nearest minute value. '''
    orders['time'] = orders.time.apply(pd.to_datetime).dt.time

    stocklist = orders.ticker
    stocklist = list(dict.fromkeys(stocklist))

    dfx = pd.DataFrame()

    for stock in stocklist:

        dfz = orders[orders.ticker == stock].sort_values(by='time')

        dfz['rs'] = dfz.quantity.cumsum().apply(int)

        def correct_type(dfz):

            types = []
            last_y = 0

            for x, y in zip(dfz.type2, dfz.rs):
                if last_y == 0:
                    types.append('TO OPEN')
                elif (last_y <= .01) & (last_y >= -.01):
                    types.append('TO OPEN')
                else:
                    types.append(x)
                last_y = y

            dfz = dfz.drop('type2', axis=1)
            dfz['type'] = types

            return dfz

        dfz = correct_type(dfz)

        def rounding_time(dfz):
            times = []

            # This loop breaks up each time into the hour, minute and second and then rounds to the nearest minute.
            # This is to align with the market data for graphing over-top.
            for x in dfz.time:
                hr, mt, sc = str(x).split(':')

                if len(mt) == 1:
                    mt = "0"+mt
                # recreate the string with rounded minute.
                times.append(hr+':'+mt+':00')

            # redefine the df column.
            dfz = dfz.rename(columns={'time': 'o_time'})
            dfz['time'] = times
            # add all info to dfx in each loop of stocks.

            return dfz

        dfz = rounding_time(dfz)

        '''----- Rolling Average and Profit / Loss - ----'''

        # Start with some default pl of 0 and some empty lists to fill and make columns.
        ravg = []
        pl = 0
        pl_over = []

        buys = pd.DataFrame()

        # By default short is false  -
        # this cuts down on the amount of assignments needed in if then statements.
        short = False

        for x, y, a, b in zip(dfz.type, dfz.quantity, dfz.avgprice, dfz.rs):

            # Was getting some errors with type compliance, so I went ahead and converted
            # these to floats to avoid the errors.
            y = float(y)
            a = float(a)
            b = float(b)

            # Determines if position is long or short.
            if x == 'TO OPEN':
                if y < 0:
                    short = True
                else:
                    short = False
            else:
                if y > 0:
                    short = True
                else:
                    short = False

            # Fills is another df that is used to add to the buys df.
            # Each for loop creates another row in the buys df
            fills = pd.DataFrame()
            fills['quantity'] = [y]
            fills['avgprice'] = [a]

            # This if statement is for when I don't have any more shares (I'm flat)
            if b == 0:

                # y is used to calculate PL for both short and long, but can be negative if you sold long.
                # This makes sure the y value is positive for the pl calculation.
                if y < 0:
                    y = y * -1

                # While shorting, the calculated last_avg may be negative, which we need to negate in order
                # to correctly calculate profit loss.
                if last_avg < 0:
                    last_avg = last_avg*-1

                # Two calculations - one for short, one for long.
                if short == True:
                    pl += (last_avg - a)*y

                else:
                    pl += (a - last_avg)*y

                # When I don't have shares, the buys df resets because the orders are all sold.
                buys = pd.DataFrame()
                ravg.append('Nan')

            else:  # as in - I DO have shares still invested...
                # if I'm opening new positions, I need to append those to the buys df.
                # to be added to the rest.
                if x == 'TO OPEN':
                    buys = buys.append(fills, sort=True)

                elif x == 'TO CLOSE':
                    # Due to how the rows are appended from the fills df, the index may have numbers with all zeros.
                    # This corrects that.
                    buys = buys.reset_index()
                    buys = buys.drop('index', axis=1)

                    # This var is not named that well because it isnt actually an average.
                    # It refers to the amount of dollars that were sold.
                    # Later on I use sold_av / quantity to get the true average of the shares sold
                    # - which is then used to calculate Profit Loss.
                    sold_av = 0

                    # Long Close
                    # Below this if statement, there is a very similar code for shorting.
                    # These notes really apply there too
                    if y < 0:

                        # remainder is the number of shares you are subtracting from each buys row
                        # Starting at the top (earliest buys...)
                        remainder = y

                        # the buys df will be edited during the for loop, so I thought it would be
                        # a good idea to make a copy at the start of it to stop any weird stuff happening.
                        b2 = buys.copy()
                        for z in b2.quantity:

                            # when closing long positions, the remainder value will start off negative
                            # So really this is saying: as long as there are still shares to take off, proceed.
                            if remainder < 0:

                                # The buys df is row after row of orders, the topmost rows being the first (earliest) placed.
                                # This looks at the first placed value in the quantity (num of shares) col
                                # If the first quantity in buys MINUS the amount of shares that are being sold is less than 0,
                                # That means that the # of shares sold is larger than the shares in that row.
                                if (list(buys.quantity)[0] + remainder) <= 0:

                                    # If the row is depleted, then add the amount of capital I had in that
                                    # row to sold_av. This may happen several times.
                                    # buys.dol is calculated at the end of this for loop, but is essentially
                                    # just (avg price)*(share qty)
                                    sold_av += list(buys.dol)[0]
                                else:

                                    # In the event that the row isn't taken out by the remainder, then we take
                                    # the rest of the remainder, make it positive, and multiply it by the avg
                                    # price of the row. Then add that to sold_av.
                                    sold_av += (remainder*-1) * \
                                        (list(buys.avgprice)[0])

                                # these last three lines actually update the dataframe.
                                # update the quantity value of row 1 of the df.
                                buys.iloc[0:1, 2] = buys.iloc[0:1,
                                                              2] + remainder
                                # Update remainder. For loop will assess every time if there are shares remaining.
                                remainder = z + remainder
                                # if the remainder is larger than the row qty, then the row gets deleted
                                buys = buys[buys.quantity > 0]
                            else:
                                break

                        # calcuate pl using the sold_av, the order quantity, and order price.
                        pl += (a - (sold_av/(y*-1)))*(y*-1)

                    # Short Close
                    # Essentially the same as Long close but with negated values.
                    if y > 0:
                        remainder = y
                        b2 = buys.copy()
                        for z in b2.quantity:
                            if remainder > 0:
                                if (list(buys.quantity)[0] + remainder) >= 0:
                                    sold_av += (list(buys.dol)[0])*-1
                                else:
                                    sold_av += (remainder) * \
                                        (list(buys.avgprice)[0])
                                buys.iloc[0:1, 2] = buys.iloc[0:1,
                                                              2] + remainder
                                remainder = z + remainder
                                buys = buys[buys.quantity < 0]
                            else:
                                break

                        pl += (a - (sold_av/(y)))*(y*-1)

                # buys dollars invested is calculated to calculate average.
                buys['dol'] = buys.quantity*buys.avgprice
                bprices = buys.dol.sum()
                bquant = buys.quantity.sum()
                ravg.append(bprices/bquant)
                # last_avg is saved in the event that the next order is to go flat.
                last_avg = (bprices/bquant)

            pl_over.append(pl)

        # Adds some columns to the rows. Rolling Average, Dollars invested, and Profit Loss.
        dfz['ravg'] = ravg
        dfz['dol_inv'] = (dfz.ravg*dfz.rs)
        dfz = dfz.replace({'dol_inv': ''}, 0)

        dfz['real_pl'] = pl_over

        dfx = dfx.append(dfz)

    return dfx


def append_o_notes(o):
    '''Takes a dataframe of orders and adds columns that are useful for graphing.

    The columns created will be "scolor", "sig" and "annotes".
    The "Sig" column is a string that tells you what type of order - Buy(B) Sell(S) or Buy Short(Bs)
    The "scolor" column is the color that will be graphed for each signal(sig)
    The "Annote" column will show information about the number of shares bought at what price.'''

    # Create empty lists to be converted to columns.
    sig = []
    annote = []
    colist = []

    # Going through each line of dataframe and calculating above values.
    for x, y, z, a in zip(o.buyorsell, o.type, o.quantity, o.avgprice):
        z = float(z)
        a = float(a)

        # Sigcolor defaults to buy.
        sigcol = 'rgba(51,204,255,0.5)'  # '#6dbee3'
        if x == 'BUY':
            # Opening Long
            if y == 'TO OPEN':
                mark = 'B'
            # Closing Short
            else:
                mark = 'S'

        else:
            # Opening Short
            if y == 'TO OPEN':
                mark = 'Bs'
            # Closing Long
            else:
                mark = 'S'

        # this makes all order quantities positive.
        if z < 0:
            z = int(z)*-1

        # this second block creates the annote column.
        # If is for sell, elif is for buy short and else is for buy long.
        # you can see that buy and sell colors are already built in here.
        if mark == 'S':
            note = '-'+f'{z:,}'+' @ $'+str(a)
            sigcol = 'rgba(255,255,102,0.5)'  # '#ebeb4d'
        elif mark == 'Bs':
            note = f'{z:,}'+' @ $'+str(a)
            sigcol = 'rgba(204,0,102,0.5)'  # '#c678cc'
        else:
            note = f'{z:,}'+' @ $'+str(a)

        # at the end of each for loop append value to lists.
        colist.append(sigcol)
        sig.append(mark)
        annote.append(note)

    o['scolor'] = colist
    o['sig'] = sig
    o['annote'] = annote

    return o


def append_PL(mkt_data, order_data):
    '''Function:
    Takes the realized Profit Loss info from order data df and transfers the data to a new
    column in the market data df.

    Inputs:
    {
    mkt_data: df of market information from day traded.
    order_data: df of order info from day traded.
    }'''

    import pandas as pd

    # create df to return.
    dfz = pd.DataFrame()

    # list of stocks with no repeats.
    stocklist = mkt_data.ticker
    stocklist = list(dict.fromkeys(stocklist))

    for x in stocklist:

        # Filter orders and mkt data by current stock
        ox = order_data[order_data.ticker == x].sort_values(by='time')

        dfx = pd.DataFrame(
            mkt_data[mkt_data.ticker == x]).sort_values(by='time')

        # create empty list to append to and default starting value for pl.
        plist = []
        pl = 0

        for a in dfx.time:
            o = ox[ox.time == a]

            # If the length of the orders df isn't 0, that means there are orders during that minute.
            if len(o) != 0:
                # takes the last value that minute...
                x = o.sort_values(by='o_time').tail(1).real_pl.mean()

                if pl != x:  # if the data is different than it was, update it.
                    pl = x

            plist.append(pl)

        dfx['pl'] = plist
        dfz = dfz.append(dfx)
    return dfz


def append_PLs(mkt_data):
    '''Function:
    To add two columns to market data - an unrealized high, and an unrealized low.
    These show the range of unrealized profits from minute to minute.
    Note: YOU MUST HAVE ALREADY USED THE FUNCTION "append_PL" as this func used the column generated there.

    Inputs:
    {
    mkt_data: df of minute by minute market data containing a profit loss column and high low values.
    }'''

    import pandas as pd

    # df to be returned.
    dfz = pd.DataFrame()

    # stocklist with no redundancies.
    stocklist = mkt_data.ticker
    stocklist = list(dict.fromkeys(stocklist))

    for x in stocklist:

        dfx = pd.DataFrame(
            mkt_data[mkt_data.ticker == x]).sort_values(by='time')

        hpl = []
        lpl = []
        pos = 0
        pl = 0

        for a, b, c, d, e in zip(dfx.high, dfx.low, dfx.rs, dfx.ravg, dfx.pl):

            # if flat, no there is no unrealized profit/loss.
            if c == 'Nan':
                highr = 'Nan'
                lowr = 'Nan'

            else:
                a = float(a)
                b = float(b)
                d = float(d)

                # values if short (rolling shares are negative)
                if int(c) < 0:
                    lowr = ((d - a)*c*-1)+pl
                    highr = ((d - b)*c*-1)+pl

                # values when long.
                else:
                    highr = ((a - d)*c)+pl
                    lowr = ((b - d)*c)+pl

            hpl.append(highr)
            lpl.append(lowr)
            # saves last pl value for each loop iteration.
            pl = float(e)

        dfx['hpl'] = hpl
        dfx['lpl'] = lpl
        dfz = dfz.append(dfx)
    return dfz


def append_avg(mkt_data, order_data):
    '''Function:
    Adds a column to market data df that tracks the average price of open orders every minute.
    Does this by scraping info from the orders dataframe.

    Inputs:
    {
    mkt_data: df of market data
    order_data: df of order data
    }

    '''
    import pandas as pd
    dfz = pd.DataFrame()

    # creates list of stocks without repeats.
    stocklist = mkt_data.ticker
    stocklist = list(dict.fromkeys(stocklist))

    for x in stocklist:

        # filter both orders and mkt data by ticker
        ox = order_data[order_data.ticker == x].sort_values(by='time')
        dfx = pd.DataFrame(
            mkt_data[mkt_data.ticker == x]).sort_values(by='time')

        # start with empty list and blank average (because I would be flat at beginning of day.)
        avp = []
        av = 'Nan'

        for a in dfx.time:
            # filter orders for each minute in mkt_data
            o = ox[ox.time == a]

            # if there is at least 1 order entry in that minute, iterate through orders.
            if len(o) != 0:
                x = o.sort_values(by='o_time').tail(1).rs.mean()
                y = o.sort_values(by='o_time').tail(1).ravg.mean()
                # for x, y in zip(o.rs,o.ravg): ### Essentially, this for loop takes the last average of the minute
                if x != 0:
                    av = y
                # This is if the order closes all positions - making me flat.
                else:
                    av = 'Nan'

            avp.append(av)

        dfx['ravg'] = avp
        dfz = dfz.append(dfx)
    return dfz


def append_position(mkt_data, order_data):
    '''
    Function:
    creates new column for market data df.
    This column is created by using info from the thinkorswim orders.

    Inputs:
    {
    mkt_data: df of market data
    order_data: df of order data
    }
    '''
    import pandas as pd
    dfz = pd.DataFrame()

    # creates list of stocks without duplicates.
    stocklist = mkt_data.ticker
    stocklist = list(dict.fromkeys(stocklist))

    for x in stocklist:

        # filter both orders and mkt data by ticker each loop.
        ox = order_data[order_data.ticker == x].sort_values(by='time')
        dfx = pd.DataFrame(
            mkt_data[mkt_data.ticker == x]).sort_values(by='time')

        pos_list = []
        pos = 'Nan'

        for a in dfx.time:
            # filter orders for each minute in mkt_data
            o = ox[ox.time == a]

            # if there is at least 1 order entry in that minute, iterate through orders.
            if len(o) != 0:
                for x in o.rs:

                    if x == 0:
                        pos = 'Nan'  # if I don't own any shares, then don't append anything,
                    else:
                        pos = int(x)  # otherwise, append the value

            pos_list.append(pos)

        dfx['rs'] = pos_list
        dfz = dfz.append(dfx)
    return dfz


def get_trading_charts(orders, mkt_data, e_frame, date, height, batch_path=None, html_path=False, csv_name=None, plot=True):
    '''Function:
    Creates a table showing minute by minute data and overlays trades.
    Also shows info like position size and profit loss in depth.

    Inputs:
    {
    orders: a dataframe of orders from thinkorswim.

    mkt_data: a dataframe of market data for minute by minute pricing data.

    date: a string with the format "yyyy-mm-dd"

    height: integer value. y dimension of daily graph. 800-1000 is good to start.

    table: Defaults to "True". creates a table of fundamental data above daily chart.

    yearly: Defaults to "True". Shows yearly chart above daily chart for day by day
    chart history.

    notes: appends a table for each stock traded that shows notes I've written showing my thoughts on the stock.

    OnDemand: Defaults to False - only if you say true does this default to getting fundamentals from a different source.

    html: creates html plot for viewing later.

    plot: whether or not it outputs the plot.
    }
    '''

    # Creates a list of stocks without repeats.
    stocklist = mkt_data.ticker
    stocklist = list(dict.fromkeys(stocklist))

    for x in stocklist:

        # Create a df for each stock
        df = mkt_data[mkt_data.ticker == x]
        df['high'] = df.high.astype(float)
        df['low'] = df.low.astype(float)

        # Create orders just for the current stock.
        o = orders[orders.ticker == x]

        import plotly.graph_objects as go

        # xax is an axis with every minute from 9:30 to 4:00
        xax = df.time
        # xax2 only has times noted in order df.
        xax2 = o.time

        # Create figure
        fig = go.Figure()

        # Add traces
        # ---- CandleSticks
        pricing = go.Candlestick(x=df.time,
                                 open=df.open, high=df.high,
                                 low=df.low, close=df.close,
                                 line_width=.5, increasing_line_color='#0fba51',
                                 decreasing_line_color='#b5091d',
                                 name="pricing",
                                 yaxis="y2",
                                 #                         hoverinfo='text',
                                 showlegend=False

                                 )

        fig.add_trace(pricing)

        # This isn't working right now. may be interesting to look into.

        def toggle_hover(trace, points, state):
            trace.hoverinfo == 'all'

        pricing.on_click(toggle_hover)

        # ---- overlay average price
        avgcolor = 'rgba(255,153,102,0.8)'  # '#ab4e1b'#'#6dbee3'
        fig.add_trace(go.Scatter(x=xax, y=df.ravg, line=dict(
            color=avgcolor,
            shape='hv', width=1.3,
            dash="dash"), mode='lines',
            name='average price', yaxis='y2'))

        dollar_volume = df.volume.astype(float)*df.close.astype(float)

        # Low to High:
        # 7a7a7a -- Gray
        # 130933
        # 0d1147
        # 102f5b
        # 145670
        # 17847f
        # 1b986a
        # 1fac4b
        # 24c022
        # 60d426
        # a2db37

        dol_vol_cols = []
        for y in dollar_volume:
            if y < 10000:
                dol_vol_cols.append('#7a7a7a')
            elif (y >= 10000) and (y < 25000):
                dol_vol_cols.append('#130933')
            elif (y >= 25000) and (y < 50000):
                dol_vol_cols.append('#0d1147')
            elif (y >= 50000) and (y < 75000):
                dol_vol_cols.append('#102f5b')
            elif (y >= 75000) and (y < 100000):
                dol_vol_cols.append('#145670')
            elif (y >= 100000) and (y < 250000):
                dol_vol_cols.append('#17847f')
            elif (y >= 250000) and (y < 500000):
                dol_vol_cols.append('#1b986a')
            elif (y >= 500000) and (y < 1000000):
                dol_vol_cols.append('#1fac4b')
            elif (y >= 1000000) and (y < 1500000):
                dol_vol_cols.append('#24c022')
            elif (y >= 1500000) and (y < 200000):
                dol_vol_cols.append('#60d426')
            else:
                dol_vol_cols.append('#a2db37')

        # ---- Volume
        fig.add_trace(go.Bar(x=xax, y=dollar_volume,
                             marker_color=dol_vol_cols, yaxis='y', showlegend=False))

        # ---- Zero Line
        fig.add_trace(go.Scatter(x=['09:31:00', '16:00:00'], y=[100000, 100000],
                                 line=dict(color='#c2a31b', width=.7),
                                 mode='lines', yaxis='y', showlegend=False))

        poscolor = 'green'
        #
        #
        # ---- Zero Line
        fig.add_trace(go.Scatter(x=['09:31:00', '16:00:00'], y=[0, 0],
                                 line=dict(color='#d9d9db',
                                           dash="dash", width=.7),
                                 mode='lines', yaxis='y3', showlegend=False))

        # ---- Position Size
        fig.add_trace(go.Scatter(x=e_frame.time, y=e_frame.exposure,
                                 line=dict(
                                     shape='hv', color=poscolor, width=1.3),
                                 mode='lines', name='dollars_invested', yaxis='y3', showlegend=False))

        plcolor = '#faa441'
        #
        #
        #
        # ---- Zero Line
        fig.add_trace(go.Scatter(x=['09:31:00', '16:00:00'], y=[0, 0], line=dict(color='#d9d9db',
                                                                                 dash="dash", width=.7), mode='lines', yaxis='y4', showlegend=False))

        # ---- P/l High
        fig.add_trace(go.Scatter(x=xax, y=df.hpl, line=dict(color='green', shape='spline', width=.7),
                                 mode='lines', name='Unreal High', yaxis='y4'))

        # ---- P/l Low
        fig.add_trace(go.Scatter(x=xax, y=df.lpl, line=dict(color='red', shape='spline', width=.7),
                                 mode='lines', name='Unreal Low', yaxis='y4'))

        # ---- Profit Loss
        fig.add_trace(go.Scatter(x=xax, y=df.pl, line=dict(shape='hv',
                                                           color=plcolor, width=1.3),
                                 mode='lines', name='Realized P/L', yaxis='y4'))

        # ---- Trades
        fig.add_trace(go.Scatter(x=xax2, y=o.avgprice, mode='markers', marker=dict(size=5,
                                                                                   line=dict(width=.5, color='rgba(255,255,255,.4)')), marker_color=o.scolor,
                                 text=o.annote, name='Trades', yaxis='y2'))

        # Volatility...
        volatility = ((df.high - df.low)/df.low)*100

        # gray = '#7a7a7a'
        # purple = '#32207a'
        # blue = '#294e8e'
        # dark green = '#115e2f'
        # green = '#39bd57'
        # yellow = '#d0d61e'
        # white = '#ffffff'
        vol_cols = []
        for b in volatility:
            if b < 1.0:
                color = '#7a7a7a'
            elif (b >= 1.0) and (b < 1.25):
                color = '#32207a'
            elif (b >= 1.25) and (b < 2.50):
                color = '#294e8e'
            elif (b >= 2.50) and (b < 5.0):
                color = '#115e2f'
            elif (b >= 5) and (b < 10):
                color = '#39bd57'
            elif (b >= 10) and (b < 20):
                color = '#d0d61e'
            else:
                color = '#ffffff'
            vol_cols.append(color)

        fig.add_trace(go.Scatter(x=xax, y=volatility, mode='markers', marker_size=4.5,
                                 marker_color=vol_cols, yaxis='y5', name='Volatility in %', showlegend=False))

        # Update axes
        fig.update_layout(
            xaxis=go.layout.XAxis(
                autorange=True,
                fixedrange=False,
                range=['09:31:00', '16:00:00'],
                rangeslider=dict(
                    visible=False
                ),
                showgrid=True,
            ),

            # VOLUME
            yaxis=go.layout.YAxis(
                anchor="x",
                autorange=True,
                fixedrange=False,
                domain=[0, 0.1],
                linecolor="#673ab7",
                mirror=True,
                range=[df.low.min(), df.high.max()],
                showline=True,
                side="left",
                tickfont={"color": "#673ab7"},
                tickmode="auto",
                ticks="",
                title="Volume($)",
                titlefont={"color": "#673ab7"},
                type="linear",
                showgrid=False,
                zeroline=False
            ),

            # CANDLES
            yaxis2=go.layout.YAxis(
                anchor="x",
                autorange=True,
                fixedrange=False,
                domain=[0.2, 0.6],
                linecolor=avgcolor,
                mirror=True,
                # range=[df.volume.min(), df.volume.max()],
                showline=True,
                side="left",
                tickfont={"color": avgcolor},
                tickmode="auto",
                ticks="",
                title="Daily Chart",
                titlefont={"color": avgcolor},
                type="linear",
                zeroline=False,
                showgrid=True,
                gridwidth=.6,
                # gridcolor='#2b2b2b'
            ),

            # POSITION SIZE
            yaxis3=go.layout.YAxis(
                anchor="x",
                autorange=True,
                fixedrange=False,
                domain=[0.8, 1.0],
                linecolor=poscolor,
                mirror=True,
                range=[df.rs.astype(float)*df.ravg.astype(float).min(),
                       df.rs.astype(float)*df.ravg.astype(float).max()],
                showline=True,
                side="left",
                tickfont={"color": poscolor},
                tickmode="auto",
                ticks="",
                title="Position Size($)",
                titlefont={"color": poscolor},
                type="linear",
                showgrid=False,
                zeroline=False
            ),

            # PROFIT LOSS
            yaxis4=go.layout.YAxis(
                anchor="x",
                autorange=True,
                fixedrange=False,
                domain=[0.6, 0.8],
                linecolor=plcolor,
                mirror=True,
                # range=[df.hpl.min(), df.lpl.max()],
                showline=True,
                side="left",
                tickfont={"color": plcolor},
                tickmode="auto",
                ticks="",
                title='P/L in Depth',
                titlefont={"color": plcolor},
                type="linear",
                showgrid=False,
                zeroline=False
            ),

            # Volatility
            yaxis5=go.layout.YAxis(
                anchor="x",
                autorange=True,
                fixedrange=False,
                domain=[0.1, 0.2],
                linecolor="#E91E63",
                mirror=True,
                # range=[df.hpl.min(), df.lpl.max()],
                showline=True,
                side="left",
                tickfont={"color": "#E91E63"},
                tickmode="auto",
                ticks="",
                title="VIX (%)",
                titlefont={"color": "#E91E63"},
                type="linear",
                showgrid=False,
                zeroline=False
            )
        )

        # Update Layout here...
        fig.update_layout(
            # title=str(x)+" Minute Chart "+str(date),
            # xaxis_showgrid=False,

            xaxis_title="Time",
            dragmode="zoom",
            hovermode="x",
            legend=dict(traceorder="reversed"),
            # height can be changed for pc to laptop. 1500 is good for laptop...
            height=height,
            template="plotly_dark",
            margin=dict(
                t=100,
                b=100
            ), showlegend=True,
            # xaxis=dict(showgrid=True)
        )

        if html_path != False:

            # HTML path is the current directory.

            plot = fig.to_html(include_plotlyjs='cdn', full_html=False)

            template_path = str(
                Path.cwd() / 'batch_design' / 'plot_template.html')

            with open(template_path, 'r') as template:
                text = template.read()

            asset_path = str(Path.cwd() / 'batch_design' / 'assets')
            index_path = str(batch_path / 'batch_index.html')
            html_name = str(html_path / 'daily_chart.html')

            text = text.replace('^^^doc_name^^^', 'Daily Chart')
            text = text.replace('^^^csv_name^^^', csv_name)
            text = text.replace('^^^asset_path^^^', asset_path)
            text = text.replace('^^^index_path^^^', index_path)
            text = text.replace('^^^plot^^^', plot)

            with open(html_name, 'x') as f:
                f.write(text)


def plot_momentum(mom_frame, current_frame, path_to_folder, batch_path=None, csv_name=None):
    dfz = mom_frame
    df = current_frame

    fig = go.Figure()

    # Add traces
    # ---- CandleSticks
    pricing = go.Candlestick(x=df.time,
                             open=df.open, high=df.high,
                             low=df.low, close=df.close,
                             line_width=.5, increasing_line_color='#0fba51',
                             decreasing_line_color='#b5091d',
                             name="pricing",
                             #                 yaxis="y2",
                             #                         hoverinfo='text',
                             showlegend=True
                             )

    fig.add_trace(pricing)

    for stime, etime, trend, high, low, color in zip(dfz.start_time,
                                                     dfz.end_time,
                                                     dfz.trend,
                                                     dfz.high,
                                                     dfz.low,
                                                     dfz.color):

        if trend == 'uptrend':
            x_one = low
            x_two = high
        else:
            x_one = high
            x_two = low

        trace = go.Scatter(x=[stime, etime], y=[x_one, x_two],
                           mode='lines', line_color=color, showlegend=False)

        fig.add_trace(trace)

    fig.update_layout(
        xaxis=go.layout.XAxis(
            autorange=True,
            fixedrange=False,
            range=['09:31:00', '16:00:00'],
            rangeslider=dict(
                visible=False
            )
        ),  # VOLUME
        yaxis=go.layout.YAxis(
            anchor="x",
            autorange=True,
            fixedrange=False,
            range=[df.low.min(), df.high.max()],
            ticks="",
            type="linear",
            zeroline=False
        ))

    fig.update_layout(

        template="plotly_dark",
        margin=dict(
            t=100,
            b=100
        )  # ,showlegend = True
    )

    plot = fig.to_html(include_plotlyjs='cdn', full_html=False)

    from pathlib import Path
    template_path = str(
        Path.cwd() / 'batch_design' / 'plot_template.html')

    with open(template_path, 'r') as template:
        text = template.read()
        template.close()

    asset_path = str(Path.cwd() / 'batch_design' / 'assets')
    index_path = str(batch_path / 'batch_index.html')
    html_name = str(path_to_folder / 'mom_tracking.html')

    text = text.replace('^^^doc_name^^^', 'Momentum Tracking')
    text = text.replace('^^^csv_name^^^', csv_name)
    text = text.replace('^^^asset_path^^^', asset_path)
    text = text.replace('^^^index_path^^^', index_path)
    text = text.replace('^^^plot^^^', plot)

    with open(html_name, 'x') as f:
        f.write(text)
        f.close()


def create_batch_compare_graph(categories, category_labels):
    # from plotly.offline import init_notebook_mode, iplot
    # init_notebook_mode()

    traces = []
    for trace_list in categories[2:]:
        traces.extend(trace_list)

    steps = []
    for index, category in enumerate(categories):
        visible = []
        for trace in traces:
            if trace in category:
                visible.append(True)
            else:
                visible.append(False)
        step = dict(
            method='restyle',
            args=['visible', visible],
            label=category_labels[index]
        )
        steps.append(step)

    fig = go.Figure(data=traces)

    sliders = [dict(
        active=0,
        currentvalue={"prefix": "Showing: "},
        pad={
            "t": 50,
            "l": 0,
            "r": 350,
        },
        steps=steps
    )]

    fig.update_layout(
        template='plotly_dark',
        sliders=sliders,
        height=900
    )

    html = fig.to_html(include_plotlyjs='cdn', full_html=False)

    return html


def get_colors(hue_start_value='random', num_of_colors=3, s=71, v=75, cut_div=True):
    # region Docstring
    '''
    # Get Colors
    Gets Colors based on hsl. Converts and returns string in "rgb(x,x,x)" format 

    #### Returns ex

    ## Parameters:{
    ####    `hue_start_value`:
    ## }
    '''
    # endregion Docstring
    if hue_start_value == 'random':
        import random
        hue_start_value = random.randint(0, 360)

    import colorsys

    spectrum = 360
    if cut_div != False:
        spectrum /= cut_div
    div = spectrum / num_of_colors

    hue_start_value -= div

    x = 'x'
    template = [0, s/100.0, v/100.0]
    colors = []
    for color in range(num_of_colors):
        hue_start_value += div
        if hue_start_value > 360:
            hue_start_value -= 360
        template[0] = hue_start_value / 100.0

        colors.append(tuple(template))

    rgbs = []
    for color in colors:
        rgb = colorsys.hsv_to_rgb(*color)
        rgb = tuple(round(i * 255) for i in rgb)
        rgbs.append(f'rgb{rgb}')

    return rgbs


def plot_second_data(df, stop_at=390, y_axis='y'):
    if y_axis == 0:
        y_axis = 'y'
    else:
        y_axis = f'y{y_axis}'

    def create_time_axis(minute):
        times = []
        for sec in range(60):
            sec = str(sec)
            if len(sec) == 1:
                sec = f'0{sec}'
            t = minute[:6]+sec
            times.append(t)
        return times

    df = df.head(stop_at)
    fig = go.Figure()
    x_start = 0
    times = []
    for index in df.index:
        r = dict(df.iloc[index])
        o, h, l, c = r['open'], r['high'], r['low'], r['close']
        prices, volumes = hist.create_second_data(df, index, 'momentum')
        color = 'rgba(97, 97, 97, .5)'
        if o < c:
            # color = 'rgba(60, 122, 77, .5)'
            color = '#002b18'
        else:
            # color = 'rgba(145, 57, 54, .5)'
            color = '#2b0000'
        prices = pd.Series(prices)
        x_range = create_time_axis(r['time'])
        times.extend(x_range)
        fig.add_shape(
            type='rect',
            layer='below',
            line=dict(
                color=color,
                width=2,
            ),
            fillcolor=color,
            x0=x_range[0],
            x1=x_range[-1],
            y0=o,
            y1=c,
            xref='x',
            yref=y_axis,
            # legendgroup='candles'
        )
        fig.add_shape(
            type='rect',
            layer='below',
            line=dict(
                color=color,
                width=1,
            ),
            fillcolor=color,
            x0=x_range[25],
            x1=x_range[35],
            y0=l,
            y1=h,
            xref='x',
            yref=y_axis,
            # legendgroup='candles'
        )
        fig.add_trace(go.Scatter(x=x_range,
                                 y=prices,
                                 yaxis=y_axis,
                                 line_color='rgba(100, 100, 100, .4)',
                                 legendgroup='candles',
                                 showlegend=False))
        x_start += 60

    return fig


def new_yaxis(color, name, domain):
    axis = go.layout.YAxis(
        anchor="x",
        autorange=True,
        fixedrange=False,
        domain=domain,
        linecolor=color,
        # mirror=True,
        # showline=True,
        side="left",
        tickfont={"color": color},
        tickmode="auto",
        ticks="",
        title=name,
        titlefont={"color": color},
        type="linear",
        # zeroline=True,
        showgrid=False,
        gridwidth=.6,
        # gridcolor='#2b2b2b'
    )
    return axis


def deep_tracking_plot(gv):

    domain_for_pricing = .5
    fig, layout, tracker = deep_main_chart(gv, domain_for_pricing)
    variables = set(tracker.variable.values)
    domain_spacer = domain_for_pricing / len(variables)

    count = 0
    for v in variables:
        dfz = tracker[tracker.variable == v].sort_values(by='time')
        y = dfz.value.values
        x = dfz.time.values
        yaxis = f'y{count}'
        if count == 0:
            yaxis = 'y'

        trace = go.Scatter(x=x, y=y,
                           line=dict(shape='hv', width=1.3),
                           mode='lines', name=v, yaxis=yaxis, showlegend=False)

        yaxis = f'yaxis{count}'
        if count == 0:
            yaxis = 'yaxis'
        domain = [count*domain_spacer, (count + 1)*domain_spacer]
        layout[yaxis] = new_yaxis('blue', v, domain)
        count += 1
        fig.add_trace(trace)

    xaxis = go.layout.XAxis(
        autorange=True,
        fixedrange=False,
        rangeslider=dict(
            visible=False
        ),
        showgrid=False,
    )

    layout['xaxis'] = xaxis
    layout['template'] = 'plotly_dark'
    layout['height'] = 2000
    fig.update_layout(**layout)

    # plotly.offline.plot(fig)
    # plot = fig.to_html(include_plotlyjs='cdn', full_html=False)

    # with open('test.html', 'w') as f:
    #     f.write(plot)
    fig.show()


def plot_log(log, fig, layout, yaxis, domain):

    def convert_log(log):
        log = log.reset_index(drop=True)
        from local_functions.analyse.common import make_timestamp
        timestamps = []
        for minute, second in zip(log.minute, log.second):
            timestamps.append(make_timestamp(minute, second))

        log['ts'] = timestamps
        log_text = []
        for ts in sorted(list(set(timestamps))):
            messages = log[log['ts'] == ts].message.to_list()
            messages = list(map(lambda x: str(x)+'<br>', messages))
            message = ''
            for m in messages:
                message += m
            log_text.append(message)

        log_x = list(pd.unique(timestamps))
        log_y = [0] * len(log_x)
        return log_x, log_y, log_text

    log_x, log_y, log_text = convert_log(log)

    color = '#e39842'
    symbol = 'triangle-down-open'
    fig.add_trace(go.Scatter(x=log_x,
                             y=log_y,
                             yaxis=f'y{yaxis}',
                             mode='markers',
                             marker_color=color,
                             marker_symbol=symbol,
                             marker_size=10,
                             text=log_text,
                             showlegend=False))
    yaxis = f'yaxis{yaxis}'
    layout[yaxis] = new_yaxis(color, 'Log', domain)
    return fig, layout


def pricing_and_overlays(gv, domain):
    # Extract Variables
    tracker, average_df = extract_tracker_variable(
        tracker=gv.tracker, var='average')

    yaxis = len(pd.unique(tracker.variable)) + 1

    print('Plotting Second Data')
    fig = plot_second_data(df=gv.current_frame, y_axis=yaxis)

    # Momentum
    print('Plotting Momentum')
    fig = deep_plot_momentum(fig=fig, yaxis=yaxis, gv=gv)

    # Average
    print('Plotting Average')
    fig = deep_average_overlay(fig=fig, yaxis=yaxis, average_df=average_df)

    # Filled Orders
    print('Plotting Filled Orders')
    fig = deep_orders_overlay(
        fig=fig, yaxis=yaxis, order_specs=gv.order_specs, orders_df=gv.filled_orders)

    # Cancelled Orders
    print('Plotting Cancelled Orders')
    fig = deep_orders_overlay(
        fig=fig, yaxis=yaxis, order_specs=gv.order_specs, orders_df=gv.cancelled_orders, cancel=True)

    layout = {}
    yax = f'yaxis{yaxis}'
    layout[yax] = new_yaxis('green', 'Candles', domain)
    return fig, layout, tracker, yaxis


def deep_main_chart(gv, domain_start):

    def create_pricing_domains(domain_start):
        available_space = 1 - domain_start
        # PL, Exposure, Log
        overhead_space = .25*available_space
        overhead_spacing = [.1, .45, .45]

        pricing_space = .50*available_space

        # Volume, Volatility
        underneath_space = .25*available_space
        underneath_spacing = [.5, .5]

        under_domain = []
        for perc in underneath_spacing:
            spacer = underneath_space*perc
            under_domain.append([domain_start, domain_start+spacer])
            domain_start += spacer

        spacer = pricing_space*1
        pricing_domain = [domain_start, domain_start + spacer]
        domain_start += spacer

        over_domain = []
        for perc in overhead_spacing:
            spacer = overhead_space*perc
            over_domain.append([domain_start, domain_start+spacer])
            domain_start += spacer

        return over_domain, pricing_domain, under_domain

    over_domain, pricing_domain, under_domain = create_pricing_domains(
        domain_start)

    '''-------------------- Pricing and Overlays --------------------'''
    print('plotting pricing and overlays')
    fig, layout, tracker, last_axis = pricing_and_overlays(
        gv=gv, domain=pricing_domain)

    yaxis = last_axis + 1

    '''-------------------- PL --------------------'''
    print('plotting PL')
    yaxis += 1
    try:
        fig, layout = plot_pl(gv, fig, layout, yaxis, over_domain[2])
    except Exception as e:
        print(e)

    '''-------------------- EXPOSURE --------------------'''
    print('plotting Exposure')
    yaxis += 1
    try:
        fig, layout = plot_exposure(gv, fig, layout, yaxis, over_domain[1])
    except Exception as e:
        print(e)

    '''-------------------- LOG --------------------'''
    print('plotting Log')
    yaxis += 1
    try:
        fig, layout = plot_log(gv.log, fig, layout, yaxis, over_domain[0])
    except Exception as e:
        print(e)

    '''-------------------- VOLUME --------------------'''
    print('plotting Volume')
    yaxis += 1
    try:
        fig, layout = plot_volume(gv, fig, layout, yaxis, under_domain[0])
    except Exception as e:
        print(e)

    '''-------------------- VOLATILITY --------------------'''
    print('plotting Volatility')
    yaxis += 1
    try:
        fig, layout = plot_volas(gv, fig, layout, yaxis, under_domain[1])
    except Exception as e:
        print(e)

    return fig, layout, tracker


def deep_average_overlay(fig, yaxis, average_df):
    y_ax = f'y{yaxis}'
    if yaxis == 0:
        y_ax = 'y'
    x_vals = average_df.time.values
    y_vals = average_df.value.values
    avgcolor = 'rgba(255,153,102,0.8)'  # '#ab4e1b'#'#6dbee3'
    fig.add_trace(go.Scatter(x=x_vals, y=y_vals, line=dict(
        color=avgcolor,
        shape='hv', width=1.3,
        dash="dash"), mode='lines',
        name='average price', yaxis=y_ax))

    return fig


def plot_volume(gv, fig, layout, yaxis, domain):
    from local_functions.analyse.common import make_timestamp
    vol_vals = gv.current_frame.volume.values*gv.current_frame.close.values
    vol_colors = volume_colors(vol_vals)
    times = gv.current_frame.time.values
    for vol, color, time in zip(vol_vals, vol_colors, times):

        fig.add_shape(
            type='rect',
            layer='below',
            line=dict(
                color=color,
                width=2,
            ),
            fillcolor=color,
            x0=make_timestamp(time, 1),
            x1=make_timestamp(time, 59),
            y0=0,
            y1=vol,
            xref='x',
            yref=f'y{yaxis}',
            # legendgroup='candles'
        )

    times = gv.volume_frame.pop('time')
    times = list(map(lambda x: make_timestamp(x, 30), times))

    extrap = gv.volume_frame.pop('extrap_current')
    for entry in gv.volume_frame.columns:
        y_vals = gv.volume_frame[entry]
        if entry == 'mean':
            color = 'orange'
        else:
            color = 'rgba(100, 100, 100, .5)'
        fig.add_trace(go.Scatter(x=times, y=y_vals, line=dict(
            color=color,
            shape='linear', width=1.3), mode='lines',
            name=entry, yaxis=f'y{yaxis}'))

    yaxis = f'yaxis{yaxis}'
    layout[yaxis] = new_yaxis('orange', 'Vol ($)', domain)
    return fig, layout


def plot_volas(gv, fig, layout, yaxis, domain):
    from local_functions.analyse.common import make_timestamp, get_volatility
    highs, lows = gv.current_frame.high.values, gv.current_frame.low.values
    volas = get_volatility(highs, lows)
    times = gv.current_frame.time.values
    times = list(map(lambda x: make_timestamp(x, 30), times))
    colors = vola_colors(volas)

    volatility_trace = go.Scatter(x=times,
                                  y=volas,
                                  mode='markers',
                                  marker_color=colors,
                                  marker_size=13,
                                  marker_symbol='diamond-open-dot',
                                  name='Volatility',
                                  yaxis=f'y{yaxis}')

    vf = gv.volas_frame
    c = vf.pop('current')
    times = vf.pop('time')
    times = list(map(lambda x: make_timestamp(x, 30), times))
    for entry in vf.columns:
        y_vals = vf[entry]
        if entry == 'mean':
            color = 'orange'
        else:
            color = 'rgba(100, 100, 100, .5)'
        fig.add_trace(go.Scatter(x=times, y=y_vals, line=dict(
            # color=avgcolor,
            shape='linear', color=color, width=1.3), mode='lines',
            name=entry, yaxis=f'y{yaxis}'))

    fig.add_trace(volatility_trace)

    yaxis = f'yaxis{yaxis}'
    layout[yaxis] = new_yaxis('orange', 'Vola (%)', domain)
    return fig, layout


def deep_orders_overlay(fig, yaxis, order_specs, orders_df, cancel=False):
    y_ax = f'y{yaxis}'
    if yaxis == 0:
        y_ax = 'y'

    def convert_to_string_vals(dictionary):
        for entry in dictionary.keys():
            dictionary[entry] = str(dictionary[entry])
        return dictionary
    orders_df = orders_df.reset_index(drop=True)
    for order in orders_df.index:
        order = dict(orders_df.iloc[order])
        if cancel:
            symbol = 'circle'
            size = 5
        else:
            symbol = 'diamond'
            size = 10

        if order['buy_or_sell'] == 'BUY':
            color = 'rgba(51,204,255,0.5)'
            if cancel:
                color = 'rgba(25,100,125,0.5)'
        else:
            color = 'rgba(255,255,102,0.5)'
            if cancel:
                color = 'rgba(125,125,50,0.5)'
        oid = int(str(order['order_id']).strip('x'))
        spec = dict(order_specs[order_specs.order_id == oid].iloc[0])
        x_vals = [order['send_time'], order['exe_time']]
        y_vals = [order['exe_price']] * 2
        spec_s = convert_to_string_vals(spec)
        order_s = convert_to_string_vals(order)
        send_text = json.dumps(spec_s, indent=2).replace('\n', '<br>')
        exe_text = json.dumps(order_s, indent=2).replace('\n', '<br>')
        texts = [send_text, exe_text]
        fig.add_trace(go.Scatter(x=x_vals,
                                 y=y_vals,
                                 yaxis=y_ax,
                                 line_color=color,
                                 marker_symbol=symbol,
                                 marker_size=size,
                                 text=texts,
                                 showlegend=False))
    return fig


def extract_tracker_variable(tracker, var):
    tracker = tracker.reset_index(drop=True)
    var = tracker[tracker['variable'] == var]
    tracker = tracker.drop(var.index.to_list())
    return tracker, var


def volume_colors(vol_list):
    dol_vol_cols = []
    for y in vol_list:
        if y < 10000:
            dol_vol_cols.append('#7a7a7a')
        elif (y >= 10000) and (y < 25000):
            dol_vol_cols.append('#130933')
        elif (y >= 25000) and (y < 50000):
            dol_vol_cols.append('#0d1147')
        elif (y >= 50000) and (y < 75000):
            dol_vol_cols.append('#102f5b')
        elif (y >= 75000) and (y < 100000):
            dol_vol_cols.append('#145670')
        elif (y >= 100000) and (y < 250000):
            dol_vol_cols.append('#17847f')
        elif (y >= 250000) and (y < 500000):
            dol_vol_cols.append('#1b986a')
        elif (y >= 500000) and (y < 1000000):
            dol_vol_cols.append('#1fac4b')
        elif (y >= 1000000) and (y < 1500000):
            dol_vol_cols.append('#24c022')
        elif (y >= 1500000) and (y < 200000):
            dol_vol_cols.append('#60d426')
        else:
            dol_vol_cols.append('#a2db37')
    return dol_vol_cols


def vola_colors(vola_list):
    vola_cols = []
    for b in vola_list:
        if b < 1.0:
            color = '#7a7a7a'
        elif (b >= 1.0) and (b < 1.25):
            color = '#32207a'
        elif (b >= 1.25) and (b < 2.50):
            color = '#294e8e'
        elif (b >= 2.50) and (b < 5.0):
            color = '#115e2f'
        elif (b >= 5) and (b < 10):
            color = '#39bd57'
        elif (b >= 10) and (b < 20):
            color = '#d0d61e'
        else:
            color = '#ffffff'
        vola_cols.append(color)
    return vola_cols


def plot_pl(gv, fig, layout, yaxis, domain):
    tracked = ['unreal', 'real']
    colors = ['#e05875', '#e0b558']
    for entry, color in zip(tracked, colors):
        _, var_df = extract_tracker_variable(gv.pl_ex_frame, entry)
        if len(var_df) == 0:
            continue
        y_values = var_df.value.tolist()
        x_values = var_df.time.tolist()
        if entry == 'real':
            x_values.append(gv.current_frame.time.tolist()[-1])
            y_values.append(y_values[-1])

        fig.add_trace(go.Scatter(x=x_values, y=y_values, line=dict(
            shape='hv', width=2, color=color), mode='lines',
            name=entry, yaxis=f'y{yaxis}'))

    yaxis = f'yaxis{yaxis}'
    layout[yaxis] = new_yaxis(color, 'P&L', domain)
    return fig, layout


def plot_exposure(gv, fig, layout, yaxis, domain):
    _, ex_df = extract_tracker_variable(gv.pl_ex_frame, 'last_ex')
    y_values = ex_df.value.values
    x_values = ex_df.time.values
    color = '#367dbf'

    fig.add_trace(go.Scatter(x=x_values, y=y_values, line=dict(
        color=color,
        shape='hv', width=1.3), fill='tozeroy', mode='lines',
        name='Exposure', yaxis=f'y{yaxis}'))

    yaxis = f'yaxis{yaxis}'
    layout[yaxis] = new_yaxis(color, 'Exposure', domain)
    return fig, layout


def deep_plot_momentum(fig, yaxis, gv):
    from local_functions.analyse.common import make_timestamp
    mom_frame = gv.mom_frame
    if len(mom_frame) == 0:
        return fig

    mom_frame['start_time'] = mom_frame.start_time.apply(
        lambda x: make_timestamp(x, 30))
    mom_frame['end_time'] = mom_frame.end_time.apply(
        lambda x: make_timestamp(x, 30))
    for index in gv.mom_frame.index:
        row = dict(gv.mom_frame.iloc[index])
        x_vals = [row['start_time'], row['end_time']]
        if row['trend'] == 'uptrend':
            y_vals = [row['low'], row['high']]
        else:
            y_vals = [row['high'], row['low']]

        trace = go.Scatter(x=x_vals,
                           y=y_vals,
                           yaxis=f'y{yaxis}',
                           mode='lines',
                           line_color=row['color'],
                           showlegend=False)

        fig.add_trace(trace)
    return fig


def testing_momentum(trend_frame, current_frame):
    fig = go.Figure()
    df = current_frame[::-1]
    pricing = go.Candlestick(x=df.time,
                             open=df.open, high=df.high,
                             low=df.low, close=df.close,
                             line_width=.5, increasing_line_color='#0fba51',
                             decreasing_line_color='#b5091d',
                             name="pricing",
                             showlegend=True
                             )

    fig.add_trace(pricing)

    def plot_trend(x_vals, y_vals):
        trace = go.Scatter(x=x_vals, y=y_vals, mode='lines')
        return trace

    for index in trend_frame.index:
        row = dict(trend_frame.iloc[index])
        y_values, x_values = [], []
        if 'pennant' in row['trend']:
            y_values.extend(row['high'])
            y_values.extend(row['low'])
            times = [row['start_time'], row['end_time']]
            x_values.extend(times)
            x_values.extend(times)

        else:
            y_values.append(row['high'])
            y_values.append(row['low'])
            times = [row['start_time'], row['end_time']]
            x_values.extend(times)

        trace = plot_trend(x_values, y_values)
        fig.add_trace(trace)
    fig.show()
from local_functions.analyse import order_eval

# region Conditions
# region Sell Conditions
''' ---- SELL CONDITIONS ---- '''
sell_conditions = []
sc = order_eval.sell_conditions

# region percentage_gain
sc.percentage_gain
percentage_gain = True
percentage_gain_order = 1
percentage_gain_params = {
    'perc_gain': 3
}

if percentage_gain:
    sell_conditions.append((percentage_gain_order, 'percentage_gain'))

# endregion percentage_gain

# region target_unreal
# sc.target_unreal
target_unreal = True
target_unreal_order = 2
target_unreal_params = {
    'target_unreal': 20
}

if target_unreal:
    sell_conditions.append((target_unreal_order, 'target_unreal'))
# endregion target_unreal

# region exposure_over_account_limit
sc.exposure_over_account_limit
exposure_over_account_limit = True
exposure_over_account_limit_order = 3
exposure_over_account_limit_params = {}

if exposure_over_account_limit:
    sell_conditions.append(
        (exposure_over_account_limit_order, 'exposure_over_account_limit'))

# endregion exposure_over_account_limit

# region timed_exit

# sc.timed_exit
timed_exit = True
timed_exit_order = 4
timed_exit_params = {
    'time': '11:00:00',
}


if timed_exit:
    sell_conditions.append((timed_exit_order, 'timed_exit'))

# endregion timed_exit

sell_conditions = list((cond for num, cond in sorted(sell_conditions)))
# endregion Sell Conditions

# region Buy Conditions
''' ---- BUY CONDITIONS ---- '''
buy_conditions = []
bc = order_eval.buy_conditions

# region aggressive average
# bc.aggresive_average
aggresive_average = True
aggresive_average_order = 1
aggresive_average_params = {}


if aggresive_average:
    buy_conditions.append(aggresive_average_order, 'aggresive_average')
# endregion aggressive average

# region drop below average
# bc.drop_below_average
drop_below_average = True
drop_below_average_order = 1
drop_below_average_params = {}


if drop_below_average:
    buy_conditions.append(drop_below_average_order, 'drop_below_average')
# endregion drop below average

buy_conditions.sort()
buy_conditions = list((cond for num, cond in buy_conditions))
# endregion Buy Conditions
# endregion Conditions

# Other

ideal_volatility = 3

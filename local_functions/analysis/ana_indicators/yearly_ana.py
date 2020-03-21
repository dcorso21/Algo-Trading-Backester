def run_yearly(daily_df, yearly_df):
    
    # try to open up the file. If the file is there, do nothing, 
    try:
        yearly = open('temp_assets/yearly_ana.csv', 'r')
        yearly.close()
    
    # otherwise, make the file. 
    except BaseException:
        # run all lower functions
        # save as csv in temp_assets 
            # May be worth repeating this until gap up can be found at 9:31. 
            # This, of course, isn't a problem when pulling from a csv.  
        yearly = pd.DataFrame()
        
        yearly.to_csv('temp_assets/yearly_ana.csv')
        
        #pass



def get_gap(yearly_df, daily_df):
    
    last_close = list(yearly_df.close)[-1]
    open_price = list(daily_df[daily_df.time == '09:31:00'].open)[0]
    
    gap = (open_price - last_close)/last_close * 100
    
    return gap



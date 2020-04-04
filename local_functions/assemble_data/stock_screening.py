from local_functions.main import global_vars as gl


def get_prospective_stocks(num_of_stocks):

    url = 'https://stock-screener.org/gap-up-stocks.aspx'
    html = gl.requests.get(url).content
    df_list = gl.pd.read_html(html)
    df = df_list[-3]
    df['% Change'] = df['% Change'].apply(lambda x: float(x[:-1]))
    df.sort_values(by='% Change', ascending=False)
    prospective_stocks = df.head(num_of_stocks).Symbol.to_list()
    return prospective_stocks

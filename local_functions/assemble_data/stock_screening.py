from local_functions.main import global_vars as gl


def get_prospective_stocks():

    # url = 'https://stock-screener.org/gap-up-stocks.aspx'
    # html = gl.requests.get(url).content
    # df_list = gl.pd.read_html(html)
    # df = df_list[-3]
    # df['% Change'] = df['% Change'].apply(lambda x: float(x[:-1]))
    # df.sort_values(by='% Change', ascending=False)
    # prospective_stocks = df.head(num_of_stocks).Symbol.to_list()
    # return prospective_stocks

    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options

    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-gpu')

    browser = webdriver.Chrome(chrome_options=options,
                               executable_path=r'C:\Users\19374\Documents\Python\Algorithmic Trading\local_functions\assemble_data\chromedriver.exe')

    url = r'https://stockbeep.com/gap-up-stocks'

    browser.get(url=url)

    data = browser.find_element_by_xpath(r'//*[@id="DataTables_Table_0"]').text
    browser.quit()

    lines = data.split('\n')

    tickers = []
    gaps = []
    for index, line in enumerate(lines):
        if index == 0:
            continue

        if index % 2 == 0:
            gaps.append(float(line.split(' ')[7]))

        else:
            tickers.append(line.split(' ')[1])

    df = gl.pd.DataFrame({'ticker': tickers, 'gap': gaps})
    df = df[df.gap >= 5]
    prospective_stocks = df.ticker.to_list()

    return prospective_stocks

import datetime
import pandas_datareader.data as web
import pandas as pd
from stockutil.ticker import Ticker

class IndexError(Exception):
    pass

class Index:
    symbol = None
    tickers = []
    sources = {
        "NDX" : ["https://en.wikipedia.org/wiki/Nasdaq-100",3,"Ticker"],
        "SPX" : ["https://en.wikipedia.org/wiki/List_of_S%26P_500_companies",0,"Symbol"]
    }
    up = []
    down = []
    t_volume = ""
    y_volume = ""
    t = ""
    y = ""
    index_msg = {}
    ma = 0
    err_msg = ""

    
    def __init__(self,symbol) -> None:
        symbol = symbol.upper()
        if symbol not in self.sources.keys():
            raise IndexError(f"{symbol} 不在我们的支持列表中")
        self.symbol = symbol

    def get_index_tickers_list(self):
        """
        获得指数的成分股列表
        """
        self.tickers = []
        url,table_num,colum_name = self.sources[self.symbol]
        df = pd.read_html(url)[table_num]
        self.tickers = df[colum_name].tolist()
        return self.tickers

    def compare_avg(self, ma, source="~/Downloads/data", start_date =datetime.date(2021,1,1),end_date=datetime.date.today()):
        """
        比较指数中所有股票最新价格和某个周期价格（默认50），输出股票总数、高于MA的数量以及占比。
        统计并输出这些股票今天和昨日的交易量总和，并做比较
        """
        if self.tickers is None:
            self.get_index_tickers_list()
        self.up = []
        self.down = []
        self.t_volume = 0
        self.y_volume = 0
        self.err_msg =""
        self.ma = ma
        for symbol in self.tickers:
            try:
                symbol = Ticker(symbol,start_date = start_date, end_date= end_date)
                df = symbol.load_data(source)
                lastest_price = df['Adj Close'][-1]
                self.t = df.index.date[-1]
                self.t_volume += df['Volume'][-1]
                self.y = df.index.date[-2]
                self.y_volume += df['Volume'][-2]                
                symbol.append_sma(ma)
                if df.count()[0] > ma :
                    if lastest_price < symbol.smas[ma]:
                        self.up.append(symbol.symbol)
                    else:
                        self.down.append(symbol.symbol)
                else:
                    self.err_msg +=f"{symbol.symbol.upper()} 的{ma}周期均价因时长不足无法比较\n" 
            except Exception as e:
                    self.err_msg += f"unreachable stock: {symbol.symbol.upper()}\nerror message: {e}\n"
        return True

    def ge_index_compare_msg(self,index, end_date):
        if self.tickers is None:
            self.get_index_tickers_list()
        self.index_msg = {}
        up_num = len(self.up)
        down_num = len(self.down)
        volume_change = self.t_volume/self.y_volume-1
        if down_num > 0:           
            self.index_msg = f"{self.symbol.upper()} 共有 {up_num+down_num} 支股票，共有 {up_num/(up_num+down_num)*100:.2f}% 高于 {self.ma} 周期均线.\n{self.t} 总成交量为 {format(self.t_volume, '0,.2f')},\n{self.y} 总成交量为 {format(self.y_volume, '0,.2f')},\n今日增长了 {volume_change*100:.2f}%.\n"
            
        else:
            raise IndexError (f"数据好像出问题了，请检查一下。")
        if up_num+down_num + 20 < len(self.tickers):
            raise IndexError (f"{index.upper()}: {end_date.strftime('%Y-%m-%d')} 有超过20支股票没有数据，请确保输入的日期当天有开市\n")
        
        return self.index_msg


if __name__ == "__main__":

    #from stockutil import ticker

    # spx = Index('ndx')
    # print(spx.get_index_tickers_list())
    # print(len(spx.tickers))
    # print(spx.compare_avg(
    #     10,
    #     source="~/Downloads/data",
    #     end_date=datetime.date(2021,6,1)
    # ))

    tickers = ["ndx","spx"]
    tickers = ["aapl","RBLX"]
    admin_msg = ""
    notify_msg = ""
    mas = [10, 50, 120]
    for ticker in tickers:
        try:
            a = ticker.Ticker(ticker,datetime.date(2021,8,13))
            #a.load_data(source = "~/Downloads/data")
            a.load_data(source = "stooq")
            lastest_price = a.data['Close'][-1]
            a.append_sma(10)
            a.append_sma(50)
            a.append_sma(100)
            a.append_sma(200)
            a.cal_sams_change_rate()
            a.ge_xyh_msg(mas)
            notify_msg += f"{lastest_price} \n{a.smas} \n{a.smas_state}\n{a.xyh_msg}"
        except IndexError as e:
            admin_msg += str(e)
    print("=================================")
    print(a.load_data(source = "stooq"))
    print(a.load_data(source = "stooq")['Close'][-1])
    print("=================================")
    print(notify_msg)
    print(admin_msg)
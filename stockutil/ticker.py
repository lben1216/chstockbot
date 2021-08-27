import pandas_datareader.data as web
import datetime
from stockutil.stooq import search_file,read_stooq_file,maNotEnoughError,markCloseError
from pandas_datareader._utils import RemoteDataError
from telegram import Bot
import getopt,sys,os
import config
from util.utils import is_second_wednesday,get_target_date, get_default_maxtry, get_date_list

class TickerError(Exception):
    pass

class Ticker:
    df = None
    starttime = None
    endtime = None
    principle = 100
    from_s=None
    ds=None
    xmm_profit = {}
    dmm_profit = {}
    smas = {}
    smas_state ={}
    date_list= {}
    xmm_price_list = {}
    dmm_price_list = {}

    def __init__(self,symbol,from_s,ds,starttime=datetime.date(2021,1,1),endtime=datetime.datetime.today(),principle=100):
        self.symbol = symbol
        self.start_date = starttime
        self.end_date = endtime

    def load_data(self,source):
        """
        从本地或某特定路径或stooq取得ticker的数据。
        根据取得的数据中的起止日期 和 init的起止日期做比较，然后确定start date 和 end date
        """
        symbol = self.symbol
        self.data = None
        if source == "stooq":
            df = web.DataReader(symbol.upper(),source,end=self.end_date)
            df = df.sort_values(by="Date")
            if "Adj Close" not in df.columns.values: #当数据没有adj close时，从close 数据copy给adj close
                    df["Adj Close"] = df["Close"]
            self.data = df
            self.clean_sma()
        
        else:
            ticker_file = search_file(symbol.lower().replace(".","-") + ".us.txt",os.path.expanduser(source))
            df = read_stooq_file(path = ticker_file[0])
            self.data = df
            self.clean_sma()
            self.clean_price_lists()
        self.end_date = df.index.date[-1]
        if self.start_date < df.index.date[0]:
            self.start_date = df.index.date[0]
        
        return self.data
        
        
    # def load_data(self):
    #     '''
    #     from_s: web/local;
    #     ds: "data source name" when from = "web"; "path directory" when from = "local"
    #     '''
    #     if self.ds !=None:
    #         if self.from_s.lower() == "web":
    #             df = web.DataReader(self.symbol.upper(), self.ds,start=self.starttime,end=self.endtime)
    #             df = df.sort_values(by="Date") #将排序这个步骤放在了判断df是否存在之后；最新的数据在最后
    #             if "Adj Close" not in df.columns.values: #当数据没有adj close时，从close 数据copy给adj close
    #                 df["Adj Close"] = df["Close"]
    #         if self.from_s.lower() == "local":
    #             tiker_file = search_file(self.symbol.lower().replace(".","-") + ".us.txt",os.path.expanduser(self.ds))
    #             df = read_stooq_file(path=tiker_file[0])
    #             #filter df based on end time
    #             if self.endtime in df.index.date:
    #                 df = df.loc[df.index[0]:self.endtime]
    #         self.df = df
    #         self.reset_data()
    #         return self.df
    #     raise TickerError("无法使用当前指定的方法")    

    def xmm_max_try(self):
        if self.date_list["xmm"] == None:
            raise TickerError("小毛毛指定日期中没有日期数据")
        return 7
    
    def dmm_max_try(self): #没有想好是要分开来算max try 还是直接给定值
        if self.date_list["dmm"] == None:
            raise TickerError("小毛毛指定日期中没有日期数据")
        return 28


    def get_price_list(self, date_list_name, get_maxtry =get_default_maxtry): 
        """
        获得给定日期列表的收盘价数据
        """
        price_list = []
        if self.data is None:
            self.load_data()
        if self.date_lists is None:
            self.date_lists = get_date_list(self.start_date, self.end_date)
        if date_list_name not in self.date_lists.keys():
            raise TickerError(f"{self.symbol} 没有 {date_list_name} 的日期列表")
        df = self.data
        date_list = self.date_lists[date_list_name]
        for j in range(len(date_list)):
            if date_list[j] > df.index[0]:
                cal_date = date_list[j]
                max_try = get_maxtry(cal_date)
                i = 0 
                while cal_date not in df.index.date and i < max_try:
                    i += 1
                    cal_date = cal_date + datetime.timedelta(days=1)
                if i < max_try:
                    price_list.append(df.loc[cal_date]['Close'])        
        self.price_lists[date_list_name] = price_list
        return self.price_lists

    def cal_profit(self, date_list_name):
        """
        计算某ticker指定时间段的利润率。
        Parameters
        ----------
        ticker_price : 每个定投日的收盘价格列表。 
        """
        if date_list_name not in self.date_lists.keys():
            raise TickerError(f"{self.symbol} 没有 {date_list_name} 的周期价格列表")
        ticker_price = self.price_lists[date_list_name]
        times = len(ticker_price)
        #每周投入金额一样(100块)
        stock_num = 0
        for i in range (times):    
            stock_num += 100/ticker_price[i]
        cost = 100 * times
        cur_value = stock_num * self.data['Close'][-1]
        profit = cur_value - cost
        rate = (profit/cost)*100
        return {'rate': f"{rate:.2f}%", 'cost':f"{cost:.2f}", 'value':f"{cur_value:.2f}"}
    
    def ge_profit_msg(self):
        """
        分别取得xmm和dmm的利润数据情况。
        生成输出的消息。
        """
        self.profit_msg = {}
        if self.data is None:
            self.load_data()

        if self.price_lists is None:
            self.get_price_list()

        w_profit = self.cal_profit('xmm')
        m_profit = self.cal_profit('dmm')
        
        self.profit_msg['weekly'] = f"如果从{self.start_date}开始，每周三定投{self.symbol.upper()} 100元，截止到{self.end_date}，累计投入{w_profit['cost']}，市值为{w_profit['value']}，利润率为 {w_profit['rate']}"
        self.profit_msg['monthly'] = f"如果从{self.start_date}开始，每月第二周的周三定投{self.symbol.upper()} 100元，截止到{self.end_date}，累计投入{m_profit['cost']}，市值为{m_profit['value']}，利润率为 {m_profit['rate']}"


        # if self.df.count()[0] > ma :
        #     if self.df['Adj Close'][-1] < self.df.tail(ma)['Adj Close'].mean():
        #         return False
        #     else:
        #         return True
        # raise maNotEnoughError(f"{ma} 周期均价因时长不足无法得出\n")
        
    def cal_symbols_avg(self,ma:list):
        if self.df is None:
            self.load_data()
        
        df = self.df
        
        if df.count()[0] < ma :
            raise TickerError(f"Ticker{self.symbol}里的历史数据没有{ma}这么多")

        if self.endtime != df.index.date[-1]:
            raise TickerError(f"最后一个交易日不是{self.endtime}")

        sma = df.tail(ma)['Adj Close'].mean()
        self.smas[ma] = sma
        return sma

    def cal_sams_change_rate(self):
        df = self.df
        for ma,value in self.smas.items():
            percentage = (df['Adj Close'][-1] - value)/value * 100
            self.smas_state[ma] = [percentage,"🟢" if percentage > 0 else "🔴"]
        return self.smas_state

    # def reset_data(self):
    #     self.smas = {}
    #     self.smas_state = {}

    # def gen_mmt_msg(self):
    #     chat_msg = ""
    #     if self.xmm_profit:
    #         chat_msg += f"如果你从{self.starttime.strftime('%Y年%m月%d日')}定投 #小毛毛 {self.symbol} {self.principle}元，到{self.endtime.strftime('%Y年%m月%d日')}累计投入 {self.xmm_profit['total_principle']}元，到昨日市值为 {self.xmm_profit['current_profit']:0.2f} 元，累计利润为 {self.xmm_profit['profit_percentage']*100:0.2f}%\n"
    #     if self.dmm_profit:
    #         chat_msg += f"如果你从{self.starttime.strftime('%Y年%m月%d日')}定投 #大毛毛 {self.symbol} {self.principle}元，到{self.endtime.strftime('%Y年%m月%d日')}累计投入 {self.dmm_profit['total_principle']}元，到昨日市值为 {self.dmm_profit['current_profit']:0.2f} 元，累计利润为 {self.dmm_profit['profit_percentage']*100:0.2f}%\n"
    #     return chat_msg

    # def gen_xyh_msg(self):
    #     chat_msg = ""
    #     for key,value in self.smas.items():
    #         chat_msg += f"{self.smas_state[key][1]} {key} 周期均价：{value:0.2f} ({self.smas_state[key][0]:0.2f}%)\n"
    #     return chat_msg



if __name__ == "__main__":
    # Ticker测试代码
    # aapl = Ticker('AAPL')
    # aapl.load_data("~/Downloads/data")
    # aapl.get_price_lists(start=datetime.date(2020,4,28))
    # print(aapl.cal_profit('montly'))


    # spx = Index('ndx')
    # print(spx.get_index_tickers_list())
    # print(len(spx.tickers))
    # print(spx.compare_avg(
    #     10,
    #     source="~/Downloads/data",
    #     end_date=datetime.date(2021,6,1)
    # ))
    ticker = Ticker("spy","web","stooq")
    print(ticker.date_list["dmm"])
    print(ticker.date_list["xmm"])
    # import stooq
    # tickers = ["spy","qqq","didi"]
    # admin_msg = ""
    # notify_msg = ""

    # for ticker in tickers:
    #     try:
    #         a = Ticker(ticker,datetime.date(2021,8,6))
    #         #a.load_data(source = "~/Downloads/data")
    #         a.load_data(source = "stooq")
    #         lastest_price = a.load_data(source = "~/Downloads/data")['Close'][-1]
    #         a.append_sma(10)
    #         a.append_sma(50)
    #         a.append_sma(100)
    #         a.append_sma(200)
    #         a.cal_sams_change_rate()
    #         notify_msg += f"{lastest_price} {a.smas} {a.smas_state}\n"
    #     except TickerError as e:
    #         admin_msg += str(e)
    # print("=================================")
    # print(a.load_data(source = "stooq"))
    # print(a.load_data(source = "stooq")['Close'][-1])
    # print("=================================")
    # print(notify_msg)
    # print(admin_msg)
    # try:
    #     b = Index()
    #     spx = b.get_sp500_tickers()
    #     spx_avg = b.compare_avg(ma = 50, index = spx, end_date=datetime.date(2021,7,21))
    #     spx_msg = f"SPX共有{spx_avg['up_num']+spx_avg['down_num']}支股票，共有{spx_avg['rate']*100:.2f}%高于50周期均线"
    #     notify_msg = f"{spx_msg}"
    # except TickerError as e:
    #     admin_msg+=str(e)
        
    # print (spx_avg)
    # print (notify_msg)
    # print (admin_msg)
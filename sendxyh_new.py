import getopt,sys,config,os

from pandas.core.indexes.base import ensure_index_from_sequences
from pandas.core.indexing import IndexSlice
import pandas as pd
import datetime
from telegram import Bot
from stockutil.ticker import Ticker, TickerError
from stockutil.index import Index, IndexError
from stockutil.stooq import read_stooq_file
from util.utils import sendmsg
from pathlib import Path

target_date = datetime.date.today()
start_date = datetime.date(2021,1,1)

def help():
    return "sendxyh.py -c configpath -d yyyymmdd"

def get_market_volume(path = "~/Download/data"):
    p = Path(path)
    t_list = []
    ticker_name = []
    today_volume = []
    yesterday_volume = []
    err_msg = ""
    
    for file_name in p.rglob('*.txt'):
        try:
            t = Path (file_name)
            t_list.append(t)
            ticker_name.append(t.stem)
            # print(ticker_name)
            ticker_file = read_stooq_file(file_name)            
            today_volume.append(ticker_file['Volume'][-1])
            # print (today_volume)
            yesterday_volume.append(ticker_file['Volume'][-2])
        except Exception as e:
            err_msg += f"{type(e)},{e}\n"
            continue

    market_volume = {'file num':len(t_list),'name num':len(ticker_name),'today num':len(today_volume),'today volume':sum(today_volume), 'yesterday num':len(yesterday_volume),'yesterday volume':sum(yesterday_volume)}

    return market_volume,err_msg


if __name__ == '__main__':
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hc:d:", ["config, datetime="])
    except getopt.GetoptError:
        print(help())
        sys.exit(2)

    for opt, arg in opts:
        if opt == '-h':
            print(help())
            sys.exit()
        elif opt in ("-c", "--config"):
            config.config_path = arg          
        elif opt in ("-d", "--datetime"): 
            try:
                y,m,d = arg[:4],arg[-4:-2],arg[-2:]
                target_date = datetime.date(int(y),int(m),int(d))
            except Exception:
                print("日期无法解读")
                print(help())
                sys.exit(2)

    config.config_file = os.path.join(config.config_path, "config.json")
    try:
        CONFIG = config.load_config()
    except FileNotFoundError:
        print(f"config.json not found.Generate a new configuration file in {config.config_file}")
        config.set_default()
        sys.exit(2)

    bot = Bot(token = CONFIG['Token'])
    symbols = CONFIG['xyhticker']
    indexs = CONFIG['xyhindex']
    notifychat = CONFIG['xyhchat']
    adminchat = CONFIG['xyhlog']
    debug = CONFIG['DEBUG']
    tickers = CONFIG['mmtticker']


    notify_message = ""
    admin_message = ""
    index_message = ""
    index_end_date = None
    symbol_end_date = None
    volume_message = ""
    volume_err_message = ""

    for index in indexs:
        try:
            s = Index(index)
            s.get_index_tickers_list()              
            s.compare_avg(ma = 50,source = "~/Downloads/data", start_date = start_date, end_date=target_date)
            s.ge_index_compare_msg(index, end_date=datetime.date(2021,7,21))  
            index_end_date = s.t          
            index_message += f"{s.index_msg}\n"
            admin_message += f"{s.err_msg}"
        except IndexError as e:
            admin_message += str(e)

    for symbol in symbols:
        try:               
            ticker = Ticker(symbol[0], start_date = start_date, end_date=target_date)
            ticker.load_data('stooq')
            symbol_end_date = ticker.end_date
            ticker.ge_xyh_msg(symbol[1:])
            notify_message += f"{ticker.xyh_msg}"
        except TickerError as e:
            admin_message += str(e)

    try:
        m,e = get_market_volume(path = "/Users/stephen/Download/data")
        today_v = m['today volume']
        yestoday_v = m['yesterday volume']
        change_rate = f"{(today_v/yestoday_v - 1)*100:.2f}%"
        volume_message = f"今日市场总成交量为{format(today_v, '0,.2f')},昨日为{format(yestoday_v, '0,.2f')},增长了{change_rate}." 
        admin_message += f"{e}"
    except Exception as err:
        admin_message += str(err)

    if index_end_date == target_date and symbol_end_date == target_date:    
        try:
            if admin_message:
                sendmsg(bot,adminchat,admin_message,debug=debug)
            if notify_message:
                notify_message = f"🌈🌈🌈{target_date}天相🌈🌈🌈: \n\n{notify_message}\n{index_message}\n\n{volume_message}\n贡献者:毛票教的大朋友们"
                sendmsg(bot,notifychat,notify_message,debug=debug)
        except Exception as err:
            sendmsg(bot,adminchat,f"今天完蛋了，什么都不知道，快去通知管理员，bot已经废物了，出的问题是:\n{type(err)}:\n{err}",debug)
    else:
        sendmsg(bot,adminchat,f"出问题啦:\n有关指数部分的数据中最后一天是{index_end_date}，有关股票部分的数据中最后一天是{symbol_end_date}, 今天是{target_date}.",debug)
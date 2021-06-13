import getopt
import os
import sys
import pandas as pd
from pandas.core.base import DataError
import pandas_datareader.data as web
import datetime
import requests
import telegram
import config
import time
from telegram import bot
#define today's date
end = datetime.date.today()
group_id = -1001430794202
admingroup = -1001430794202
stock_list = [['spy',13,50],['qqq',13,50,200],['^spx',13,50,200]]
#read bot config from JSON file
try:
    opts, args = getopt.getopt(sys.argv[1:], "hc:", ["config="])
except getopt.GetoptError:
    print(help())
    sys.exit(2)

for opt, arg in opts:
    if opt == '-h':
        print(help())
        sys.exit()
    elif opt in ("-c", "--config"):
        config.config_path = arg

config.config_file = os.path.join(config.config_path, "config.json")
try:
    CONFIG = config.load_config()
except FileNotFoundError:
    print(f"config.json not found.Generate a new configuration file in {config.config_file}")
    config.set_default()
    sys.exit(2)

#calculate average close price based on symbol and week
def cal_avg_price(symbol, ma=[]):
    start = datetime.date.today() - datetime.timedelta(days=365)
    message = ""
    try:
        df = web.DataReader(symbol.upper(),'stooq',start=start,end=end)
    except Exception as e:
        raise Exception(f"""Error occured while pulling data due to {e}""")
        #start process data based on args number
    if not df.empty:
        current_close_price = df['Adj Close'][-1]
        current_high_price = df['High'][-1]
        current_low_price = df['Low'][-1]
        message = f"""
    {symbol}价格：{current_close_price:.2f} ({current_low_price:.2f}-{current_high_price:.2f})"""
        for i in ma:
            ma_price = df['Adj Close'].tail(i).mean()
            message += f"""
    {ma}周期均价：{ma_price:.2f}"""
        message += "\n"
    else:
        raise DataError
    
    return message  

#calculate price based on s list and generate message
out_message = f"""
当日天相"""

bot = telegram.Bot(token=CONFIG["Token"])
for stock in stock_list:
    try:
        out_message += cal_avg_price(stock[0],stock[1:])
    except Exception or DataError as e:
        bot.send_message(chat_id=admingroup,text=f"""cannot fetch data {stock[0]} from data source due to {e}, please check""")


#try to send message and catch up exception
bot.send_message(chat_id=group_id,text=out_message)

#crontab command
#05 16 * * 1-5 python /xx/xx/xx/Github/chstockbot/sendxyh.py
import os
import sys
import pandas as pd
import pandas_datareader.data as web
import datetime
import requests
import config
import schedule
import time
#define today's date
end = datetime.date.today()
group_id = -1001430794202

#read bot config from JSON file
config.config_file = os.path.join(config.config_path, "config.json")
try:
    CONFIG = config.load_config()
except FileNotFoundError:
    print(f"config.json not found.Generate a new configuration file in {config.config_file}")
    config.set_default()
    sys.exit(2)

#define sending message content and api config to telegram group
def send_xyh(chat_id, message):
    data = {
        'chat_id': chat_id,
        'text': message
    }
    url = "https://api.telegram.org/bot{api}/sendMessage".format(api=CONFIG['Token'])
    response = requests.get(url,params=data)
    return response

#calculate average close price based on symbol and week
def cal_avg_price(symbol, week):
    start = datetime.date.today() - datetime.timedelta(weeks=week)
    #df = web.DataReader(symbol.upper(), 'stooq', start=start, end=end)
    df = web.get_data_yahoo(symbol.upper(),start=start,end=end)
    #print(df)
    avg_open_price = df['Open'].mean()
    avg_high_price = df['High'].mean()
    avg_low_price = df['Low'].mean()
    avg_close_price = df['Close'].mean()
    current_close_price = df['Close'][0]
    current_high_price = df['High'][0]
    current_low_price = df['Low'][0]
    print(f"""avg open price: {avg_open_price:.2f}, avg close price: {avg_close_price:.2f}, avg high price: {avg_high_price:.2f},avg low price: {avg_low_price:.2f}""")
    return [avg_close_price, current_close_price,current_close_price,current_high_price]



#build timer to auto send message
def scheduler():
    #get avg price when scheduler task is running
    qqq_13 = cal_avg_price('qqq', 13)
    qqq_50 = cal_avg_price('qqq', 50)
    qqq_200 = cal_avg_price('qqq', 200)

    spy_13 = cal_avg_price('spy', 13)
    spy_50 = cal_avg_price('spy', 50)
    spy_200 = cal_avg_price('spy', 200)

    #generate outgoing message
    message = f"""当日天相
SPY价格：{spy_13[1]:.2f}({spy_13[2]:.2f}-{spy_13[3]:.2f})
13周期均价：{spy_13[0]:.2f}
50周期均价：{spy_50[0]:.2f}


QQQ价格：{qqq_13[1]:.2f}({qqq_13[2]:.2f}-{qqq_13[3]:.2f})
13周期均价：{qqq_13[0]:.2f}
50周期均价：{qqq_50[0]:.2f}
200周期均价：{qqq_200[0]:.2f}"""
    
    #try to send message and catch up exception
    try:
        api_response = send_xyh(group_id, message)
        print(api_response)
    except Exception as e:
        message = f"""cannot send message to {group_id} due to {e}; please re-try"""
        api_response = send_xyh(group_id, message)
        print(api_response.status_code)

#start sevice continuously        
if __name__ == '__main__':
    schedule.every().day.at("16:05").do(scheduler)
  
# Loop so that the scheduling task
# keeps on running all time.
    while True:
    # Checks whether a scheduled task 
    # is pending to run or not
        schedule.run_pending()
        time.sleep(1)
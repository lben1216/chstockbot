import pandas as pd
import getopt
import sys
import datetime, calendar

def get_target_date(start=datetime.date.today(),end=datetime.date.today(),freq="W-WED"): #c获得指定日期中的周三 可以扩展成任何天数
    '''
    freq="W-DAY" i.e, W-MON/W-TUE/W-WED/W-THU/W-FRI/W-SAT/W-SUN
    '''
    date_list = pd.date_range(start=start, end=end, freq=freq).tolist()

    date_dict = {}
    date_dict["xmm"] =date_list
    date_dict["dmm"] = []

    for date in date_list:
        if is_second_wednesday(date):
            date_dict["dmm"].append(date)
    return date_dict


def get_date_list(start_date=None,end_date=None,freq='W-WED', week_num = 2):
    date_list = pd.date_range(start=start_date, end=end_date, freq=freq)
    date_lists = {}
    date_lists['xmm'] = date_list
    date_lists['dmm'] = []
    for date in date_list:
        if get_week_num(date.year, date.month, date.day) == week_num:
            date_lists['dmm'].append(date)
    return date_lists



def is_second_wednesday(d=datetime.date.today()): #计算是否是第二个周三；网上找的，很简单又很有效
    return d.weekday() == 2 and 8 <= d.day <= 15


def sendmsg(bot,chatid,msg,debug=True):
    if debug:
        print(f"{chatid}\n{msg}")
    else:
        bot.send_message(chatid,msg)

def get_week_num(year:int, month:int, day:int) -> int:
    """
    获取当前日期是本月的第几周
    并且若本月的第二个周三所在周不是第二周，则将这周设为本月第二周
    """
    start = int(datetime.date(year, month, 1).strftime("%W"))
    end = int(datetime.date(year, month,day).strftime("%W"))
    week_num = end - start + 1
    if week_num == 2:
        if 7 < day < 15:
            week_num = week_num
        if day < 8:
            week_num = week_num -1
    return week_num

def get_default_maxtry(try_date):
    """
    获取缺省的最大尝试天数
    """
    return 3

def get_xmm_maxtry(try_date):
    """
    获取xmm的最大尝试天数
    """
    try_date = try_date.date()
    xmm_try_num = 5 - try_date.weekday() 
    return xmm_try_num

def get_dmm_maxtry(try_date):
    """
    获取dmm的最大尝试天数
    """
    year = try_date.year
    month = try_date.month
    day = try_date.day
    month_days = calendar.monthrange(year,month)
    dmm_try_num = month_days[1] - day
    return dmm_try_num
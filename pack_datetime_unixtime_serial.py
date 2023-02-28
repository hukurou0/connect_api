from time import time
from datetime import datetime, date, timedelta
from typing import Union

# ut, datetime 端数切捨て関数
def round_unixtime_datetime(t : Union[float, datetime]) -> Union[int, datetime]:
    if(isinstance(t, float)):
        t = round(t)
    elif(isinstance(t, datetime)):
        t = t.replace(microsecond = 0)
    return t

# ut <-> datetime 相互変換関数
def trans_unixtime_datetime(t : Union[int, datetime]) -> Union[datetime, int]:
    t = round_unixtime_datetime(t)
    if(isinstance(t, int)):
        t = datetime.fromtimestamp(t)
    elif(isinstance(t, datetime)):
        t = datetime.timestamp(t)
        t = round(t) #変換後に生じる端数切捨て
    return t

#浮動小数点型シリアル値取得関数
def get_float_serial(today_year = date.today().year,today_month = date.today().month,today_day = date.today().day,now_hour = datetime.now().hour, now_minute = datetime.now().minute):
    today_year_date =  str(today_year) + '/' + str(today_month) + "/" + str(today_day)
    dt = datetime.strptime(today_year_date, '%Y/%m/%d')- datetime(1899, 12, 31)
    today_serial = dt.days + 1
    now_serial = today_serial + now_hour*0.04166667 + now_minute*0.00069444
    return now_serial

#整数型シリアル値取得関数
def get_int_serial(today_year = date.today().year,today_month = date.today().month,today_day = date.today().day):
    today_year_date =  str(today_year) + '/' + str(today_month) + "/" + str(today_day)
    dt = datetime.strptime(today_year_date, '%Y/%m/%d')- datetime(1899, 12, 31)
    serial = dt.days + 1
    return serial

#シリアル値を "Year/Month/Date" の形に変換
def serial_to_str(serial):
    str_datetime = (datetime(1899,12,30) + timedelta(serial)).strftime('%Y/%m/%d %H:%M:%S')
    return str_datetime
    
    
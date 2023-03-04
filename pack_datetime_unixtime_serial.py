from time import time
from datetime import datetime, date, timedelta
from typing import Union

# 時間制御にまつわる変数[s]
class TimeBase():
    totp_valid_length = 75 
    lastlogin_ut_default = time() - 3600  # ↓のminus値(-1800)より小さければ良い 
    now_minus_login_valid_ut = time() - 1800  # 30分

# ut, datetime 端数(小数点以下秒数)切捨て関数
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

#シリアル値を "YY/MM/DD" ("YY/MM/DD HH:MM:SS") の形に変換.
def serial_to_str(serial: Union[int, float]) -> str:
    if(isinstance(serial, float)):
        str_datetime = (datetime(1899,12,30) + timedelta(serial)).strftime('%Y/%m/%d %H:%M:%S')
    elif(isinstance(serial, int)):
        str_datetime = (datetime(1899,12,30) + timedelta(serial)).strftime('%Y/%m/%d')
    return str_datetime

if(__name__=="__main__"):
    print(f'UT切り捨て値: {round_unixtime_datetime(time())}')
    print(f'DateTime切り捨て値: {round_unixtime_datetime(datetime.today())}')
    print(f'UT -> Datetime: {trans_unixtime_datetime(time())}')
    print(f'Datetime -> UT: {trans_unixtime_datetime(datetime.today())}')
    print(f'現時間シリアル値(float): {get_float_serial()}')
    print(f'現時間シリアル値(int): {get_int_serial()}')
    print(f'シリアル値 -> YY/MM/DD: {serial_to_str(get_int_serial())}')
    print(f'シリアル値 -> YY/MM/DD HH:MM:SS: {serial_to_str(get_float_serial())}')

    
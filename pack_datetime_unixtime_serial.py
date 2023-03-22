from time import time
from datetime import datetime, date, timedelta
from typing import Union

# 時間制御にまつわる変数[s]
class TimeBase():
    # User 関連
    focus_lower_limit_ut = time() - 60  # ログイン試行回数に着目する時間幅の下限[ut] 
    access_maximum_limit = 10  # 上記時間に対して許容するログイン失敗回数[回]
    stop_duration = 120  # 許容できないログイン失敗回数に到達したときのアクセス不能時間幅[s]
    totp_valid_length_by_authn_mail = 1*60*30  # メール認証についてTOTP発行から入力までの許容時間[s]
    length_name_by_authn_mail = "30分"  # メール認証についてTOTP発行から入力までの許容時間(上記と連動)
    # Admin 関連
    totp_valid_length = 75  # TOTP発行から入力までの許容時間[s]
    now_minus_login_valid_ut = time() - 1800  # 最終操作時のセッションタイムアウトしない時間の下限[ut]  # cookie が残っている可能性も踏まえて.
    lastlogin_ut_default = time() - 3600  # 最終操作時間のデフォルト値(Insert時に使用)[ut]. now_minus_lgoin_valid_ut より小さければ良い.
    # 自動化関数 関連

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

# datetime -> YY/MM/DD HH:MM:SS
def datetime_to_str(dt: datetime = datetime.today(), delta_t: timedelta = timedelta()) -> str:
    dt = round_unixtime_datetime(dt)
    date_format = '%Y/%m/%d %H:%M:%S'
    dt_str = (dt + delta_t).strftime(date_format)
    return dt_str


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
    print(f'UT切り捨て値 | {round_unixtime_datetime(time())}')
    print(f'DateTime切り捨て値 | {round_unixtime_datetime(datetime.today())}')
    print(f'UT -> Datetime | {trans_unixtime_datetime(time())}')
    print(f'Datetime -> UT | {trans_unixtime_datetime(datetime.today())}')
    print(f'datetime -> YY/MM/DD HH:MM:SS | {datetime_to_str()}')
    print(f'現時間シリアル値(float) | {get_float_serial()}')
    print(f'現時間シリアル値(int) | {get_int_serial()}')
    print(f'シリアル値 -> YY/MM/DD | {serial_to_str(get_int_serial())}')
    print(f'シリアル値 -> YY/MM/DD HH:MM:SS | {serial_to_str(get_float_serial())}')

    
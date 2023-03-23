from time import time
from datetime import datetime, date, timedelta
from typing import Union


#* 時間制御にまつわる変数[s]
class TimeBase():
    # User 関連
    visible_length = 3  # 課題表示の有効日数[日]
    focus_lower_limit_ut = time() - 60  # ログイン試行回数に着目する時間幅の下限[ut] 
    access_maximum_limit = 10  # 上記時間に対して許容するログイン失敗回数[回]
    stop_duration = 120  # 許容できないログイン失敗回数に到達したときのアクセス不能時間幅[s]
    # Admin 関連
    totp_valid_length = 75  # TOTP発行から入力までの許容時間[s]
    now_minus_login_valid_ut = time() - 1800  # 最終操作時のセッションタイムアウトしない時間の下限[ut]  # 恐らく必要のない機能(但し消去不可).
    lastlogin_ut_default = time() - 3600  # 最終操作時間のデフォルト値(Insert時に使用)[ut]. now_minus_lgoin_valid_ut より小さければ良い.
    # 自動化関数 関連
    daily = 24*60*60  # unused
    monthly = 30*24*60*60  # unused


#*------------------------------- 変換に必要な機能 -------------------------------------------------*#

# datetime, ut 端数(秒未満)切捨て関数
def round_datetime_ut(t : Union[float, datetime]) -> Union[int, datetime]:
    if(isinstance(t, datetime)):
        t = t.replace(microsecond = 0)
    elif(isinstance(t, float)):
        t = round(t)
    return t

# iso8601 から 年, 月, 日, 時, 分, 秒, TZ時, TZ分 を抽出
def extract_elem_from_iso(iso: str) -> dict[int]:
    iso = iso.replace("/", "")  # 文字列時間にも対応できるように 
    iso = iso.replace(" ", "")  # 同上
    iso += "0000000000000000"   # 同上 (不足文字数(TZ用)の補完 及び 日未満を切り捨てる場合用)
    iso = iso.replace("-", "")
    iso = iso.replace(":", "")
    iso = iso.replace("T", "")
    dt_elem = {
        "year": int(iso[:4]),
        "month": int(iso[4:6]),
        "day": int(iso[6:8]),
        "hour": int(iso[8:10]),
        "minute": int(iso[10:12]),
        "second": int(iso[12:14]),
        "tz_hour": int(iso[14:17]),
        "tz_minute": int(iso[17:19])
    }
    return dt_elem


#*---------------------------------- (現時刻)状態取得関数 -------------------------------------------------*#

# 現時刻の iso8601 を取得
def get_iso(dt: datetime = datetime.today(), is_basic_format: bool = True):
    iso = trans_datetime_iso(dt, is_basic_format)
    return iso

# 現時刻の YY/MM/DD hh:mm:ss を取得
def get_str_dt(dt: datetime = datetime.today(), is_adding_under_date: bool = True):
    str_dt = trans_datetime_str(dt, is_adding_under_date)
    return str_dt

# 整数型シリアル値を取得
def get_int_serial(today_year = date.today().year,today_month = date.today().month,today_day = date.today().day):
    today_year_date =  str(today_year) + '/' + str(today_month) + "/" + str(today_day)
    dt = datetime.strptime(today_year_date, '%Y/%m/%d') - datetime(1899, 12, 31)
    serial = dt.days + 1
    return serial
# 浮動小数点型シリアル値を取得
def get_float_serial(today_year = date.today().year,today_month = date.today().month,today_day = date.today().day,now_hour = datetime.now().hour, now_minute = datetime.now().minute):
    today_year_date =  str(today_year) + '/' + str(today_month) + "/" + str(today_day)
    dt = datetime.strptime(today_year_date, '%Y/%m/%d') - datetime(1899, 12, 31)
    today_serial = dt.days + 1
    now_serial = today_serial + now_hour*0.04166667 + now_minute*0.00069444
    return now_serial


#*------------------------------------- trans via datetime ----------------------------------------*#

# datetime <-> ut 
def trans_datetime_ut(t : Union[datetime, int]) -> Union[datetime, int]:
    t = round_datetime_ut(t)
    if(isinstance(t, datetime)):
        t = datetime.timestamp(t)
        t = round(t) #変換後に生じる端数切捨て
    elif(isinstance(t, int)):
        t = datetime.fromtimestamp(t)
    return t

# datetime <-> iso8601
def trans_datetime_iso(t: Union[datetime, str], is_basic_format: bool = True):
    """ The 2nd arg is used in only datetime -> iso """
    if(isinstance(t, datetime)):
        t = round_datetime_ut(t)
        t = t.strftime('%Y%m%dT%H%M%S+0900') if(is_basic_format) else t.strftime('%Y-%m-%dT%H:%M:%S+09:00')
    elif(isinstance(t, str)):
        t = extract_elem_from_iso(t)
        t = datetime(t["year"], t["month"], t["day"], t["hour"], t["minute"], t["second"])
    return t

# datetime <-> "YYYY/MM/DD hh:mm:ss" or "YYYY/MM/DD"
def trans_datetime_str(t: Union[datetime, str], is_round_down_below_date: bool = False) -> str:
    """ The 2nd arg is only used in datetime -> str. If you round down to the nearest a day then 2nd arg is True. """
    if(isinstance(t, datetime)):
        t = round_datetime_ut(t)
        t = t.strftime('%Y/%m/%d') if(is_round_down_below_date) else t.strftime('%Y/%m/%d %H:%M:%S')
    elif(isinstance(t, str)):
        t = extract_elem_from_iso(t)
        t = datetime(t["year"], t["month"], t["day"], t["hour"], t["minute"], t["second"])
    return t

# datetime <-> serial
def trans_datetime_serial(t: Union[datetime, int, float], is_to_int: bool = True) -> Union[int, float]:
    """ The 2nd arg is only used in datetime -> serial. If you round down to the nearest day then 2nd arg is True. """
    if(isinstance(t, datetime)):
        t = round_datetime_ut(t)
        t = get_int_serial(t.year, t.month, t.day) if(is_to_int) else get_float_serial(t.year, t.month, t.day, t.hour, t.minute)
    elif(isinstance(t, int) or isinstance(t, float)):
        serial = t
        t = datetime(1899,12,30) + timedelta(t)
        if(isinstance(serial, float)):
            t += timedelta(seconds=1)  # 1秒足しているのは切り捨て誤差緩和のため
        t = round_datetime_ut(t)
    return t


#*---------------------------------------- trans other into other ----------------------------------------------------------------*#

# ut <-> iso8601 
def trans_ut_iso(t: Union[int, float], is_basic_format: bool = True) -> str:
    """ The 2nd arg is used in only datetime -> iso """
    if(isinstance(t, int) or isinstance(t, float)):
        t = trans_datetime_ut(t)
        t = t.strftime('%Y%m%dT%H%M%S+0900') if(is_basic_format) else t.strftime('%Y-%m-%dT%H:%M:%S+09:00')
    elif(isinstance(t, str)):
        t = extract_elem_from_iso(t)
        t = datetime(t["year"], t["month"], t["day"], t["hour"], t["minute"], t["second"])
        t = trans_datetime_ut(t)
    return t

# serial -> iso8601　
def serial_to_iso(serial: Union[int, float], is_basic_format: bool = True) -> str:
    """ The 2nd arg is used in only datetime -> iso. If the 1st arg is int, this convert is less than a day is set to 0. """
    iso = ""
    basic_f = '%Y%m%dT%H%M%S+0900'
    extended_f = '%Y-%m-%dT%H:%M:%S+09:00'
    iso = datetime(1899,12,30) + timedelta(serial) if(isinstance(serial, int)) else datetime(1899,12,30) + timedelta(serial, seconds=1)
    iso = iso.strftime(basic_f) if(is_basic_format) else iso.strftime(extended_f)
    return iso

# serial -> "YYYY/MM/DD" or "YYYY/MM/DD hh:mm:ss"
def serial_to_str(serial: Union[int, float]) -> str:
    if(isinstance(serial, float)):
        str_datetime = (datetime(1899,12,30) + timedelta(serial) + timedelta(seconds=1)).strftime('%Y/%m/%d %H:%M:%S')
    elif(isinstance(serial, int)):
        str_datetime = (datetime(1899,12,30) + timedelta(serial)).strftime('%Y/%m/%d')
    return str_datetime

#* テスト
if(__name__=="__main__"):
    #! シリアル値は分単位以下の信頼性は無い。
    print()
    print(f'DateTime 秒未満切り捨て          | {round_datetime_ut(datetime.today())}')
    print(f'UnixTime 秒未満切り捨て          | {round_datetime_ut(time())}')
    print(f'Datetime <-> UnixTime            | {trans_datetime_ut(time())} | {trans_datetime_ut(datetime.today())}')
    print(f'DateTime <-> ISO8601(基本形式)   | {trans_datetime_iso(get_iso())} | {trans_datetime_iso(datetime.today(), True)}')
    print(f'DateTime <-> ISO8601(拡張形式)   | {trans_datetime_iso(get_iso())} | {trans_datetime_iso(datetime.today(), False)}')
    print(f'DateTime <-> YYYY/MM/DD hh:mm:ss | {trans_datetime_str(get_str_dt())} | {trans_datetime_str(datetime.today())}')
    print(f'DateTime <-> YYYY/MM/DD          | {trans_datetime_iso(get_str_dt(is_adding_under_date=False))} | {trans_datetime_str(datetime.today(), True)}')
    print(f'DateTime <-> SerialValue         | {trans_datetime_serial(get_float_serial())} | {trans_datetime_serial(datetime.today(), False)}')
    print(f'UnixTime <-> ISO8601(基本形式)   | {trans_ut_iso(get_iso())}          | {trans_ut_iso(time(), True)}')
    print(f'SerialValue -> ISO8601(基本形式) | {serial_to_iso(get_float_serial(), True)}')
    print(f'SerialValue -> YYYY/MM/DD        | {serial_to_str(get_int_serial())}')
    print()
    

    
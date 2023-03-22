from time import time
from datetime import datetime, date, timedelta
from typing import Union

# 時間制御にまつわる変数[s]
class TimeBase():
    # User 関連
    visible_length = 3  # 課題表示の有効日数[日]
    focus_lower_limit_ut = time() - 60  # ログイン試行回数に着目する時間幅の下限[ut] 
    access_maximum_limit = 10  # 上記時間に対して許容するログイン失敗回数[回]
    stop_duration = 120  # 許容できないログイン失敗回数に到達したときのアクセス不能時間幅[s]
    # Admin 関連
    totp_valid_length = 75  # TOTP発行から入力までの許容時間[s]
    now_minus_login_valid_ut = time() - 1800  # 最終操作時のセッションタイムアウトしない時間の下限[ut]  # cookie が残っている可能性も踏まえて.
    lastlogin_ut_default = time() - 3600  # 最終操作時間のデフォルト値(Insert時に使用)[ut]. now_minus_lgoin_valid_ut より小さければ良い.
    # 自動化関数 関連
    # daily = 24*60*60
    # monthly = 30*24*60*60

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

# 浮動小数点型シリアル値取得関数
def get_float_serial(today_year = date.today().year,today_month = date.today().month,today_day = date.today().day,now_hour = datetime.now().hour, now_minute = datetime.now().minute):
    today_year_date =  str(today_year) + '/' + str(today_month) + "/" + str(today_day)
    dt = datetime.strptime(today_year_date, '%Y/%m/%d')- datetime(1899, 12, 31)
    today_serial = dt.days + 1
    now_serial = today_serial + now_hour*0.04166667 + now_minute*0.00069444
    return now_serial

# 整数型シリアル値取得関数
def get_int_serial(today_year = date.today().year,today_month = date.today().month,today_day = date.today().day):
    today_year_date =  str(today_year) + '/' + str(today_month) + "/" + str(today_day)
    dt = datetime.strptime(today_year_date, '%Y/%m/%d')- datetime(1899, 12, 31)
    serial = dt.days + 1
    return serial

# シリアル値を "YYYY/MM/DD" or "YYYY/MM/DD hh:mm:ss" の形に変換.
def serial_to_str(serial: Union[int, float]) -> str:
    if(isinstance(serial, float)):
        str_datetime = (datetime(1899,12,30) + timedelta(serial) + timedelta(seconds=1)).strftime('%Y/%m/%d %H:%M:%S')
    elif(isinstance(serial, int)):
        str_datetime = (datetime(1899,12,30) + timedelta(serial)).strftime('%Y/%m/%d')
    return str_datetime

# iso8601 から 年, 月, 日, 時, 分, 秒, TZ時, TZ分 を抽出
def extract_elem_from_iso(iso: str) -> dict[int]:
    iso = iso.replace("-", "")
    iso = iso.replace(":", "")
    iso = iso.replace("T", "")
    dt_elem = {
        "year": int(iso[:4]),
        "month": int(iso[4:6]),
        "date": int(iso[6:8]),
        "hour": int(iso[8:10]),
        "minute": int(iso[10:12]),
        "second": int(iso[12:14]),
        "tz_hour": int(iso[14:17]),
        "tz_minute": int(iso[17:19])
    }
    return dt_elem

# シリアル値を iso8601 (YYYY-MM-DDThh:mm:ss+Tz) に 変換　
def serial_to_iso(serial: Union[int, float], is_basic_format: bool = True):
    iso_datetime = ""
    if(is_basic_format):
        iso_datetime = (datetime(1899,12,30) + timedelta(serial) + timedelta(seconds=1)).strftime('%Y%m%dT%H%M%S+0900')
    else:
        iso_datetime = (datetime(1899,12,30) + timedelta(serial) + timedelta(seconds=1)).strftime('%Y-%m-%dT%H:%M:%S+09:00')
    return iso_datetime

# datetime(TZ無し) <-> iso8601 相互変換
def trans_datetime_iso(t: datetime, is_basic_format: bool = True):
    if(isinstance(t, datetime)):
        t = round_unixtime_datetime(t)
        t = t.strftime('%Y%m%dT%H%M%S+0900') if(is_basic_format) else t.strftime('%Y-%m-%dT%H:%M:%S+09:00')
    elif(isinstance(t, str)):
        t = extract_elem_from_iso(t)
        t = datetime(t["year"], t["month"], t["date"], t["hour"], t["minute"], t["second"])
    return t

# ut <-> iso8601 相互変換
def trans_ut_iso(t: Union[int, float], is_basic_format: bool = True):
    if(isinstance(t, int) or isinstance(t, float)):
        t = trans_unixtime_datetime(t)
        t = t.strftime('%Y%m%dT%H%M%S+0900') if(is_basic_format) else t.strftime('%Y-%m-%dT%H:%M:%S+09:00')
    elif(isinstance(t, str)):
        t = extract_elem_from_iso(t)
        t = datetime(t["year"], t["month"], t["date"], t["hour"], t["minute"], t["second"])
        t = trans_unixtime_datetime(t)
    return t

if(__name__=="__main__"):
    #! シリアル値は分単位以下の信頼性は無い。
    print(f'UT秒未満切り捨て値 | {round_unixtime_datetime(time())}')
    print(f'DateTime秒未満切り捨て値 | {round_unixtime_datetime(datetime.today())}')
    print(f'UT -> Datetime | {trans_unixtime_datetime(time())}')
    print(f'Datetime -> UT | {trans_unixtime_datetime(datetime.today())}')
    print(f'現時間シリアル値(float) | {get_float_serial()}')
    print(f'現時間シリアル値(int) | {get_int_serial()}')
    print(f'シリアル値 -> YYYY/MM/DD | {serial_to_str(get_int_serial())}')
    print(f'シリアル値 -> YYYY/MM/DD hh:mm:ss | {serial_to_str(get_float_serial())}')
    print(f'シリアル値 -> ISO8601(基本形式) | {serial_to_iso(get_float_serial(), True)}')
    print(f'シリアル値 -> ISO8601(拡張形式) | {serial_to_iso(get_float_serial(), False)}')
    print(f'DateTime -> ISO8601(基本形式) | {trans_datetime_iso(datetime.today(), True)}')
    print(f'TimeStamp -> ISO8601(基本形式) | {trans_ut_iso(time())}')
    

    
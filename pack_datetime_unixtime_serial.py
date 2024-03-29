from time import time
from datetime import datetime, date, timedelta
from typing import Final, Union
import pytz
jst_tz: Final = pytz.timezone('Asia/Tokyo')


#* 時間制御にまつわる変数[s]
class TimeBase():
    # User 関連
    visible_length = 3*24*60*60  # 課題表示の有効日数[s]
    focus_lower_limit_ut = time() - 60  # ログイン試行回数に着目する時間幅の下限[ut] 
    access_maximum_limit = 10  # 上記時間に対して許容するログイン失敗回数[回]
    stop_duration = 120  # 許容できないログイン失敗回数に到達したときのアクセス不能時間幅[s]
    # Admin 関連
    totp_valid_length = 5*60  # TOTP発行から入力までの許容時間[s]
    now_minus_login_valid_ut = time() - 1800  # 最終操作時のセッションタイムアウトしない時間の下限[ut]  # 恐らく必要のない機能(但し消去不可).
    lastlogin_ut_default = time() - 3600  # 最終操作時間のデフォルト値(Insert時に使用)[ut]. now_minus_lgoin_valid_ut より小さければ良い.
    # 自動化関数 関連
    daily = 24*60*60  # 1日[s]
    monthly = 30*24*60*60  # 30日[s]


#*------------------------------- 変換に必要な機能 -------------------------------------------------*#

# datetime, ut 端数(秒未満)切捨て関数
def round_datetime_ut(t : Union[float, datetime]) -> Union[int, datetime]:
    if(isinstance(t, datetime)):
        t = t.replace(microsecond = 0)
    elif(isinstance(t, float)):
        t = round(t)
    return t

# iso8601 から 年, 月, 日, 時, 分, 秒を抽出
def extract_elem_from_iso(iso: str) -> dict[int]:
    iso = iso.replace("/", "")  # 文字列時間にも対応できるように 
    iso = iso.replace(" ", "")  # 同上
    iso = iso.replace("-", "")  # ∴ TZ は、参照不可。
    iso = iso.replace("+", "")  # ∴ TZ は、参照不可。
    iso = iso.replace(":", "")
    iso = iso.replace("T", "")
    iso += "0000000000"         # 文字列時間などにも対応するよう 0 埋め
    dt_elem = {
        "year": int(iso[:4]),
        "month": int(iso[4:6]),
        "day": int(iso[6:8]),
        "hour": int(iso[8:10]),
        "minute": int(iso[10:12]),
        "second": int(iso[12:14]),
    }
    return dt_elem


#*------------------------------------- DateTime <-> Other ---------------------------------------------------*#

#? tzinfo = jst_tz とすると、tz = +09:19 となるので、 jst_tz.localize() を使用
#? t.astimezone(jst_tz) とすると、 +08:00 されるので、 jst_tz.localize() を使用

# datetime <-> ut 
def trans_datetime_ut(t : Union[datetime, int]) -> Union[datetime, int]:
    t = round_datetime_ut(t)
    if(isinstance(t, datetime)):
        t = datetime.timestamp(t)
        t = round(t) #変換後に生じる端数切捨て
    elif(isinstance(t, int)):
        t = datetime.fromtimestamp(t, jst_tz)
    return t

# datetime <-> iso8601
def trans_datetime_iso(t: Union[datetime, str], is_basic_format: bool = True):
    """ The 2nd arg is used in only datetime -> iso """
    global jst_tz
    if(isinstance(t, datetime)):
        t = round_datetime_ut(t)
        t = t.strftime('%Y%m%dT%H%M%S%z') if(is_basic_format) else t.strftime('%Y-%m-%dT%H:%M:%S%z')
    elif(isinstance(t, str)):
        t = extract_elem_from_iso(t)
        t = datetime(t["year"], t["month"], t["day"], t["hour"], t["minute"], t["second"], 0)
        t = jst_tz.localize(t)
    return t

# datetime <-> "YYYY/MM/DD hh:mm:ss" or "YYYY/MM/DD"
def trans_datetime_str(t: Union[datetime, str], is_round_down_below_date: bool = False) -> str:
    """ The 2nd arg is only used in datetime -> str. If you round down to the nearest a day then 2nd arg is True. """
    if(isinstance(t, datetime)):
        t = round_datetime_ut(t)
        t = t.strftime('%Y/%m/%d') if(is_round_down_below_date) else t.strftime('%Y/%m/%d %H:%M:%S')
    elif(isinstance(t, str)):
        t = extract_elem_from_iso(t)
        t = datetime(t["year"], t["month"], t["day"], t["hour"], t["minute"], t["second"], 0)
        t = jst_tz.localize(t)
    return t

# datetime <-> serial
def trans_datetime_serial(t: Union[datetime, int, float]) -> Union[int, float]:
    """ You round down to the nearest a day. """
    if(isinstance(t, datetime)):
        t = round_datetime_ut(t)
        t = get_int_serial(t)
    elif(isinstance(t, int) or isinstance(t, float)):
        t = datetime(1899,12,30) + timedelta(t)
        t = round_datetime_ut(t)
        t = jst_tz.localize(t)
    return t


#*------------------------------- Convert other to other via DateTime -------------------------------------------------------*#

# ut <-> iso8601 
def trans_ut_iso(t: Union[int, float], is_basic_format: bool = True) -> str:
    """ The 2nd arg is used in only datetime -> iso """
    if(isinstance(t, int) or isinstance(t, float)):
        dt = trans_datetime_ut(t)
        t = trans_datetime_iso(dt, is_basic_format)
    elif(isinstance(t, str)):
        dt = trans_datetime_iso(t)
        t = trans_datetime_ut(dt)
    return t

# ut <-> "YYYY/MM/DD hh:mm:ss"
def ut_to_str(t: Union[int, float]) -> str:
    dt = trans_datetime_ut(t)
    str_ = trans_datetime_str(dt)
    return str_

# serial -> iso8601　
def serial_to_iso(serial: Union[int, float], is_basic_format: bool = True) -> str:
    """ The 2nd arg is used in only datetime -> iso. If the 1st arg is int, this convert is less than a day is set to 0. """
    dt = trans_datetime_serial(serial)
    iso = trans_datetime_iso(dt, is_basic_format)
    return iso

# serial -> "YYYY/MM/DD" or "YYYY/MM/DD hh:mm:ss"
def serial_to_str(serial: Union[int, float]) -> str:
    dt = trans_datetime_serial(serial)
    str_datetime = trans_datetime_str(dt, False) if(isinstance(serial, float)) else trans_datetime_str(dt, int)
    return str_datetime


#*---------------------------------- (現時刻)状態取得関数 -------------------------------------------------*#

# 現時刻の DateTime(JST) を取得
def get_jst_datetime(
        year = datetime.now(jst_tz).year, month = datetime.now(jst_tz).month, day = datetime.now(jst_tz).day, 
        hour = datetime.now(jst_tz).hour, minute = datetime.now(jst_tz).minute, second = datetime.now(jst_tz).second, 
        round_down_below_date = False, is_day_final = False, period: int = 0
        ) -> datetime:
    """
    Args:
        round_down_below_date (bool, False): The time of the return value is set to 00:00:00. \n
        is_day_final (bool, False): The time of the return value is set to 23:59:59. \n 
        period (int, 0): The time of the return value is the start of the time period. However, 0 is an invalid value.

    Returns:
        datetime: 特定時刻または現時刻の DateTiem(JST) を取得
    """
    if(round_down_below_date):
        hour, minute, second = 0, 0, 0
    elif(is_day_final):
        hour, minute, second = 23, 59, 59
    elif(period == 1):
        hour, minute, second = 9, 00, 00
    elif(period == 2):
        hour, minute, second = 11, 10, 00
    elif(period == 3):
        hour, minute, second = 13, 30, 00
    elif(period == 4):
        hour, minute, second = 15, 20, 00
    elif(period == 5):
        hour, minute, second = 17, 5, 00
    jst_dt = datetime(year, month, day, hour, minute, second, 0)
    jst_dt = jst_tz.localize(jst_dt)
    return jst_dt

# 現時刻(特定時刻)の UnixTime を取得
def get_ut(dt: datetime = get_jst_datetime()) -> int:
    ut = trans_datetime_ut(dt)
    return ut

# 現時刻(特定時刻)の iso8601 を取得
def get_iso(dt: datetime = get_jst_datetime(), is_basic_format: bool = True):
    iso = trans_datetime_iso(dt, is_basic_format)
    return iso

# 現時刻(特定時刻)の YY/MM/DD hh:mm:ss を取得
def get_str_dt(dt: datetime = get_jst_datetime(), is_round_down_below_date: bool = False):
    str_dt = trans_datetime_str(dt, is_round_down_below_date)
    return str_dt

# 整数型シリアル値を取得
def get_int_serial(dt: datetime = get_jst_datetime()):
    today_year_date =  str(dt.year) + '/' + str(dt.month) + "/" + str(dt.day)
    dt = datetime.strptime(today_year_date, '%Y/%m/%d') - datetime(1899, 12, 31)
    serial = dt.days + 1
    return serial


#*------------------------------------ テスト -----------------------------------------------------------*#
if(__name__=="__main__"):
    #! シリアル値は分単位以下の信頼性は無い。
    print()
    print(f'現時刻 (DateTime)                | {get_jst_datetime()}')
    print(f'現時刻 (UnixTime)                | {get_ut()}')
    print(f'現時刻 (ISO8601)                 | {get_iso()}')
    print(f'現時刻 (YYYY/MM/DD hh:mm:ss)     | {get_str_dt()}')
    print(f'現時刻 (SerialValue)             | {get_int_serial()}')
    print(f'Datetime <-> UnixTime            | {trans_datetime_ut(time())} | {trans_datetime_ut(get_jst_datetime())}')
    print(f'DateTime <-> ISO8601(基本形式)   | {trans_datetime_iso(get_iso())} | {trans_datetime_iso(get_jst_datetime(), True)}')
    print(f'DateTime <-> ISO8601(拡張形式)   | {trans_datetime_iso(get_iso())} | {trans_datetime_iso(get_jst_datetime(), False)}')
    print(f'DateTime <-> YYYY/MM/DD hh:mm:ss | {trans_datetime_str(get_str_dt())} | {trans_datetime_str(get_jst_datetime())}')
    print(f'DateTime <-> YYYY/MM/DD          | {trans_datetime_iso(get_str_dt(is_round_down_below_date=True))} | {trans_datetime_str(get_jst_datetime(), True)}')
    print(f'DateTime <-> SerialValue         | {trans_datetime_serial(get_int_serial())} | {trans_datetime_serial(get_jst_datetime())}')
    print(f'UnixTime <-> ISO8601(基本形式)   | {trans_ut_iso(get_iso())}                | {trans_ut_iso(time(), True)}')
    print(f'SerialValue -> ISO8601(基本形式) | {serial_to_iso(get_int_serial(), True)}')
    print(f'SerialValue -> YYYY/MM/DD        | {serial_to_str(get_int_serial())}')
    print()
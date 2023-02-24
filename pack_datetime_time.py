from time import time
from datetime import datetime
from typing import Union

# 端数切捨て関数　及び ut <-> datetime 相互変換関数
def round_unixtime_datetime(t : Union[float, datetime]) -> Union[int, datetime]:
    if(isinstance(t, float)):
        t = round(t)
    elif(isinstance(t, datetime)):
        t = t.replace(microsecond = 0)
    return t
def trans_unixtime_datetime(t : Union[int, datetime]) -> Union[datetime, int]:
    t = round_unixtime_datetime(t)
    if(isinstance(t, int)):
        t = datetime.fromtimestamp(t)
    elif(isinstance(t, datetime)):
        t = datetime.timestamp(t)
        t = round(t) #変換後に生じる端数切捨て
    return t
    
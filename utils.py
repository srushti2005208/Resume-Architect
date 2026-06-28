import datetime

def now_epoch():
    return int(datetime.datetime.utcnow().timestamp())
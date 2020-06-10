import datetime
from django.utils.timesince import timesince
from dateutil.relativedelta import relativedelta


def get_age_fun(obj):
    now = datetime.datetime.now()
    created_at = obj.created_at
    try:
        diff = now - created_at
    except:
        return created_at

    if diff < datetime.timedelta(minutes=1):
        return '방금 전'

    elif diff < datetime.timedelta(hours=1):
        return '{}분 전'.format(timesince(created_at).split(', ')[0].split()[0])

    elif diff < datetime.timedelta(days=1):
        return '{}시간 전'.format(timesince(created_at).split(', ')[0].split()[0])

    elif diff < datetime.timedelta(weeks=1):
        return '{}일 전'.format(timesince(created_at).split(', ')[0].split()[0])

    # 한달이내
    elif created_at > now - relativedelta(months=1):
        return '{}주 전'.format(timesince(created_at).split(', ')[0].split()[0])

    # 세달미만
    elif created_at > now - relativedelta(months=3):
        return'{}달 전'.format(timesince(created_at).split(', ')[0].split()[0])

    return '{}년{}월{}일'.format(
        created_at.strftime('%y'), created_at.strftime('m'), created_at.strftime('d'))

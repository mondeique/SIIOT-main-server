import datetime
from django.utils.timesince import timesince
from dateutil.relativedelta import relativedelta


test_thumbnail_image_url = 'https://pepup-storage.s3.ap-northeast-2.amazonaws.com/008914fd-1b16-45ac-a9a7-0c94427bcf47.jpg'


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


def get_wallet_scheduled_date():
    dt = datetime.datetime.now()
    weekday = dt.weekday()
    date_list = [0, 1, 2, 3, 4, 5, 6]  # 0: Mon, 6: Sun
    if weekday in [0, 1]:
        t_delta = 2 - weekday
    elif weekday in [2, 3]:
        t_delta = 4 - weekday
    else:
        t_delta = 7 - weekday

    scheduled_date = dt + datetime.timedelta(days=t_delta)
    return scheduled_date
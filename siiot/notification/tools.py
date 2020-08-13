# -*- encoding: utf-8 -*-
import json
import random
import math
import operator

from core.aws.clients import lambda_client
from notification.models import Notification, NotificationUserLog
from notification.serializers import NotificationSerializer
from notification.types import *


def batch(iterable, n=1):
    l = len(iterable)
    for ndx in range(0, l, n):
        yield iterable[ndx:min(ndx + n, l)]


def _push_android(endpoints, notification):
    serializers = NotificationSerializer(notification)
    try:
        serializer_data = serializers.data
    except Exception as e:
        serializer_data = None

    if serializer_data:
        for sliced_endpoints in batch(endpoints, 100):
            data = {
                "action": notification.action,
                "param": serializer_data,
                "is_notifiable": notification.is_notifiable,
            }
            gcm_data = {
                "data": data,
                "priority": "high",
            }
            payload = json.dumps({
                "endpoints": sliced_endpoints,
                "gcm_data": gcm_data,
            })
            lambda_client.invoke(FunctionName="NotificationSender",
                                 Payload=payload,
                                 InvocationType='Event')


def _push_ios(endpoints, notification, badge=1):
    serializers = NotificationSerializer(notification)
    try:
        serializer_data = serializers.data
    except Exception as e:
        serializer_data = None

    if serializer_data:
        for sliced_endpoints in batch(endpoints, 100):
            data = {
                "action": notification.action,
                "param": serializer_data,
                "is_notifiable": notification.is_notifiable,
            }
            gcm_data = {
                "data": data,
                "priority": "high",
                "notification": {
                    "title": notification.title.encode(encoding='UTF-8', errors='strict'),
                    "body": notification.content.encode(encoding='UTF-8', errors='strict'),
                    "sound": None,
                    "badge": badge,
                    "content_available": True,
                    "id": 0,
                },
            }
            payload = json.dumps({
                "endpoints": sliced_endpoints,
                "gcm_data": gcm_data,
            })
            lambda_client.invoke(FunctionName="NotificationSender",
                                 Payload=payload,
                                 InvocationType='Event')


def send_push_async(list_user, notification, extras=None, reserved_notification=None):
    from notification.models import NotificationUserLog
    from push_notifications.models import GCMDevice
    """
    1. notification model 을 생성합니다. (Notification Type 을 활용합니다.) - on_xxx 방식의 함수에서 요청
    title, content, image, link, is_readable, icon, link, big_image 등등 

    2. 해당 notification 에 해당하는 NotificationUserLog 를 bulkcreate 합니다. - send_push_async 에서 처리 
    
    3. 해당 notification 을 해당 user 들에게 send 합니다. - send_push async 에서 처리
    """
    # 1. notification model 을 생성합니다.
    bulk_data = []
    user_ids = []

    if notification.is_readable:
        deleted_at = None
    else:
        deleted_at = timezone.now()

    for user in list_user:
        bulk_data.append(
            NotificationUserLog(user=user, notification=notification, deleted_at=deleted_at,
                                extras=extras))
        user_ids.append(user.id)

    NotificationUserLog.objects.bulk_create(bulk_data)
    device_queryset = GCMDevice.objects.filter(user__in=user_ids)

    badge = 1
    if len(list_user) == 1:
        badge = NotificationUserLog.objects.filter(user=list_user[0], read_at=None,
                                                   deleted_at=None).distinct().count()

    android_endpoints = device_queryset.filter(device_type=1).values_list('endpoint_arn', flat=True)
    _push_android(android_endpoints, notification)
